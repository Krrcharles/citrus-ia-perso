import copy
from dataclasses import fields
import json
import unittest

from src.bodacc import (
    BodaccDialect,
    BodaccNormalizationError,
    NormalizedParty,
    extract_siren_candidates,
    normalize_bodacc_announcement,
)


def person(identifier_key, identifier, name):
    return {
        "numeroImmatriculation": {identifier_key: identifier},
        "denomination": name,
    }


def parsed_rcs_a_payload():
    return {
        "registre": "RCS-A",
        "listepersonnes": {
            "personne": [
                person("numeroIdentification", "732 829 320", "SOCIETE ACTUELLE"),
                person("numeroIdentification", 55801013, "SECONDE SOCIETE"),
            ]
        },
        "listeprecedentproprietaire": {
            "personne": [
                person("numeroIdentification", "123.456.782", "ANCIEN PROPRIETAIRE"),
                {"denomination": "PROPRIETAIRE SANS SIREN"},
            ]
        },
        "listeprecedentexploitant": {
            "personne": person(
                "numeroIdentification", "356 000 000", "ANCIEN EXPLOITANT"
            )
        },
        "listeetablissements": {
            "etablissement": [
                {"origineFonds": "Achat d'un fonds"},
                {"origineFonds": "Création"},
            ]
        },
        "acte": {
            "dateCommencementActivite": "2026-01-02",
            "dateEffet": "2026-01-03",
            "vente": {
                "descriptif": "Description de vente RCS-A",
                "publiciteLegale": {"date": "2026-01-04"},
            },
        },
        "dateparution": "2026-01-05",
        "url_complete": "https://www.bodacc.fr/annonce/test",
    }


def stringified(payload):
    result = copy.deepcopy(payload)
    for key in (
        "listepersonnes",
        "listeprecedentproprietaire",
        "listeprecedentexploitant",
        "listeetablissements",
        "acte",
    ):
        result[key] = json.dumps(result[key])
    return result


class BodaccNormalizationTest(unittest.TestCase):
    def test_stringified_and_parsed_containers_normalize_identically(self):
        parsed = normalize_bodacc_announcement(parsed_rcs_a_payload())
        encoded = normalize_bodacc_announcement(stringified(parsed_rcs_a_payload()))

        for field in fields(parsed):
            if field.name != "raw_payload":
                self.assertEqual(
                    getattr(parsed, field.name), getattr(encoded, field.name)
                )

    def test_normalization_does_not_mutate_or_retain_nested_input_references(self):
        payload = parsed_rcs_a_payload()
        before = copy.deepcopy(payload)
        normalized = normalize_bodacc_announcement(payload)

        self.assertEqual(payload, before)
        payload["listepersonnes"]["personne"][0]["denomination"] = "CHANGED"
        self.assertEqual(
            normalized.raw_payload["listepersonnes"]["personne"][0]["denomination"],
            "SOCIETE ACTUELLE",
        )

    def test_rcs_a_current_parties_main_accessors_and_siren_format(self):
        normalized = normalize_bodacc_announcement(parsed_rcs_a_payload())

        self.assertEqual(normalized.dialect, BodaccDialect.RCS_A)
        self.assertEqual(normalized.main_siren, "732829320")
        self.assertEqual(normalized.main_name, "SOCIETE ACTUELLE")
        self.assertEqual(
            normalized.current_persons,
            (
                NormalizedParty("732829320", "SOCIETE ACTUELLE"),
                NormalizedParty("055801013", "SECONDE SOCIETE"),
            ),
        )

    def test_rcs_b_identifier_and_modification_description(self):
        payload = {
            "listepersonnes": {
                "personne": person(
                    "numeroIdentificationRCS", "732.829.320", "SOCIETE RCS-B"
                )
            },
            "modificationsGenerales": json.dumps(
                {
                    "descriptif": "Description de modification RCS-B",
                    "dateEffet": "2026-02-01",
                }
            ),
        }

        normalized = normalize_bodacc_announcement(payload)

        self.assertEqual(normalized.dialect, BodaccDialect.RCS_B)
        self.assertEqual(normalized.main_siren, "732829320")
        self.assertEqual(
            normalized.modification_description,
            "Description de modification RCS-B",
        )
        self.assertEqual(
            normalized.primary_description,
            "Description de modification RCS-B",
        )
        self.assertEqual(normalized.effect_date, "2026-02-01")

    def test_previous_owners_and_operators_preserve_order_and_missing_values(self):
        normalized = normalize_bodacc_announcement(parsed_rcs_a_payload())

        self.assertEqual(
            normalized.previous_owners,
            (
                NormalizedParty("123456782", "ANCIEN PROPRIETAIRE"),
                NormalizedParty(None, "PROPRIETAIRE SANS SIREN"),
            ),
        )
        self.assertEqual(
            normalized.previous_operators,
            (NormalizedParty("356000000", "ANCIEN EXPLOITANT"),),
        )

    def test_descriptions_remain_separate_and_unknown_has_no_primary_guess(self):
        payload = parsed_rcs_a_payload()
        payload.pop("registre")
        payload["listepersonnes"] = None
        payload["modificationsGenerales"] = {
            "descriptif": "Description de modification RCS-B"
        }

        normalized = normalize_bodacc_announcement(payload)

        self.assertEqual(normalized.dialect, BodaccDialect.UNKNOWN)
        self.assertEqual(normalized.sale_description, "Description de vente RCS-A")
        self.assertEqual(
            normalized.modification_description,
            "Description de modification RCS-B",
        )
        self.assertEqual(
            normalized.all_descriptions,
            ("Description de vente RCS-A", "Description de modification RCS-B"),
        )
        self.assertIsNone(normalized.primary_description)

    def test_source_dates_url_and_origin_funds_are_independent(self):
        normalized = normalize_bodacc_announcement(parsed_rcs_a_payload())

        self.assertEqual(normalized.publication_date, "2026-01-05")
        self.assertEqual(normalized.commencement_date, "2026-01-02")
        self.assertEqual(normalized.effect_date, "2026-01-03")
        self.assertEqual(normalized.legal_publication_date, "2026-01-04")
        self.assertEqual(
            normalized.source_url, "https://www.bodacc.fr/annonce/test"
        )
        self.assertEqual(
            normalized.origin_funds, ("Achat d'un fonds", "Création")
        )
        self.assertEqual(normalized.first_origin_funds, "Achat d'un fonds")

    def test_sparse_payload_has_explicit_empty_values(self):
        normalized = normalize_bodacc_announcement(
            {
                "listepersonnes": None,
                "acte": "",
                "modificationsGenerales": "null",
            }
        )

        self.assertEqual(normalized.dialect, BodaccDialect.UNKNOWN)
        self.assertEqual(normalized.current_persons, ())
        self.assertEqual(normalized.previous_owners, ())
        self.assertEqual(normalized.previous_operators, ())
        self.assertEqual(normalized.origin_funds, ())
        self.assertEqual(normalized.all_descriptions, ())
        self.assertIsNone(normalized.main_siren)
        self.assertIsNone(normalized.main_name)
        self.assertIsNone(normalized.publication_date)

    def test_malformed_or_scalar_expected_json_has_clear_error(self):
        with self.assertRaisesRegex(
            BodaccNormalizationError, "Malformed JSON container in acte"
        ):
            normalize_bodacc_announcement({"acte": "{not-json}"})

        with self.assertRaisesRegex(
            BodaccNormalizationError, "Expected a JSON object or array"
        ):
            normalize_bodacc_announcement({"listepersonnes": '"not-a-container"'})

    def test_siren_candidates_accept_supported_forms_and_preserve_order(self):
        text = (
            "Sociétés 123.456.782, 732 829 320 et 356000000; "
            "puis à nouveau 123456782."
        )

        self.assertEqual(
            extract_siren_candidates(text),
            ("123456782", "732829320", "356000000"),
        )

    def test_siren_candidates_exclude_known_and_reject_invalid_luhn(self):
        text = "Principal 732829320, autre 123456789, cible 123 456 782."

        self.assertEqual(
            extract_siren_candidates(text, excluded_sirens={"732 829 320"}),
            ("123456782",),
        )

    def test_siren_candidates_reject_obvious_currency_amounts(self):
        text = (
            "Prix 732829320 EUR, autre prix 123.456.782 €, "
            "mais société 356 000 000."
        )

        self.assertEqual(extract_siren_candidates(text), ("356000000",))


if __name__ == "__main__":
    unittest.main()
