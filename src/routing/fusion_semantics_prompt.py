"""Versioned prompt for source-grounded fusion-family semantics."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any


FUSION_SEMANTICS_PROMPT_VERSION = "fusion-semantics-v1"


def build_fusion_semantic_messages(
    context: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Build deterministic French messages from normalized source facts."""

    system = """Tu analyses une annonce légale BODACC déjà rattachée à la famille des fusions, absorptions, scissions ou apports partiels d'actifs.

Ta sortie décrit uniquement les faits que cette annonce individuelle établit. Tu ne choisis aucun code d'opération final et tu ne complètes jamais un fait pour rendre l'annonce compatible avec une classification finale supposée.

Valeurs autorisées pour kind :
- FUSION : l'annonce décrit une fusion ou une absorption entre sociétés ;
- SCISSION : l'annonce décrit une scission ou la répartition d'un patrimoine entre bénéficiaires ;
- PARTIAL_ASSET_TRANSFER : l'annonce décrit explicitement un apport partiel d'actifs ou une branche d'activité apportée ;
- UNKNOWN : la nature locale est absente, ambiguë ou contradictoire.

Axes sémantiques autorisés :
- transfer_scope : TOTAL seulement si l'annonce établit la transmission de tout le patrimoine, PARTIAL seulement si elle établit une partie, une branche ou des actifs limités, UNKNOWN sinon ;
- transferor_fate : DISAPPEARS seulement si l'annonce établit la dissolution, la disparition ou l'absence de survie du cédant, SURVIVES seulement si sa continuation est établie, UNKNOWN sinon ;
- beneficiary_creation : NEW seulement si l'annonce établit que le bénéficiaire est créé pour l'opération, EXISTING seulement si elle établit qu'il préexiste, MIXED_OR_UNKNOWN si les situations sont mixtes ou si le fait n'est pas établi.

Ne déduis jamais NEW ou EXISTING de la classification finale qu'une opération devrait recevoir. La seule présence d'un participant, d'un numéro ou du mot « bénéficiaire » ne suffit pas à établir sa création. De même, ne déduis jamais la disparition ou la survie du cédant en l'absence d'une indication source. Conserve les valeurs d'incertitude quand l'annonce ne tranche pas.

Participants :
- role vaut TRANSFEROR pour un apporteur, une société absorbée ou scindée qui transmet ; BENEFICIARY pour une société absorbante ou bénéficiaire qui reçoit ; BOTH_OR_UNCLEAR si les deux rôles coexistent ou si le rôle local ne peut pas être établi ;
- siren est une chaîne de neuf chiffres seulement lorsque ce SIREN est explicitement présent dans le contexte ; sinon siren vaut null ;
- name reprend un nom explicitement présent ; sinon name vaut null ;
- ne transforme pas un montant, un capital ou un autre nombre en SIREN et n'invente pas un participant.

Réponds uniquement par un objet JSON valide, sans Markdown ni texte autour, avec exactement les champs suivants :
{"kind":"FUSION|SCISSION|PARTIAL_ASSET_TRANSFER|UNKNOWN","transfer_scope":"TOTAL|PARTIAL|UNKNOWN","transferor_fate":"DISAPPEARS|SURVIVES|UNKNOWN","beneficiary_creation":"NEW|EXISTING|MIXED_OR_UNKNOWN","participants":[{"siren":"123456782","name":"NOM SOURCE","role":"TRANSFEROR|BENEFICIARY|BOTH_OR_UNCLEAR"}],"evidence":["indice source bref"],"reason":"une phrase concise fondée sur la source"}

participants peut être vide et contient au plus vingt objets. Pour un SIREN ou un nom absent, utilise la valeur JSON null, jamais la chaîne "null". evidence contient de zéro à six extraits ou indices brefs. reason est une phrase concise et ne doit pas contenir de raisonnement caché ou détaillé."""
    compact_context = json.dumps(
        dict(context),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    user = (
        "Contexte source normalisé de l'annonce à analyser :\n"
        f"{compact_context}\n\n"
        "Commence directement la réponse par { et termine-la par }. "
        "N'ajoute aucune balise Markdown ni aucun nom de langage."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


__all__ = (
    "FUSION_SEMANTICS_PROMPT_VERSION",
    "build_fusion_semantic_messages",
)
