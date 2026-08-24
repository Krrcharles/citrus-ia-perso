"""Operation extraction skills."""

from src.operation.base import OperationResult, OperationSkill
from src.operation.location_gerance import (
    LocationGeranceSkill,
    location_gerance_skill,
)
from src.operation.vente import VenteSkill, vente_skill

__all__ = (
    "LocationGeranceSkill",
    "OperationResult",
    "OperationSkill",
    "VenteSkill",
    "location_gerance_skill",
    "vente_skill",
)
