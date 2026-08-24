"""Minimal contract shared by operation extraction skills."""

from typing import Any, ClassVar, Protocol, TypedDict, runtime_checkable


class OperationResult(TypedDict):
    """Business prediction produced for one BODACC announcement."""

    anneeCampagne: int
    typeOperation: str
    sirenCedant: str
    raisonSocialeCedant: str
    sirenBeneficiaire: str
    raisonSocialeBeneficiaire: str
    dateEffetComptable: str
    dateRealisationJuridique: None
    montantNet: int
    source: str


@runtime_checkable
class OperationSkill(Protocol):
    """Small boundary implemented by an announcement-level operation skill."""

    operation_type: ClassVar[str]

    def extract(self, announcement: dict[str, Any]) -> OperationResult:
        """Extract a Citrus-like business prediction from an announcement."""
        ...
