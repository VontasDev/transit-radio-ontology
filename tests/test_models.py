"""Round-trip every example through the Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from transit_radio_ontology import (
    Scenario,
    parse_entity,
    parse_event,
)
from transit_radio_ontology.models import ENTITY_KEY_TO_MODEL, EVENT_MODELS


def test_scenario_parses(example_file: Path) -> None:
    sc = Scenario.from_file(example_file)
    assert sc.events, f"no events discovered in {example_file.name}"


def test_entities_roundtrip(example_file: Path) -> None:
    raw = json.loads(example_file.read_text(encoding="utf-8"))
    for key, obj in (raw.get("entities") or {}).items():
        if not isinstance(obj, dict):
            continue
        if key.lower() not in ENTITY_KEY_TO_MODEL:
            continue
        model = parse_entity(key, obj)
        dumped = model.model_dump(exclude_none=True, mode="json")
        for field, value in obj.items():
            if field.startswith("$"):
                continue
            assert field in dumped, f"{key}.{field} missing after round-trip"


def test_events_roundtrip(example_file: Path) -> None:
    sc = Scenario.from_file(example_file)
    for evt in sc.events:
        assert type(evt).__name__ in EVENT_MODELS
        dumped = evt.model_dump(exclude_none=True, mode="json")
        # Re-parse the dumped form; should produce an equivalent model.
        reparsed = parse_event(dumped)
        assert reparsed.model_dump(exclude_none=True, mode="json") == dumped


def test_known_counts() -> None:
    # Guard against drift: ensure the exported model registries match the spec
    # (13 entities, 12 events).
    assert len(ENTITY_KEY_TO_MODEL) == 13
    assert len(EVENT_MODELS) == 12
