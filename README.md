# Transit Radio Ontology

A shared vocabulary for transit radio: who is talking, where they are, what is happening on their bus, and what the dispatcher needs to decide. Grounded in real operational data from Vontas Resolve customer studies (SORTA Cincinnati, LBT Long Beach, DL), aligned where possible with public standards (GTFS, Transmodel).

## What this is

A set of **entity definitions**, **event types**, and **relationships** that describe the world a transit radio dispatcher lives in. Written in plain English first (for operators, dispatchers, PMs), then as JSON Schema (for engineers), with pointers to public transit standards (for interop).

This ontology is the shared noun list that anything built on top of transit voice (agents, assistants, analytics, UI, case files) can reach into instead of each inventing its own terms.

## What this is not

- Not a product spec. Not a database schema. Not a replacement for GTFS.
- Not (yet) a full OWL/RDF ontology with formal axioms. See [docs/04-alignments.md](docs/04-alignments.md) for the path there.
- Not a surveillance or operator-scoring system. Entities are modeled at the role and event level, not for individual rating.

## Start here

- [docs/01-overview.md](docs/01-overview.md): The 10-minute tour. Why this exists, what problem it solves.
- [docs/02-entities.md](docs/02-entities.md): The core nouns (Agency, Vehicle, Operator, Route, Trip, Yard, Group, Device, ...).
- [docs/03-events.md](docs/03-events.md): The core verbs (PTT press, position update, alarm, accident report, login, missed trip, SOC alert, ...).
- [docs/04-alignments.md](docs/04-alignments.md): How this maps to GTFS, Transmodel, GeoSPARQL, SOSA.
- [docs/diagrams/overview.md](docs/diagrams/overview.md): Entity-relationship diagrams.
- [docs/05-usage.md](docs/05-usage.md): Installing and using the Python package (`transit_radio_ontology`).
- [schemas/](schemas/): Machine-readable JSON Schema for each entity and event.
- [examples/](examples/): Worked scenarios (radio check-in, accident case file).

## Usage

The repo ships a small Python package (`transit_radio_ontology`) with typed
Pydantic models, a JSON Schema validator, a scenario graph loader, a reference
GTFS mapper, and a CLI:

```
pip install -e ".[dev]"
transit-radio-ontology validate examples/radio-check.json
```

See [docs/05-usage.md](docs/05-usage.md) for the full walkthrough.

## Status

**MVP, v0.1.** Not yet versioned. Expect breaking changes until v0.2.

Contributions: open a PR against `main`. See the primitive sources in [docs/02-entities.md](docs/02-entities.md) for which validated findings a given entity is grounded in, so additions stay traceable to real operational evidence.

## License

Apache-2.0 (see [LICENSE](LICENSE)). Placeholder until Vontas picks a final license.
