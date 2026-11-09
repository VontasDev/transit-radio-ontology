# 03 Events

The verbs. Events are what happens over time; entities are the nouns they hang off. Every event has at minimum a `type`, `occurredAt` (ISO 8601 UTC), `agencyId`, and a subject reference (which vehicle, operator, trip, etc. it is about).

> **Source tags** are the same as in [02-entities.md](02-entities.md).

---

## LoginEvent

An Operator assumes control of a Vehicle (and often a scheduled Trip or Block). Marks the start of the operational state transitions the ontology cares about.

- **source:** `ORION`; `RESOLVE:LBT:tests-at-logon` (tests-at-logon rule tiering)
- **schema:** [schemas/events/login-event.schema.json](../schemas/events/login-event.schema.json)
- **key properties:** `operatorId`, `vehicleId`, `tripId` (optional), `blockId` (optional), `yardId` (optional, if in a yard polygon), `occurredAt`.

## PositionUpdate

A single GPS fix from a Vehicle. These stream continuously (typically every 1-5 s). The ontology does not require you to persist all of them, but it defines the shape so producers and consumers agree.

- **source:** GTFS-Realtime `VehiclePosition`; TXM `Vehicle Journey Monitoring`; `RESOLVE:LBT:pre-crash-trail` (10-min pre-crash GPS trail primitive)
- **schema:** [schemas/events/position-update.schema.json](../schemas/events/position-update.schema.json)
- **key properties:** `vehicleId`, `lat`, `lon`, `speedMps`, `headingDeg`, `occurredAt`, optional `tripId`, `odometer`, `insideYard` (resolved from Yard polygon), `onCorridor` (resolved from Corridor geometry).

## PTTEvent

A single press-to-talk cycle. Carries press time, release time, speaker, and the Group the audio was sent on. Transmission payload (audio, transcription, classification) is modeled as a separate Transmission linked to this event.

- **source:** `ORION`; `RESOLVE:ORION:ptt-latch` (single-pulse vs double-pulse; 500 ms latch window)
- **schema:** [schemas/events/ptt-event.schema.json](../schemas/events/ptt-event.schema.json)
- **key properties:** `speakerId` (operator, dispatcher, or bot), `groupId`, `deviceId`, `pressedAt`, `releasedAt`, `durationMs`, `latchApplied` (boolean), `transmissionId` (if a Transmission object was recorded).

## Transmission

The audio and derived artifacts of a PTT cycle. One Transmission always belongs to exactly one PTTEvent. Separated because audio + transcription + classification are produced by different systems at different times.

- **source:** `ORION`; `RESOLVE:DL:case-file` (voice capture retention strata, median 214 KB snapshot = 132 MB/yr)
- **schema:** [schemas/events/transmission.schema.json](../schemas/events/transmission.schema.json)
- **key properties:** `pttEventId`, `audioUri` (where the recording lives), `transcript` (text), `transcriptionModel`, `classifications` (list of structured tags, e.g. `intent:radio-check`, `intent:accident-report`), `sentiment`, `priorityFromClassifier` (`routine|priority|emergency`).

## GroupStateUpdate

The dispatcher UI (or any client) learns that a Group's membership or state has changed: someone joined, someone left, priority tier shifted. The missing echo of this event is the ORION bug that stuck buttons on the loading wheel; it is modeled here explicitly.

- **source:** `ORION`; `RESOLVE:ORION:group-state-sync` (atlas-console PR #2131, group buttons stuck fix)
- **schema:** [schemas/events/group-state-update.schema.json](../schemas/events/group-state-update.schema.json)
- **key properties:** `groupId`, `change` (`join|leave|tier-shift|scope-change`), `subjectId`, `occurredAt`.

## Alarm

A non-voice signal from a Vehicle or Device that something needs attention: low battery, overspeed, door-open-while-moving, alarm-button press, device offline. Alarms are distinct from Transmissions (which are voice) and from AccidentReports (which are declared).

- **source:** `RESOLVE:SORTA:alarm-triage` (alarm-rule switch from "in a yard" primitive)
- **schema:** [schemas/events/alarm.schema.json](../schemas/events/alarm.schema.json)
- **key properties:** `vehicleId`, `alarmType` (`low-soc|overspeed|door-open|operator-emergency|device-offline|other`), `severity` (`info|warn|critical`), `acknowledged` (boolean), `acknowledgedBy` (dispatcher id), `occurredAt`.

## AccidentReport

A declared accident, usually initiated by an Operator over radio and confirmed by a Dispatcher in OnCall. Links to the GPS pre-crash trail (via `PositionUpdate` windows), to the Transmission that declared it, and to the optional structured injury/damage/weather/911 strata used in the Resolve DL case-file finding.

- **source:** `RESOLVE:DL:case-file` (zero of 1079 LBT accidents filled by humans in the injury/damage/911/weather fields; voice fills the gap); `RESOLVE:LBT:hit-and-run-fold` (4-spelling fold primitive, +28 found)
- **schema:** [schemas/events/accident-report.schema.json](../schemas/events/accident-report.schema.json)
- **key properties:** `vehicleId`, `operatorId`, `declaredAt`, `location` (GeoJSON Point), `severity`, `hitAndRun` (boolean), `strata` (nested: `injury`, `damage`, `nineoneone`, `weather`), `preCrashTrailRef` (identifier for a saved window of PositionUpdates), `declaringTransmissionId`.

## MissedTrip

A scheduled Trip that did not run (or ran so partially it counts as missed by the agency rulebook). Core primitive behind the SORTA staffing-driven missed-trip finding.

- **source:** GTFS-Realtime negatives; `RESOLVE:SORTA:missed-trip-staffing` (staffing-driven missed-trip)
- **schema:** [schemas/events/missed-trip.schema.json](../schemas/events/missed-trip.schema.json)
- **key properties:** `tripId`, `agencyId`, `serviceDate`, `reasonClass` (`no-operator|no-vehicle|disruption|other`), `detectedAt`.

## LatePullout

A Trip that started later than its scheduled pullout time by more than the agency's threshold.

- **source:** `RESOLVE:LBT:no-adherence-mdt` (53 pct of flagged "No-Adherence-MDT" late pullouts were actually on time; false-positive primitive)
- **schema:** [schemas/events/late-pullout.schema.json](../schemas/events/late-pullout.schema.json)
- **key properties:** `tripId`, `scheduledPullout`, `actualPullout`, `latenessSeconds`, `yardId`, `operatorId`, `vehicleId`, `flaggedBy` (e.g. `No-Adherence-MDT|GPS|dispatcher`).

## SOCAlert

An EV battery state-of-charge crossed an agency-configured threshold going down. The LBT finding: 40 pct SOC alert catches 83 pct of battery-related radio calls, median 120 min warning.

- **source:** `RESOLVE:LBT:ev-soc-alert`
- **schema:** [schemas/events/soc-alert.schema.json](../schemas/events/soc-alert.schema.json)
- **key properties:** `vehicleId`, `thresholdPct` (e.g. 40), `currentSocPct`, `estimatedMinutesRemaining`, `occurredAt`.

## DeviceHealthEvent

A radio or PTT device changed health state (degraded audio quality, dropped pulse, firmware reboot, offline). Feeds the LBT device-health-score finding.

- **source:** `RESOLVE:LBT:device-health` (1.97x held-out lift)
- **schema:** [schemas/events/device-health-event.schema.json](../schemas/events/device-health-event.schema.json)
- **key properties:** `deviceId`, `vehicleId`, `healthState` (`healthy|degraded|dropped-pulse|rebooted|offline`), `occurredAt`.

## RuleFiring

A Rule evaluated true for an event and took its declared action. These are themselves events so that downstream systems (and humans) can audit why a tier shifted or a notification was sent.

- **source:** `ORION`; `RESOLVE:LBT:priority-rtt-held-out`
- **schema:** [schemas/events/rule-firing.schema.json](../schemas/events/rule-firing.schema.json)
- **key properties:** `ruleId`, `triggeringEventType`, `triggeringEventId`, `action` (`tier-shift|notify|suppress|annotate`), `actionDetail`, `occurredAt`.
