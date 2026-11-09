# 04 Alignments

How this ontology relates to the public standards it was designed against, and what it would take to become a formal OWL ontology later.

## GTFS (General Transit Feed Specification)

Status: **reuse, do not redefine.** For the schedule and fleet layer, our entities are either GTFS concepts (Agency, Route, Trip, Stop, Calendar) or thin wrappers that add operational attributes (Vehicle extends the GTFS fleet notion with device + powertrain + SOC).

| This ontology    | GTFS                       | Notes                                                                                              |
| ---------------- | -------------------------- | -------------------------------------------------------------------------------------------------- |
| Agency           | `agency.txt`               | We prefer `agency_id` as the short code.                                                           |
| Route            | `routes.txt`               | We key on `route_short_name` because that is what dispatchers say out loud.                        |
| Trip             | `trips.txt` + service date | GTFS trip_id is not calendar-aware. We canonicalize to `trip:<agency>:<trip-id>:<service-date>`.   |
| Stop             | `stops.txt`                | Reused as-is.                                                                                      |
| Vehicle position | GTFS-Realtime VehiclePosition | Our `PositionUpdate` is a superset: adds `insideYard` and `onCorridor` resolved fields.         |

The Madrid public bus ontology ([Semantic Web Journal, 2023](https://www.semantic-web-journal.net/node/2841)) used RML mappings to convert GTFS to RDF. If we go the RDF route later, that is the reference implementation to follow.

## Transmodel

Status: **align but do not require.** Transmodel is the European reference data model for public transport, distributed as a UML specification. It is extensive, and the Madrid team found mapping it to OWL was non-trivial because UML aggregation and association semantics do not translate cleanly.

Our operational-layer entities align to Transmodel concepts where it is unambiguous:

| This ontology | Transmodel              |
| ------------- | ----------------------- |
| Agency        | Operator                |
| Vehicle       | Vehicle                 |
| Operator      | Driver                  |
| Trip          | Vehicle Journey         |
| Route         | Line / Service Pattern  |
| Yard          | Operating Base / Depot  |

We intentionally do **not** align Group, Channel, Device, PTTEvent, or Transmission. These are radio-platform concepts outside Transmodel's scope.

## GeoSPARQL

Status: **recommended for RDF serialization.** When we encode Yard polygons, Corridor LineStrings, and PositionUpdate points as RDF, use GeoSPARQL's `geo:Geometry` with WKT literals. For the JSON Schema layer, we use GeoJSON directly (simpler for engineers, same information).

## SOSA (Sensor, Observation, Sample, Actuator)

Status: **recommended for RDF serialization.** PositionUpdate, SOCAlert, and DeviceHealthEvent are SOSA Observations of a Vehicle (the ObservedFeature) by the Device (the Sensor). Modeling them this way makes it trivial to pull in third-party telematics streams.

## Internal Vontas alignments

- **Orion / OnCall:** Group, Channel, Device, PTTEvent, Transmission, GroupStateUpdate come straight from the Orion data model and the atlas-console console.
- **TransitMaster (TM):** Trip, Block, Operator assignment, LatePullout, MissedTrip align with TM BusOps concepts. The TmcDatacubeProvider (Dapr) exposes a subset of these for Resolve and other Azure-side consumers (unverified beyond the current Resolve prototype scope).
- **Icarus / Meissa / Alnilam:** PTTEvent, Transmission, and GroupStateUpdate are produced by these services in prod; wire-level formats are not this ontology's concern.

## Non-alignments and why

- **NeTEx / SIRI:** Siblings of Transmodel focused on data exchange. Interesting for cross-agency interop; out of scope for an MVP.
- **GTFS-flex:** Demand-responsive transit. Different operational model (no fixed Trips). We can add if an agency case demands it.
- **W3C Linked Data Platform:** Interesting if this ontology becomes a public endpoint; irrelevant to an internal MVP.

## Path to a formal OWL ontology

If this grows beyond JSON Schema into OWL/SHACL, these are the steps the Madrid team's experience suggests:

1. Convert each entity definition to a `rdfs:Class` with explicit domain and range axioms. Keep ids namespaced under `https://ontology.vontas.com/transit-radio#`.
2. Encode cardinality constraints in SHACL (OWL cardinalities tend to trip reasoners, as the Madrid reviewers noted).
3. Write **competency questions** for each entity (e.g. "Given an operator, which trips did they log in for this service date?") and validate the ontology can answer them via SPARQL.
4. Publish a Turtle dump and an HTML documentation site (Widoco is a common choice).
5. Register with prefix.cc for the namespace.

We do **not** recommend starting here. The engineering value in the next 90 days is 10x higher in the JSON Schema + example-driven form.

## Sources

- Public Bus Transport Ontology aligned with Transmodel (Madrid EMT, Semantic Web Journal 2023): https://www.semantic-web-journal.net/node/2841
- Applying the LOT Methodology (same paper, open version): https://semantic-web-journal.net/content/applying-lot-methodology-public-bus-transport-ontology-aligned-transmodel-challenges-and-0
- GTFS static reference: https://gtfs.org/schedule/reference/
- GTFS-Realtime reference: https://gtfs.org/realtime/reference/
- GeoSPARQL: https://www.ogc.org/standards/geosparql
- SOSA: https://www.w3.org/TR/vocab-ssn/
