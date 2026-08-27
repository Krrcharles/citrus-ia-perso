"""Public semantic family-routing boundary."""

from src.routing.prompt import ROUTER_PROMPT_VERSION
from src.routing.router import (
    FamilyRouter,
    ROUTING_TAXONOMY_VERSION,
    RoutingError,
    RoutingFamily,
    RoutingLLMError,
    RoutingOutputError,
    RoutingResult,
    build_routing_context,
    family_router,
    validate_routing_output,
)


__all__ = (
    "FamilyRouter",
    "ROUTER_PROMPT_VERSION",
    "ROUTING_TAXONOMY_VERSION",
    "RoutingError",
    "RoutingFamily",
    "RoutingLLMError",
    "RoutingOutputError",
    "RoutingResult",
    "build_routing_context",
    "family_router",
    "validate_routing_output",
)
