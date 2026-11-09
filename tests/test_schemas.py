"""JSON Schema validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from transit_radio_ontology import list_schemas, load_schema, validate
from transit_radio_ontology.models import ENTITY_KEY_TO_MODEL, EVENT_MODELS


def test_every_bundled_schema_is_a_valid_2020_12_schema() -> None:
    for kind in list_schemas():
        schema = load_schema(kind)
        # ``check_schema`` raises if ``schema`` isn't a valid 2020-12 schema.
        Draft202012Validator.check_schema(schema)


def test_validate_scenario_entities(example_file: Path) -> None:
    raw = json.loads(example_file.read_text(encoding="utf-8"))
    for key, obj in (raw.get("entities") or {}).items():
        model = ENTITY_KEY_TO_MODEL.get(key.lower())
        if model is None:
            continue
        validate(obj, model.__name__)


def test_validate_scenario_events(example_file: Path) -> None:
    from transit_radio_ontology.graph import _walk_event_dicts

    raw = json.loads(example_file.read_text(encoding="utf-8"))
    for raw_evt in _walk_event_dicts(raw):
        kind = raw_evt["type"]
        assert kind in EVENT_MODELS
        validate(raw_evt, kind)


def test_unknown_schema_raises() -> None:
    with pytest.raises(KeyError):
        load_schema("NotAThing")
