"""Scenario: a loaded collection of entities + events with referential checks.

Scenarios in ``examples/*.json`` do not share a single top-level event array:
``radio-check.json`` uses ``events``; ``accident-case-file.json`` splits them
across ``preCrashTrail.events`` and ``declaration``. The Scenario walker finds
events anywhere in the tree by looking for dicts whose ``type`` matches one of
the known event types.

Public API:
    Scenario.from_file(path)
    Scenario.from_dict(d)
    scenario.entities          # dict[id -> Entity model]
    scenario.events            # list[Event model]
    scenario.entity(id)        # typed lookup
    scenario.events_for(id)    # events that reference the given entity id
    scenario.validate_all()    # JSON Schema + referential integrity

load_scenario(path) is a convenience alias for Scenario.from_file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Tuple

from pydantic import BaseModel

from .models import (
    ENTITY_KEY_TO_MODEL,
    EVENT_MODELS,
    ID_PREFIX_TO_MODEL,
    entity_model_for_id,
    parse_entity,
    parse_event,
)
from .schemas import ValidationError, validate

__all__ = ["Scenario", "load_scenario"]


_ID_RE = re.compile(
    r"^(?:agency|vehicle|operator|route|trip|yard|group|device|dispatcher|bot|"
    r"channel|corridor|rule):[^\s]+$"
)


def _is_id_string(v: Any) -> bool:
    return isinstance(v, str) and bool(_ID_RE.match(v))


def _iter_id_values(obj: Any) -> Iterator[str]:
    """Yield every id-looking string found anywhere in ``obj``."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_id_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_id_values(v)
    elif _is_id_string(obj):
        yield obj


class Scenario:
    """Parsed, typed, graph-queryable scenario."""

    def __init__(
        self,
        entities: Dict[str, BaseModel],
        events: List[BaseModel],
        source: Path | None = None,
        raw: Dict[str, Any] | None = None,
    ) -> None:
        self._entities: Dict[str, BaseModel] = dict(entities)
        self._events: List[BaseModel] = list(events)
        self.source: Path | None = source
        self.raw: Dict[str, Any] = raw or {}

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> "Scenario":
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        sc = cls.from_dict(data)
        sc.source = p
        return sc

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        entities = _extract_entities(data.get("entities", {}) or {})
        events = _extract_events(data)
        return cls(entities=entities, events=events, raw=data)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def entities(self) -> Dict[str, BaseModel]:
        return dict(self._entities)

    @property
    def entities_by_id(self) -> Dict[str, BaseModel]:
        return dict(self._entities)

    @property
    def events(self) -> List[BaseModel]:
        return list(self._events)

    def entity(self, entity_id: str) -> BaseModel | None:
        return self._entities.get(entity_id)

    def events_for(self, entity_id: str) -> List[BaseModel]:
        """Events that reference ``entity_id`` in any id-looking field."""
        out: List[BaseModel] = []
        for evt in self._events:
            # Walk the serialised dict so we hit nested id fields too.
            data = evt.model_dump(exclude_none=True, mode="json")
            if entity_id in set(_iter_id_values(data)):
                out.append(evt)
        return out

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_all(
        self, strict_refs: bool = False
    ) -> Tuple[List[str], List[str]]:
        """Validate every entity and event against its JSON Schema and check
        referential integrity.

        Returns ``(schema_errors, ref_errors)``. Both lists are empty if the
        scenario is valid. Referential errors are returned instead of raised so
        callers can decide the policy (``strict_refs=True`` collects errors for
        any id reference that does not resolve inside the scenario).
        """
        schema_errors: List[str] = []
        ref_errors: List[str] = []

        # Entity schemas.
        raw_entities = self.raw.get("entities", {}) or {}
        for key, obj in raw_entities.items():
            model_cls = ENTITY_KEY_TO_MODEL.get(key.lower())
            if model_cls is None:
                schema_errors.append(f"unknown entity kind: {key!r}")
                continue
            kind = model_cls.__name__
            try:
                validate(obj, kind)
            except ValidationError as e:
                schema_errors.append(f"entity[{key}]: {e.message}")

        # Event schemas.
        for i, raw_evt in enumerate(_walk_event_dicts(self.raw)):
            kind = raw_evt.get("type")
            if kind not in EVENT_MODELS:
                schema_errors.append(f"event[{i}]: unknown type {kind!r}")
                continue
            try:
                validate(raw_evt, kind)
            except ValidationError as e:
                schema_errors.append(f"event[{i}]({kind}): {e.message}")

        # Referential integrity.
        known_ids = set(self._entities.keys())
        for evt in self._events:
            data = evt.model_dump(exclude_none=True, mode="json")
            evt_type = data.get("type", type(evt).__name__)
            for ref in set(_iter_id_values(data)):
                prefix = ref.split(":", 1)[0]
                if prefix not in ID_PREFIX_TO_MODEL:
                    continue
                if ref not in known_ids:
                    msg = (
                        f"{evt_type}: reference to {ref!r} "
                        "does not resolve to any scenario entity"
                    )
                    if strict_refs:
                        ref_errors.append(msg)

        # Also check entity-to-entity references (e.g. Device.vehicleId).
        for ent_id, model in self._entities.items():
            data = model.model_dump(exclude_none=True, mode="json")
            for ref in set(_iter_id_values(data)):
                if ref == ent_id:
                    continue
                prefix = ref.split(":", 1)[0]
                if prefix not in ID_PREFIX_TO_MODEL:
                    continue
                if ref not in known_ids and strict_refs:
                    ref_errors.append(
                        f"entity[{ent_id}]: reference to {ref!r} does not "
                        "resolve to any scenario entity"
                    )

        return schema_errors, ref_errors

    # ------------------------------------------------------------------
    # Dunder niceties
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        src = f" source={self.source}" if self.source else ""
        return (
            f"<Scenario entities={len(self._entities)} "
            f"events={len(self._events)}{src}>"
        )

    def __iter__(self) -> Iterator[BaseModel]:
        yield from self._events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_entities(raw: Dict[str, Any]) -> Dict[str, BaseModel]:
    out: Dict[str, BaseModel] = {}
    for key, obj in raw.items():
        if not isinstance(obj, dict):
            continue
        model_cls = ENTITY_KEY_TO_MODEL.get(key.lower())
        if model_cls is None:
            continue
        model = parse_entity(key, obj)
        obj_id = getattr(model, "id", None)
        if obj_id:
            out[obj_id] = model
    return out


def _walk_event_dicts(root: Any) -> Iterable[Dict[str, Any]]:
    """Yield every dict whose ``type`` matches a known event type.

    Skips the top-level ``entities`` block so entity dicts are never confused
    with events.
    """
    if isinstance(root, dict):
        skip_keys = {"entities"} if root is root else set()
        # The above expression is always {"entities"} at the top level; written
        # this way so we can pass sub-dicts recursively without skipping.
        for key, value in root.items():
            if key == "entities":
                continue
            if isinstance(value, dict):
                if isinstance(value.get("type"), str) and value["type"] in EVENT_MODELS:
                    yield value
                yield from _walk_event_dicts(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if isinstance(item.get("type"), str) and item["type"] in EVENT_MODELS:
                            yield item
                        yield from _walk_event_dicts(item)
    elif isinstance(root, list):
        for item in root:
            yield from _walk_event_dicts(item)


def _extract_events(data: Dict[str, Any]) -> List[BaseModel]:
    out: List[BaseModel] = []
    for raw_evt in _walk_event_dicts(data):
        out.append(parse_event(raw_evt))
    return out


def load_scenario(path: str | Path) -> Scenario:
    """Load a scenario file into a parsed :class:`Scenario`."""
    return Scenario.from_file(path)
