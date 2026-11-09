# 02 Entities

The nouns. Each entity has a plain-English definition, a canonical id form, a source note (public standard or Resolve finding), and a link to its JSON Schema.

> **Source tags**
> - `GTFS`: the entity is a GTFS concept, reused as-is.
> - `TXM`: aligned with Transmodel (via the Madrid public bus ontology).
> - `RESOLVE:SORTA|LBT|DL:<topic>`: grounded in a validated finding from a Resolve customer study.
> - `ORION`: operational concept introduced by the Orion/OnCall voice platform.

---

## Agency

A transit operating organization (e.g. SORTA, LBT). Owns routes, employs operators, runs a dispatch center.

- **id form:** `agency:<short-code>` (e.g. `agency:sorta`, `agency:lbt`)
- **source:** GTFS `agency.txt`; TXM `Operator`
- **schema:** [schemas/entities/agency.schema.json](../schemas/entities/agency.schema.json)
- **notes:** A single Vontas tenant can hold one or more agencies. An Agency owns a Rulebook (see "Rule" below) that configures priority tiers, yard polygons, and group-policy defaults.

## Vehicle

An in-service revenue vehicle. Almost always a bus in the MVP, but the ontology leaves room for other modes. Has a fixed VIN, a plate, an agency-local fleet number ("bus number"), and a device (radio) assignment that can change.

- **id form:** `vehicle:<agency>:<fleet-number>` (e.g. `vehicle:lbt:2201`)
- **source:** TXM `Vehicle`; `RESOLVE:LBT:device-health` (device health score, 1.97x held-out lift); `RESOLVE:SORTA:ev-range` (SOC primitive)
- **schema:** [schemas/entities/vehicle.schema.json](../schemas/entities/vehicle.schema.json)
- **key properties:** `vin`, `fleetNumber`, `agencyId`, `powertrain` (`diesel|hybrid|bev|cng`), `deviceId` (current radio), `fleetClass`.
- **notes:** Vehicles carry SOC (battery state of charge) when electric, which is the primitive behind the SORTA EV-range alerting finding (40 pct SOC alert catches 83 pct of battery-related radio calls, median 120 min warning).

## Operator

A person licensed to drive a Vehicle, modeled as a **role + credential** rather than an identity. We never store ratings, performance scores, or disciplinary data in this ontology.

- **id form:** `operator:<agency>:<badge>` (badge is opaque to this ontology)
- **source:** TXM `Driver`; `RESOLVE:LBT:new-operator-track` (90-day late-prone cohort, 2.3x accident rate); `RESOLVE:LBT:late-prone-cohort` (26 pct of ops drive 63 pct of breaks)
- **schema:** [schemas/entities/operator.schema.json](../schemas/entities/operator.schema.json)
- **key properties:** `badge`, `agencyId`, `hireDate`, `tenureCohort` (`new-30d|new-90d|experienced`).
- **tenureCohort** is a derived primitive used by the Resolve new-operator findings. It is not a judgment, just the bucket that unlocks the right coaching products.

## Route

A named service pattern, usually consistent over years. A Route has many Trips.

- **id form:** `route:<agency>:<route-short-name>` (e.g. `route:lbt:94`)
- **source:** GTFS `routes.txt`
- **schema:** [schemas/entities/route.schema.json](../schemas/entities/route.schema.json)
- **notes:** For transit radio purposes, the fields we use most are `route_short_name` (what the dispatcher says: "route 94"), `route_long_name`, and which Corridor(s) it traverses.

## Trip

A single scheduled traversal of a Route on a specific service date. Each Trip is assigned to a Block (the sequence of trips a single Vehicle+Operator pair completes over a service day).

- **id form:** `trip:<agency>:<gtfs-trip-id>:<service-date>`
- **source:** GTFS `trips.txt`; TXM `Vehicle Journey`
- **schema:** [schemas/entities/trip.schema.json](../schemas/entities/trip.schema.json)
- **key properties:** `tripId` (GTFS), `blockId`, `routeId`, `serviceDate`, `scheduledStart`, `scheduledEnd`, `direction`.
- **adherence** (actual vs scheduled) is a derived view, not stored here; see the `PositionUpdate` and `MissedTrip` events.

## Yard

A physical location where buses start, end, and are stored. Each yard has a geofenced polygon. Pullouts begin at a yard; pull-ins end at a yard.

- **id form:** `yard:<agency>:<short-name>` (e.g. `yard:lbt:anaheim`)
- **source:** `RESOLVE:LBT:yard-rule-priority-rtt` (the yard-rule tier primitive, 15.4 pct of RTT held-out traffic bottomed, all 159 real events kept)
- **schema:** [schemas/entities/yard.schema.json](../schemas/entities/yard.schema.json)
- **key properties:** `agencyId`, `name`, `polygon` (GeoJSON Polygon in WGS84), `capacity`, `activeHours`.
- **notes:** The yard polygon is semantically load-bearing. Many priority rules key off "is the vehicle currently inside a yard polygon?" and incident retention policy may differ for in-yard vs on-route.

## Corridor

A named contiguous segment of street where multiple Routes converge. Used for safety and incident geography: "the Anaheim corridor is 3.8x the fleet accident rate" is a Corridor-level claim.

- **id form:** `corridor:<agency>:<short-name>` (e.g. `corridor:lbt:anaheim`)
- **source:** `RESOLVE:LBT:anaheim-corridor` (3.8x accident rate held-out)
- **schema:** [schemas/entities/corridor.schema.json](../schemas/entities/corridor.schema.json)
- **key properties:** `agencyId`, `name`, `geometry` (GeoJSON LineString or MultiLineString), `routesServing`.

## Group (Talk Group)

A Push-to-Talk group on the radio platform. Operators, dispatchers, and bots are members. A Group is bound to one or more Routes/Yards by policy ("Anaheim yard group," "Route 94 ops," "FieldOps supervisors").

- **id form:** `group:<agency>:<name>` (e.g. `group:lbt:anaheim-yard`)
- **source:** `ORION`
- **schema:** [schemas/entities/group.schema.json](../schemas/entities/group.schema.json)
- **key properties:** `agencyId`, `name`, `tier` (`routine|priority|emergency`), `members` (list of Operator/Dispatcher/Bot ids), `scopedTo` (list of route or yard ids this group serves).
- **notes:** A single operator is typically in several Groups at once (the yard they start from, the route they are driving, the agency-wide emergency group). Priority routing between groups is governed by rules; see Rule below.

## Channel

A radio channel. In most Orion deployments this is a convenience grouping that gates which Groups a device can hear. Vendors and hardware differ, so the ontology keeps Channel lightweight.

- **id form:** `channel:<agency>:<name>`
- **source:** `ORION`
- **schema:** [schemas/entities/channel.schema.json](../schemas/entities/channel.schema.json)
- **key properties:** `agencyId`, `name`, `groups` (list of Group ids reachable on this channel).

## Device

The physical radio (or PTT-capable mobile) assigned to a Vehicle. Carries a model and a PTT behavior profile (single-pulse vs double-pulse latch), which matters because some USB mics (Trucklink, RAM, GPSLockbox) only emit one pulse per edge and need a latch.

- **id form:** `device:<serial>`
- **source:** `ORION`; `RESOLVE:ORION:ptt-latch` (ORION-545, single-pulse mics; MediaSessionDoublePulseCallback, 500 ms latch)
- **schema:** [schemas/entities/device.schema.json](../schemas/entities/device.schema.json)
- **key properties:** `serial`, `model`, `vendor` (e.g. `trucklink|ram|gpslockbox|jielie|builtin`), `pttProfile` (`single-pulse|double-pulse`), `vehicleId` (current assignment), `firmwareVersion`.

## Dispatcher

A control-room role with authority to dispatch, log incidents, and reassign vehicles. Modeled, like Operator, as a role + credential.

- **id form:** `dispatcher:<agency>:<badge>`
- **source:** `ORION`
- **schema:** [schemas/entities/dispatcher.schema.json](../schemas/entities/dispatcher.schema.json)
- **key properties:** `badge`, `agencyId`, `permissions` (e.g. `can-dispatch-console`, `can-see-all-messages`, `can-override-priority`).

## Bot

A non-human member of a Group or Channel (voice AI assistant, radio-check bot, incident-triage bot). Isolated from Operator so analytics never mix human and bot traffic.

- **id form:** `bot:<agency>:<name>`
- **source:** `ORION`
- **schema:** [schemas/entities/bot.schema.json](../schemas/entities/bot.schema.json)
- **key properties:** `agencyId`, `name`, `capabilities` (list of what it can do, e.g. `respond-to-radio-check|route-code-blue|transcribe`), `escalationContacts` (who it pings when stuck).

## Rule

A declarative priority or routing rule, scoped to an Agency. Rules are the primitives behind "priority RTT tiering," "yard rule," "tests-at-logon."

- **id form:** `rule:<agency>:<name>`
- **source:** `RESOLVE:LBT:priority-rtt-held-out` (yard rule + tests-at-logon + priority-RTT yard, 164 of 1068 events, 15.4 pct)
- **schema:** [schemas/entities/rule.schema.json](../schemas/entities/rule.schema.json)
- **key properties:** `agencyId`, `name`, `when` (JSON-Logic or SPARQL-like predicate on events/entities), `then` (action: tier shift, notify, suppress).

---

## Relationships

A quick tour of how these connect. See [diagrams/overview.md](diagrams/overview.md) for the picture.

- An **Agency** has many Vehicles, Operators, Dispatchers, Routes, Yards, Corridors, Groups, Channels, Rules.
- A **Vehicle** is assigned to zero or one **Operator** at a time (`LoginEvent` is how the assignment changes).
- A **Vehicle** is assigned to zero or one **Trip** at a time.
- A **Vehicle** carries exactly one **Device** at a time (configurable; swaps emit DeviceReassigned).
- A **Trip** runs on exactly one **Route** and crosses zero or more **Corridors**.
- A **Yard** is a start/end point for many Trips.
- A **Group** has many **Operators**, **Dispatchers**, and **Bots** as members, and is scoped to zero or more **Routes** or **Yards**.
- A **Rule** applies to an **Agency** and can fire based on any event in the next section.
