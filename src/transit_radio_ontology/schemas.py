"""JSON Schema validation against the bundled ontology schemas.

The ``schemas/`` tree is force-included into the wheel at
``transit_radio_ontology/_schemas`` (see pyproject.toml). Schemas use relative
``$ref`` (e.g. ``../common.schema.json#/$defs/Polygon``), resolved here via a
``jsonschema`` ``Registry`` keyed by each schema's ``$id``.

Public API:
    load_schema(name)      -> raw dict
    list_schemas()         -> dict of known names
    validate(instance, kind)
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Iterable

from jsonschema import Draft202012Validator
from jsonschema import ValidationError  # re-exported
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

__all__ = [
    "ValidationError",
    "load_schema",
    "list_schemas",
    "validate",
    "schema_path",
]


# ---------------------------------------------------------------------------
# Locate the bundled schemas tree.
# ---------------------------------------------------------------------------
# When installed as a wheel, schemas live at
# ``transit_radio_ontology/_schemas/*``. In an editable install from a source
# checkout, the same path works because we force-include the top-level
# ``schemas/`` dir. As a last-resort fallback for running tests directly out of
# a source tree without the force-include being materialised yet, walk up to
# find the repo-root ``schemas/`` directory.

def _candidate_roots() -> Iterable[Path]:
    # 1. Installed location (hatch force-include).
    pkg = resources.files("transit_radio_ontology")
    installed = Path(str(pkg)) / "_schemas"
    yield installed

    # 2. Source-tree sibling (repo_root/schemas), useful for `pytest` from a
    #    source checkout without hatch materialising the include.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "schemas"
        if (candidate / "common.schema.json").exists():
            yield candidate
            break


def _schemas_root() -> Path:
    for root in _candidate_roots():
        if (root / "common.schema.json").exists():
            return root
    raise FileNotFoundError(
        "Could not locate bundled schemas directory (transit_radio_ontology/_schemas/)"
    )


# Map of human-friendly kind name -> relative path under schemas/.
_KIND_TO_RELPATH: Dict[str, str] = {
    "Common": "common.schema.json",
    # Entities
    "Agency": "entities/agency.schema.json",
    "Vehicle": "entities/vehicle.schema.json",
    "Operator": "entities/operator.schema.json",
    "Route": "entities/route.schema.json",
    "Trip": "entities/trip.schema.json",
    "Yard": "entities/yard.schema.json",
    "Group": "entities/group.schema.json",
    "Device": "entities/device.schema.json",
    "Dispatcher": "entities/dispatcher.schema.json",
    "Bot": "entities/bot.schema.json",
    "Channel": "entities/channel.schema.json",
    "Corridor": "entities/corridor.schema.json",
    "Rule": "entities/rule.schema.json",
    # Events
    "LoginEvent": "events/login-event.schema.json",
    "PTTEvent": "events/ptt-event.schema.json",
    "Transmission": "events/transmission.schema.json",
    "PositionUpdate": "events/position-update.schema.json",
    "Alarm": "events/alarm.schema.json",
    "AccidentReport": "events/accident-report.schema.json",
    "MissedTrip": "events/missed-trip.schema.json",
    "LatePullout": "events/late-pullout.schema.json",
    "SOCAlert": "events/soc-alert.schema.json",
    "DeviceHealthEvent": "events/device-health-event.schema.json",
    "RuleFiring": "events/rule-firing.schema.json",
    "GroupStateUpdate": "events/group-state-update.schema.json",
}


def list_schemas() -> Dict[str, str]:
    """Return a copy of the kind -> relative-path mapping."""
    return dict(_KIND_TO_RELPATH)


def schema_path(kind: str) -> Path:
    """Absolute path of the bundled schema file for ``kind``."""
    try:
        rel = _KIND_TO_RELPATH[kind]
    except KeyError as exc:
        raise KeyError(f"Unknown schema kind: {kind!r}") from exc
    return _schemas_root() / rel


@lru_cache(maxsize=None)
def load_schema(kind: str) -> Dict[str, Any]:
    """Return the parsed JSON Schema dict for ``kind`` (e.g. ``"Vehicle"``)."""
    with schema_path(kind).open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Registry + validator cache
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _registry() -> Registry:
    """Build a jsonschema Registry populated with every bundled schema.

    Schemas are registered twice:
        - under their canonical ``$id`` URI, and
        - under their relative-path URI (e.g. ``../common.schema.json``) so
          that ``$ref`` strings resolve against the referencing schema's
          location without further massaging.
    """
    root = _schemas_root()
    reg = Registry()
    resources_to_add: list[tuple[str, Resource]] = []

    for kind, rel in _KIND_TO_RELPATH.items():
        schema = load_schema(kind)
        resource = Resource(contents=schema, specification=DRAFT202012)

        # Register under $id.
        canonical = schema.get("$id")
        if canonical:
            resources_to_add.append((canonical, resource))

        # Register under absolute file path URI so relative refs work.
        abs_path = (root / rel).resolve().as_uri()
        resources_to_add.append((abs_path, resource))

    return reg.with_resources(resources_to_add)


def _validator_for(kind: str) -> Draft202012Validator:
    schema = load_schema(kind)
    return Draft202012Validator(schema, registry=_registry())


def validate(instance: Any, kind: str) -> None:
    """Validate ``instance`` against the schema named ``kind``.

    Raises ``jsonschema.ValidationError`` on failure.
    """
    _validator_for(kind).validate(instance)
