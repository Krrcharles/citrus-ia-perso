"""Operation extraction skills."""

from src.operation.base import OperationResult, OperationSkill
from src.operation.vente import VenteSkill, vente_skill

__all__ = ("OperationResult", "OperationSkill", "VenteSkill", "vente_skill")
