"""Provider registry: capability lookup, mode gating, budget and logging."""

from __future__ import annotations

import json
import os
from typing import Any

from .base import (
    CostGuard,
    OperationLog,
    Provider,
    ProviderError,
    ProviderExecutor,
    ProviderUnavailable,
    SpendNotAuthorized,
)

MODE_RANK = {"local": 0, "hybrid": 1, "premium": 2}


class Registry:
    def __init__(self, config: dict, *, project_dir: str | None = None):
        self.config = config
        self.mode = (config.get("mode") or "local").lower()
        if self.mode not in MODE_RANK:
            raise ValueError(f"invalid mode {self.mode!r}")
        gen = config.get("generation", {})
        self.authorize_spend = bool(gen.get("authorize_spend", False))
        self.budget_usd = float(gen.get("budget_usd", 0.0))
        max_per_run = gen.get("max_spend_per_run_usd")
        if max_per_run is not None:
            self.budget_usd = min(self.budget_usd, float(max_per_run))
        log_path = os.path.join(project_dir or ".", "logs", "generation_history.jsonl")
        self.log = OperationLog(log_path)
        self.guard = CostGuard(budget_usd=self.budget_usd, authorized=self.authorize_spend, log=self.log)
        self.providers: dict[str, Provider] = {}
        self.notes: list[dict] = []

    # -- registration -------------------------------------------------
    def add(self, provider: Provider) -> None:
        key = f"{provider.capability}:{provider.name}"
        self.providers[key] = provider
        self.log.write(
            "provider_registered",
            provider=provider.name,
            capability=provider.capability,
            mode=provider.min_mode,
            external=provider.is_external,
            cost=provider.cost_model.notes,
        )

    def note(self, provider: str, text: str) -> None:
        self.notes.append({"provider": provider, "note": text})

    # -- selection ----------------------------------------------------
    def candidates(self, capability: str) -> list[Provider]:
        return [p for k, p in self.providers.items() if p.capability == capability]

    def select(self, capability: str) -> Provider:
        """Pick the best provider allowed by the current mode.

        Ordering: local first, then cheapest external. In LOCAL mode an external
        provider is never returned — this is the hard guarantee that the skill
        cannot spend money by accident.
        """
        options = self.candidates(capability)
        if not options:
            raise ProviderUnavailable(f"no provider registered for capability {capability!r}")

        allowed = []
        for provider in options:
            if MODE_RANK.get(provider.min_mode, 0) > MODE_RANK[self.mode]:
                continue
            if provider.is_external and self.mode == "local":
                continue
            allowed.append(provider)

        if not allowed:
            raise ProviderUnavailable(
                f"capability {capability!r} has no provider allowed in {self.mode} mode "
                f"(available: {[p.name for p in options]})"
            )

        allowed.sort(key=lambda p: (p.is_external, p.cost_model.usd_per_unit))
        chosen = allowed[0]
        if chosen.is_external and not self.authorize_spend:
            raise SpendNotAuthorized(
                f"{chosen.name} would spend money but generation.authorize_spend is false"
            )
        self.log.write(
            "provider_selected",
            capability=capability,
            provider=chosen.name,
            external=chosen.is_external,
            mode=self.mode,
            rejected=[p.name for p in options if p is not chosen],
        )
        return chosen

    def execute(self, capability: str, request) -> Any:
        provider = self.select(capability)
        return ProviderExecutor(provider, self.guard, self.log).execute(request)

    # -- reporting ----------------------------------------------------
    def status(self) -> dict:
        rows = []
        for provider in self.providers.values():
            available, reason = provider.is_available()
            rows.append(
                {
                    "provider": provider.name,
                    "capability": provider.capability,
                    "min_mode": provider.min_mode,
                    "external": provider.is_external,
                    "available": available,
                    "reason": reason,
                    "cost_model": provider.cost_model.__dict__,
                }
            )
        return {
            "mode": self.mode,
            "authorize_spend": self.authorize_spend,
            "budget_usd": self.budget_usd,
            "spent_usd": self.guard.spent_usd,
            "providers": rows,
            "notes": self.notes,
        }

    def write_status(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.status(), fh, indent=2)


def build_registry(config: dict, *, project_dir: str | None = None) -> Registry:
    from . import external, local

    registry = Registry(config, project_dir=project_dir)
    local.register(registry)
    external.register(registry)
    return registry


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    # Environment override keeps the "no spend by default" rule even if a config
    # file is edited by hand: LOCAL cannot be escalated by an env var, only
    # de-escalated (ACS_MODE=local wins).
    env_mode = os.environ.get("ACS_MODE")
    if env_mode:
        config["mode"] = env_mode.lower()
    if os.environ.get("ACS_AUTHORIZE_SPEND") not in (None, "", "0", "false"):
        config.setdefault("generation", {})["authorize_spend"] = True
    return config
