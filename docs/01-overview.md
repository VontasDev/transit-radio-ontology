# 01 Overview

## Why an ontology for transit radio?

Transit radio is a conversation between three populations, mediated by push-to-talk:

- **Operators** on buses. They talk when something is non-routine: a radio check at pullout, a rider dispute, a bus that will not start, a passenger medical event, an accident.
- **Dispatchers** in a control room. They listen to many channels, make priority calls, dispatch police or supervisors, and keep a running mental model of which bus is where and what state it is in.
- **Agents, assistants, and analytics** (increasingly). Software that transcribes, classifies, tags, routes, and, for routine traffic, answers.

Every team that touches this domain reinvents the same nouns: "operator," "run," "block," "yard," "group," "channel," "alarm." They end up with slightly different definitions, inconsistent ids, and no shared way to talk about events that span radio, GPS, device health, and schedule adherence.

The **transit radio ontology** is the shared noun list. It lets a radio check at 05:48 on bus 2201 be linked, without custom glue, to the trip it was reporting for, the yard it departed from, the operator who pressed the button, the agency rulebook that defines "pullout," and the dispatcher who logged it in OnCall.

## What it covers

Three tiers:

1. **Fleet and schedule (reused from GTFS):** Agency, Route, Trip, Stop, Calendar. We do not redefine these. We point at GTFS.
2. **Operational layer (new, but Transmodel-aware):** Operator, Yard, Corridor, Vehicle-in-service, Group (radio talk group), Channel, Device (radio hardware).
3. **Interaction layer (where the radio lives, and where we have the most novel content):** PTT event, Transmission, Alarm, AccidentReport, LoginEvent, PositionUpdate, SOCAlert, MissedTrip.

## What problem it solves

**Concrete scenario, LBT 2026-09-14:** operator on route 94 presses PTT at 15:43:07 saying "I just hit something." The dispatcher needs:

- Who is pressing (operator id and name)
- Which bus (vehicle id, VIN, license plate)
- Which trip (trip id, block, service day)
- Where (lat/lon, intersection, which corridor, which yard they came from)
- What happened just before (last 10 minutes of GPS, speed, any alarms)
- What usually happens next (incident flow: 911? supervisor? tow?)

Today this comes from three different systems (CAD/AVL, radio console, ERP). With a shared ontology, the event itself knows how to link to all of it. An agent (human or software) handling the call reads one object, not five.

## The method

Each entity and event in this ontology is **grounded** in a real operational primitive observed in the Vontas Resolve customer studies (SORTA Cincinnati, LBT Long Beach, DL). Where possible it maps to a **public standard**:

- GTFS for schedule / service / route primitives
- Transmodel (via the Madrid public bus ontology, Semantic Web Journal 2023) for operator, journey, service pattern
- GeoSPARQL for geometry (yard polygons, corridor segments)
- SOSA for sensor observations (device health, SOC, GPS)

Where no public standard exists (PTT events, radio groups, talk-group priority, yard-rule semantics), we introduce new terms with explicit definitions and grounded examples.

## Design principles

1. **Operational over administrative.** The ontology models what happens, not what is billed. "An operator presses PTT" is in; "an operator is on a payroll run number" is out.
2. **Event-first.** Entities exist to carry events. A Vehicle is not interesting without a PositionUpdate stream. An Operator is not interesting without a LoginEvent.
3. **Traceable to evidence.** Every entity's definition cites either a public standard or a specific finding from Resolve. Nothing is defined because it "sounds right."
4. **Role, not person.** Operators and dispatchers are modeled as roles with credentials, not as scored individuals. Analytics work (late-prone cohort, new-operator track) is at the cohort level, not per-person.
5. **Explicit uncertainty.** Where a primitive (e.g. "pullout time") varies by agency, we call it out and let agencies override.

## Non-goals for this MVP

- Formal OWL axioms and reasoners (see [04-alignments.md](04-alignments.md) for the path)
- Full Transmodel coverage (we pick the bus-dispatch slice)
- Multimodal (rail, ferry) beyond the obvious generalizations
- Anything that requires SSO, PII keys, or secrets
- UI, API, or storage layer. This is a vocabulary.

## Audience

- **Product and design** people writing specs: use these nouns verbatim so your spec and engineering share a model.
- **Engineers** writing event producers or consumers: use the JSON Schemas directly.
- **Analysts** and **Resolve** customer studies: cite the entity/event ids in findings so downstream work can replay.
- **Partners** (voice AI, telematics, CAD/AVL): map your incoming data to these shapes once; then every Vontas product understands it.
