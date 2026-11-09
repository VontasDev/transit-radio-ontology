# Usage

The ontology ships with a small Python package (`transit_radio_ontology`) that
provides typed models, JSON Schema validation, a scenario graph loader, a
reference GTFS mapper, and a CLI. Everything here maps one-to-one onto the
schemas under `schemas/`; the Python layer is a convenience, not a second source
of truth.

## Install

From a clone of the repo:

```
pip install -e ".[dev]"
```

Python 3.10+ is required.

## Validate a scenario file

Scenario files (see `examples/`) bundle entities and events. The validator runs
every entity and event in the file against its JSON Schema:

```
transit-radio-ontology validate examples/radio-check.json
```

On success it prints an `entities: N  events: M` line and `OK`. On failure it
exits non-zero and prints each schema error. Pass `--strict-refs` to also
require that every id-looking reference in an event resolves to an entity
defined in the same scenario.

Programmatically:

```python
from transit_radio_ontology import Scenario

scenario = Scenario.from_file("examples/radio-check.json")
schema_errors, ref_errors = scenario.validate_all(strict_refs=False)
assert not schema_errors
```

## Inspect counts

```
transit-radio-ontology inspect examples/accident-case-file.json
```

Prints the entity and event counts grouped by type. Useful for a quick sanity
check on a case file before handing it to downstream analytics.

## Build a scenario programmatically

Every entity and event has a Pydantic v2 model with the same field names as
the schema:

```python
from datetime import datetime, timezone
from transit_radio_ontology import (
    Agency, Vehicle, Operator, Device, Group, PTTEvent, Transmission,
)

agency = Agency(id="agency:lbt", shortCode="lbt",
                name="Long Beach Transit", timezone="America/Los_Angeles")
vehicle = Vehicle(id="vehicle:lbt:2201", agencyId=agency.id, fleetNumber="2201",
                  mode="bus", powertrain="bev")
device = Device(id="device:ORN-884a2f", serial="ORN-884a2f",
                vendor="trucklink", pttProfile="single-pulse",
                vehicleId=vehicle.id)
operator = Operator(id="operator:lbt:14022", agencyId=agency.id, badge="14022")
group = Group(id="group:lbt:anaheim-yard", agencyId=agency.id,
              name="Anaheim Yard", tier="routine",
              members=[operator.id])
ptt = PTTEvent(
    agencyId=agency.id,
    speakerId=operator.id,
    groupId=group.id,
    deviceId=device.id,
    pressedAt=datetime(2026, 11, 9, 13, 41, 12, tzinfo=timezone.utc),
    releasedAt=datetime(2026, 11, 9, 13, 41, 14, tzinfo=timezone.utc),
    durationMs=2000,
    latchApplied=True,
    transmissionId="tx-1",
)
```

`model_dump(mode="json", exclude_none=True)` serialises any model to the
schema-shaped JSON form.

## Map from GTFS

The ``mappers.gtfs`` module turns GTFS rows into ontology entities. GTFS does
not carry per-service-date Trip instances, so ``map_trip`` takes an explicit
service date and start/end wall-clock times (derived from ``stop_times.txt``
in a real pipeline):

```python
from transit_radio_ontology.mappers.gtfs import map_agency, map_route, map_trip

agency = map_agency(
    {"agency_id": "LBT", "agency_name": "Long Beach Transit",
     "agency_timezone": "America/Los_Angeles", "agency_lang": "en-US"},
    short_code="lbt",
)
route = map_route(
    {"route_id": "LBT-94", "agency_id": "LBT",
     "route_short_name": "94", "route_long_name": "Anaheim St",
     "route_type": "3"},
    agency_id=agency.id,
)
trip = map_trip(
    {"trip_id": "94-AM-01", "route_id": "LBT-94",
     "direction_id": "0", "block_id": "B-94-AM"},
    agency_id=agency.id,
    service_date="2026-11-09",
    scheduled_start="05:30:00",
    scheduled_end="07:14:00",
    route_id=route.id,
)
```

See `docs/04-alignments.md` for the broader GTFS / Transmodel alignment story.

## Dump a schema

```
transit-radio-ontology schema Vehicle
transit-radio-ontology list-schemas
```

`schema NAME` prints the bundled JSON Schema for one kind. `list-schemas`
prints every supported kind (entity + event).

## Validate just one object

For code that handles individual messages rather than whole scenarios:

```python
from transit_radio_ontology import validate

validate(my_ptt_dict, "PTTEvent")   # raises jsonschema.ValidationError on failure
```
