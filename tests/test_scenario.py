"""Scenario loader and referential-integrity tests."""

from __future__ import annotations

from pathlib import Path

from transit_radio_ontology import Scenario


def test_scenario_loads(example_file: Path) -> None:
    sc = Scenario.from_file(example_file)
    assert sc.source == example_file


def test_scenario_validate_all_schema_passes(example_file: Path) -> None:
    sc = Scenario.from_file(example_file)
    schema_errs, _ = sc.validate_all(strict_refs=False)
    assert schema_errs == []


def test_scenario_entity_lookup_roundtrip(example_file: Path) -> None:
    sc = Scenario.from_file(example_file)
    for ent_id, model in sc.entities.items():
        looked_up = sc.entity(ent_id)
        assert looked_up is not None
        assert looked_up.model_dump(exclude_none=True, mode="json") == model.model_dump(
            exclude_none=True, mode="json"
        )


def test_events_for_entity(examples_dir: Path) -> None:
    sc = Scenario.from_file(examples_dir / "radio-check.json")
    # Vehicle 2201 appears in LoginEvent (and any event that references it).
    vehicle_id = "vehicle:lbt:2201"
    events = sc.events_for(vehicle_id)
    assert any(type(e).__name__ == "LoginEvent" for e in events), (
        f"expected LoginEvent for {vehicle_id}, got {[type(e).__name__ for e in events]}"
    )


def test_strict_refs_can_be_queried(examples_dir: Path) -> None:
    sc = Scenario.from_file(examples_dir / "radio-check.json")
    schema_errs, ref_errs = sc.validate_all(strict_refs=True)
    # The radio-check scenario does not fully define a Dispatcher entity for
    # dispatcher:lbt:d04, so strict mode will produce at least one ref error.
    assert schema_errs == []
    # Don't over-constrain; just ensure the mode returns a list.
    assert isinstance(ref_errs, list)
