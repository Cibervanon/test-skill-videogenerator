"""Provider subsystem: local (free) and external (paid, gated) generation."""

from .base import (  # noqa: F401
    BudgetExceeded,
    CostGuard,
    CostModel,
    OperationLog,
    Provider,
    ProviderError,
    ProviderExecutor,
    ProviderRequest,
    ProviderResult,
    ProviderUnavailable,
    SpendNotAuthorized,
)
from .registry import Registry, build_registry, load_config  # noqa: F401
