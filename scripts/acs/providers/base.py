"""Provider abstraction: every generation capability is a plug-in.

Design rules enforced here (not just documented):
  * a provider declares its cost model before it can be used;
  * no external call can happen without `authorize_spend=True`;
  * every attempt is logged, including refusals and failures;
  * a provider that is not configured raises ProviderUnavailable instead of
    returning fake output.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


class ProviderError(RuntimeError):
    """Base class for all provider failures."""


class ProviderUnavailable(ProviderError):
    """The provider cannot run here (missing key, package, GPU, service)."""


class BudgetExceeded(ProviderError):
    """The requested spend would break the configured budget."""


class SpendNotAuthorized(ProviderError):
    """External generation was requested without explicit user authorization."""


@dataclass(frozen=True)
class CostModel:
    unit: str
    usd_per_unit: float
    notes: str = ""

    def estimate(self, units: float) -> float:
        return round(max(0.0, units) * self.usd_per_unit, 4)


@dataclass
class ProviderRequest:
    capability: str
    prompt: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    count: int = 1
    destination: str | None = None


@dataclass
class ProviderResult:
    provider: str
    capability: str
    ok: bool
    outputs: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    duration_s: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class OperationLog:
    """Append-only JSONL log. Never stores credentials or prompt secrets."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    def write(self, event: str, **payload: Any) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class CostGuard:
    """Hard budget ceiling plus an explicit authorization latch.

    LOCAL mode never needs authorization because nothing is spent. HYBRID and
    PREMIUM do: the latch is per-run, constructed only when the user approved
    external spending for this project.
    """

    def __init__(self, *, budget_usd: float, authorized: bool, log: OperationLog | None = None):
        self.budget_usd = float(budget_usd)
        self.authorized = bool(authorized)
        self.spent_usd = 0.0
        self.log = log

    def check(self, estimate_usd: float, *, is_external: bool) -> None:
        if not is_external:
            return
        if not self.authorized:
            raise SpendNotAuthorized(
                "External generation requires explicit user authorization "
                "(set generation.authorize_spend=true after the user agrees)."
            )
        if self.spent_usd + estimate_usd > self.budget_usd + 1e-9:
            raise BudgetExceeded(
                f"Estimated ${estimate_usd:.4f} would exceed the remaining "
                f"budget (${self.budget_usd - self.spent_usd:.4f} of ${self.budget_usd:.2f})."
            )

    def commit(self, amount_usd: float) -> None:
        self.spent_usd = round(self.spent_usd + amount_usd, 4)
        if self.log:
            self.log.write("spend", amount_usd=amount_usd, spent_total=self.spent_usd, budget=self.budget_usd)


class Provider(ABC):
    """Interface every generation capability must implement."""

    name: str = "unnamed"
    capability: str = "unknown"
    #: "local" | "hybrid" | "premium" — minimum mode required to be selected
    min_mode: str = "local"
    #: True when the provider performs a paid network call
    is_external: bool = False
    cost_model: CostModel = CostModel("call", 0.0, "free / local")

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Return (available, reason). Must not perform network I/O."""

    @abstractmethod
    def run(self, request: ProviderRequest, guard: CostGuard) -> ProviderResult:
        """Execute the request. Raise ProviderError subclasses on failure."""

    def estimate(self, request: ProviderRequest) -> float:
        return self.cost_model.estimate(request.count)


class ProviderExecutor:
    """Wraps a provider call with budget checks, timing and logging."""

    def __init__(self, provider: Provider, guard: CostGuard, log: OperationLog):
        self.provider = provider
        self.guard = guard
        self.log = log

    def execute(self, request: ProviderRequest) -> ProviderResult:
        available, reason = self.provider.is_available()
        if not available:
            raise ProviderUnavailable(f"{self.provider.name}: {reason}")

        estimate = self.provider.estimate(request)
        self.guard.check(estimate, is_external=self.provider.is_external)

        self.log.write(
            "provider_request",
            provider=self.provider.name,
            capability=request.capability,
            count=request.count,
            estimate_usd=estimate,
            external=self.provider.is_external,
        )
        started = time.time()
        try:
            result = self.provider.run(request, self.guard)
        except ProviderError as exc:
            self.log.write(
                "provider_error",
                provider=self.provider.name,
                capability=request.capability,
                error=str(exc),
                elapsed_s=round(time.time() - started, 3),
            )
            raise
        result.duration_s = round(time.time() - started, 3)
        if self.provider.is_external and result.cost_usd:
            self.guard.commit(result.cost_usd)
        self.log.write(
            "provider_result",
            provider=result.provider,
            capability=result.capability,
            ok=result.ok,
            outputs=result.outputs,
            cost_usd=result.cost_usd,
            duration_s=result.duration_s,
        )
        return result
