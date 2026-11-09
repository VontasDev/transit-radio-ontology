# Contributing

## Adding a new entity or event

1. Pick a name. Singular, PascalCase (`FareEvasionReport`, not `fare_evasion_reports`).
2. Write it up in `docs/02-entities.md` or `docs/03-events.md` with:
   - A plain-English definition (what is it, in one paragraph a dispatcher or PM would understand)
   - An id form (`<kind>:<agency>:<rest>`)
   - A **source tag** (`GTFS`, `TXM`, `ORION`, or `RESOLVE:<agency>:<topic>`)
   - Key properties
3. Add the JSON Schema under `schemas/entities/` or `schemas/events/`.
4. If it is cross-cutting (used by multiple events), consider adding it to `schemas/common.schema.json`.
5. Extend one of the `examples/` scenarios (or add a new one) so the shape is exercised.

## Grounding

Every addition should answer: **what operational primitive does this map to?** If the answer is "it seemed like a good idea," the ontology does not need it yet. Prefer discoverable evidence (Resolve finding, Orion bug ticket, GTFS clause) over abstract completeness.

## PRs

- Branch names: dash-separated, no slashes (e.g. `henliao-fare-evasion-event`). Matches atlas-console's CI constraint and keeps us consistent.
- One concept per PR where possible.
- No squashing of unrelated changes.
- Keep the scope of a single PR under 500 lines of new JSON + markdown. If you need more, split.
