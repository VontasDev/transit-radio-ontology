"""Pydantic v2 models for every entity and event in the ontology.

Field names, types, patterns, enums, and defaults mirror the JSON Schema files
under ``schemas/`` one-to-one. ``model_config = ConfigDict(extra="forbid")``
mirrors each schema's ``additionalProperties: false``.

Use PEP 604 unions (``X | None``) and ``Optional`` via ``| None`` consistently.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# ID patterns (lifted verbatim from common.schema.json / per-entity schemas)
# ---------------------------------------------------------------------------

AGENCY_ID_PATTERN = r"^agency:[a-z][a-z0-9-]*$"
VEHICLE_ID_PATTERN = r"^vehicle:[a-z][a-z0-9-]*:[^:]+$"
OPERATOR_ID_PATTERN = r"^operator:[a-z][a-z0-9-]*:[^:]+$"
ROUTE_ID_PATTERN = r"^route:[a-z][a-z0-9-]*:[^:]+$"
TRIP_ID_PATTERN = r"^trip:[a-z][a-z0-9-]*:[^:]+:\d{4}-\d{2}-\d{2}$"
YARD_ID_PATTERN = r"^yard:[a-z][a-z0-9-]*:[^:]+$"
GROUP_ID_PATTERN = r"^group:[a-z][a-z0-9-]*:[^:]+$"
DEVICE_ID_PATTERN = r"^device:[^:]+$"
DISPATCHER_ID_PATTERN = r"^dispatcher:[a-z][a-z0-9-]*:[^:]+$"
BOT_ID_PATTERN = r"^bot:[a-z][a-z0-9-]*:[^:]+$"
CHANNEL_ID_PATTERN = r"^channel:[a-z][a-z0-9-]*:[^:]+$"
CORRIDOR_ID_PATTERN = r"^corridor:[a-z][a-z0-9-]*:[^:]+$"
RULE_ID_PATTERN = r"^rule:[a-z][a-z0-9-]*:[^:]+$"

SERVICE_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
HHMM_PATTERN = r"^\d{2}:\d{2}$"

Tier = Literal["routine", "priority", "emergency"]


# ---------------------------------------------------------------------------
# Geometry primitives (from common.schema.json $defs)
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Point(_Base):
    type: Literal["Point"]
    coordinates: List[float] = Field(..., min_length=2, max_length=3)


class Polygon(_Base):
    type: Literal["Polygon"]
    # Outer ring + optional holes; each ring is a closed list of [lon, lat].
    coordinates: List[List[List[float]]]


class LineString(_Base):
    type: Literal["LineString"]
    coordinates: List[List[float]]


class MultiLineString(_Base):
    type: Literal["MultiLineString"]
    coordinates: List[List[List[float]]]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class Agency(_Base):
    """Transit operating organization (GTFS agency.txt, Transmodel Operator)."""

    id: str = Field(..., pattern=AGENCY_ID_PATTERN)
    shortCode: str = Field(..., pattern=r"^[a-z][a-z0-9-]*$")
    name: str
    timezone: str
    gtfsAgencyId: str | None = None
    defaultLocale: str | None = None
    rulebookRef: str | None = None


class Vehicle(_Base):
    """In-service revenue vehicle."""

    id: str = Field(..., pattern=VEHICLE_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    fleetNumber: str
    vin: str | None = None
    plate: str | None = None
    mode: Literal["bus", "shuttle", "paratransit", "rail", "ferry"] = "bus"
    powertrain: Literal[
        "diesel", "hybrid", "cng", "bev", "fuel-cell", "unknown"
    ] = "unknown"
    batteryCapacityKwh: float | None = None
    deviceId: str | None = Field(default=None, pattern=r"^device:.+$")
    fleetClass: str | None = None


class Operator(_Base):
    """Licensed driver, modeled as role + credential. No performance data."""

    id: str = Field(..., pattern=OPERATOR_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    badge: str
    hireDate: date | None = None
    tenureCohort: Literal["new-30d", "new-90d", "experienced"] | None = None


class Route(_Base):
    """Named service pattern (GTFS routes.txt)."""

    id: str = Field(..., pattern=ROUTE_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    gtfsRouteId: str | None = None
    routeShortName: str
    routeLongName: str | None = None
    routeType: int | None = None
    corridorsServing: List[str] | None = Field(
        default=None, json_schema_extra={"items_pattern": r"^corridor:.+$"}
    )


class Trip(_Base):
    """Single scheduled traversal of a Route on a specific service date."""

    id: str = Field(..., pattern=TRIP_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    routeId: str = Field(..., pattern=r"^route:.+$")
    gtfsTripId: str
    blockId: str | None = None
    serviceDate: str = Field(..., pattern=SERVICE_DATE_PATTERN)
    scheduledStart: AwareDatetime
    scheduledEnd: AwareDatetime
    direction: Literal["inbound", "outbound", "loop", "unknown"] = "unknown"
    startYardId: str | None = Field(default=None, pattern=r"^yard:.+$")
    endYardId: str | None = Field(default=None, pattern=r"^yard:.+$")


class _ActiveWindow(_Base):
    start: str = Field(..., pattern=HHMM_PATTERN)
    end: str = Field(..., pattern=HHMM_PATTERN)


class Yard(_Base):
    """Physical bus storage/start/end location."""

    id: str = Field(..., pattern=YARD_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    polygon: Polygon
    capacity: int | None = None
    activeHoursLocal: Dict[str, List[_ActiveWindow]] | None = None


class Group(_Base):
    """PTT talk group."""

    id: str = Field(..., pattern=GROUP_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    tier: Tier
    members: List[str] | None = None  # operator|dispatcher|bot id patterns
    scopedTo: List[str] | None = None  # route|yard id patterns


class Device(_Base):
    """Physical PTT device (radio or mobile)."""

    id: str = Field(..., pattern=DEVICE_ID_PATTERN)
    serial: str
    model: str | None = None
    vendor: Literal[
        "trucklink", "ram", "gpslockbox", "jielie", "orion-builtin", "other"
    ]
    pttProfile: Literal["single-pulse", "double-pulse"]
    vehicleId: str | None = Field(default=None, pattern=r"^vehicle:.+$")
    firmwareVersion: str | None = None


class Dispatcher(_Base):
    """Control-room role."""

    id: str = Field(..., pattern=DISPATCHER_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    badge: str
    permissions: (
        List[
            Literal[
                "can-dispatch-console",
                "can-see-all-messages",
                "can-override-priority",
                "can-reassign-vehicle",
                "can-close-incident",
            ]
        ]
        | None
    ) = None


class Bot(_Base):
    """Non-human group/channel member."""

    id: str = Field(..., pattern=BOT_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    capabilities: List[
        Literal[
            "respond-to-radio-check",
            "route-code-blue",
            "transcribe",
            "classify-intent",
            "emergency-escalate",
            "annotate-group",
        ]
    ]
    escalationContacts: List[str] | None = None  # dispatcher|operator ids


class Channel(_Base):
    """Radio channel - convenience grouping gating Group visibility."""

    id: str = Field(..., pattern=CHANNEL_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    groups: List[str] | None = None  # group ids


class Corridor(_Base):
    """Named contiguous street segment where multiple routes converge."""

    id: str = Field(..., pattern=CORRIDOR_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    geometry: Union[LineString, MultiLineString]
    routesServing: List[str] | None = None


class _RuleWhen(_Base):
    dsl: Literal["json-logic", "sparql-select", "custom"]
    expression: Any


class _RuleThen(_Base):
    action: Literal["tier-shift", "notify", "suppress", "annotate"]
    detail: Dict[str, Any] | None = None


class Rule(_Base):
    """Declarative priority or routing rule."""

    id: str = Field(..., pattern=RULE_ID_PATTERN)
    agencyId: str = Field(..., pattern=AGENCY_ID_PATTERN)
    name: str
    description: str | None = None
    when: _RuleWhen
    then: _RuleThen
    enabled: bool = True


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class LoginEvent(_Base):
    """Operator assumes control of a Vehicle."""

    type: Literal["LoginEvent"] = "LoginEvent"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    operatorId: str = Field(..., pattern=r"^operator:.+$")
    vehicleId: str = Field(..., pattern=r"^vehicle:.+$")
    tripId: str | None = Field(default=None, pattern=r"^trip:.+$")
    blockId: str | None = None
    yardId: str | None = Field(default=None, pattern=r"^yard:.+$")
    location: Point | None = None


class PTTEvent(_Base):
    """A single press-to-talk cycle."""

    type: Literal["PTTEvent"] = "PTTEvent"
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    speakerId: str = Field(..., pattern=r"^(operator|dispatcher|bot):.+$")
    groupId: str = Field(..., pattern=r"^group:.+$")
    deviceId: str = Field(..., pattern=r"^device:.+$")
    pressedAt: AwareDatetime
    releasedAt: AwareDatetime | None = None
    durationMs: int | None = Field(default=None, ge=0)
    latchApplied: bool | None = None
    transmissionId: str | None = None
    occurredAt: AwareDatetime | None = None


class _Classification(_Base):
    key: str
    value: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class Transmission(_Base):
    """Audio and derived artifacts of a single PTTEvent."""

    type: Literal["Transmission"] = "Transmission"
    pttEventId: str
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    audioUri: str | None = None
    audioDurationMs: int | None = Field(default=None, ge=0)
    transcript: str | None = None
    transcriptionModel: str | None = None
    transcriptionConfidence: float | None = Field(default=None, ge=0, le=1)
    classifications: List[_Classification] | None = None
    priorityFromClassifier: Tier | None = None


class PositionUpdate(_Base):
    """Single GPS fix from a Vehicle."""

    type: Literal["PositionUpdate"] = "PositionUpdate"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    vehicleId: str = Field(..., pattern=r"^vehicle:.+$")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speedMps: float | None = Field(default=None, ge=0)
    headingDeg: float | None = Field(default=None, ge=0, le=360)
    odometerMeters: float | None = Field(default=None, ge=0)
    tripId: str | None = Field(default=None, pattern=r"^trip:.+$")
    operatorId: str | None = Field(default=None, pattern=r"^operator:.+$")
    insideYard: str | None = Field(default=None, pattern=r"^yard:.+$")
    onCorridor: List[str] | None = None


class Alarm(_Base):
    """Non-voice signal from a Vehicle or Device."""

    type: Literal["Alarm"] = "Alarm"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    vehicleId: str = Field(..., pattern=r"^vehicle:.+$")
    alarmType: Literal[
        "low-soc",
        "overspeed",
        "door-open-while-moving",
        "operator-emergency",
        "device-offline",
        "stop-request-stuck",
        "other",
    ]
    severity: Literal["info", "warn", "critical"]
    location: Point | None = None
    insideYard: str | None = Field(default=None, pattern=r"^yard:.+$")
    acknowledged: bool = False
    acknowledgedBy: str | None = Field(default=None, pattern=r"^dispatcher:.+$")
    acknowledgedAt: AwareDatetime | None = None
    detail: Dict[str, Any] | None = None


class _NineOneOne(_Base):
    called: bool | None = None
    atFromCaller: str | None = None
    cadId: str | None = None


class _Weather(_Base):
    conditions: str | None = None
    source: str | None = None


class _AccidentStrata(_Base):
    # The accident-report schema allows arbitrary objects under injury/damage;
    # keep them open to match "type": "object" with no further constraints.
    injury: Dict[str, Any] | None = None
    damage: Dict[str, Any] | None = None
    nineOneOne: _NineOneOne | None = None
    weather: _Weather | None = None


class AccidentReport(_Base):
    """Declared accident."""

    type: Literal["AccidentReport"] = "AccidentReport"
    declaredAt: AwareDatetime
    occurredAt: AwareDatetime | None = None
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    vehicleId: str = Field(..., pattern=r"^vehicle:.+$")
    operatorId: str = Field(..., pattern=r"^operator:.+$")
    tripId: str | None = Field(default=None, pattern=r"^trip:.+$")
    location: Point
    severity: (
        Literal[
            "minor",
            "property-damage",
            "injury",
            "serious-injury",
            "fatality",
            "unknown",
        ]
        | None
    ) = None
    hitAndRun: bool = False
    declaringTransmissionId: str | None = None
    preCrashTrailRef: str | None = None
    strata: _AccidentStrata | None = None


class MissedTrip(_Base):
    """Scheduled Trip that did not run."""

    type: Literal["MissedTrip"] = "MissedTrip"
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    tripId: str = Field(..., pattern=r"^trip:.+$")
    serviceDate: str = Field(..., pattern=SERVICE_DATE_PATTERN)
    reasonClass: Literal[
        "no-operator", "no-vehicle", "disruption", "weather", "other", "unknown"
    ]
    detectedAt: AwareDatetime


class LatePullout(_Base):
    """Trip that started later than its scheduled pullout."""

    type: Literal["LatePullout"] = "LatePullout"
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    tripId: str = Field(..., pattern=r"^trip:.+$")
    scheduledPullout: AwareDatetime
    actualPullout: AwareDatetime
    latenessSeconds: int
    yardId: str | None = Field(default=None, pattern=r"^yard:.+$")
    operatorId: str | None = Field(default=None, pattern=r"^operator:.+$")
    vehicleId: str | None = Field(default=None, pattern=r"^vehicle:.+$")
    flaggedBy: (
        Literal[
            "No-Adherence-MDT", "GPS", "dispatcher", "scheduler", "other"
        ]
        | None
    ) = None


class SOCAlert(_Base):
    """EV battery state-of-charge crossed a configured threshold going down."""

    type: Literal["SOCAlert"] = "SOCAlert"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    vehicleId: str = Field(..., pattern=r"^vehicle:.+$")
    thresholdPct: float = Field(..., ge=0, le=100)
    currentSocPct: float = Field(..., ge=0, le=100)
    estimatedMinutesRemaining: int | None = Field(default=None, ge=0)


class DeviceHealthEvent(_Base):
    """PTT device changed health state."""

    type: Literal["DeviceHealthEvent"] = "DeviceHealthEvent"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    deviceId: str = Field(..., pattern=r"^device:.+$")
    vehicleId: str | None = Field(default=None, pattern=r"^vehicle:.+$")
    healthState: Literal[
        "healthy", "degraded", "dropped-pulse", "rebooted", "offline"
    ]
    detail: Dict[str, Any] | None = None


class RuleFiring(_Base):
    """A Rule evaluated true for an event and took its declared action."""

    type: Literal["RuleFiring"] = "RuleFiring"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    ruleId: str = Field(..., pattern=r"^rule:.+$")
    triggeringEventType: str
    triggeringEventId: str | None = None
    action: Literal["tier-shift", "notify", "suppress", "annotate"]
    actionDetail: Dict[str, Any] | None = None


class GroupStateUpdate(_Base):
    """A Group's membership or state changed."""

    type: Literal["GroupStateUpdate"] = "GroupStateUpdate"
    occurredAt: AwareDatetime
    agencyId: str = Field(..., pattern=r"^agency:.+$")
    groupId: str = Field(..., pattern=r"^group:.+$")
    change: Literal["join", "leave", "tier-shift", "scope-change"]
    subjectId: str | None = None


# ---------------------------------------------------------------------------
# Unions + registries
# ---------------------------------------------------------------------------

Event = Annotated[
    Union[
        LoginEvent,
        PTTEvent,
        Transmission,
        PositionUpdate,
        Alarm,
        AccidentReport,
        MissedTrip,
        LatePullout,
        SOCAlert,
        DeviceHealthEvent,
        RuleFiring,
        GroupStateUpdate,
    ],
    Field(discriminator="type"),
]

Entity = Union[
    Agency,
    Vehicle,
    Operator,
    Route,
    Trip,
    Yard,
    Group,
    Device,
    Dispatcher,
    Bot,
    Channel,
    Corridor,
    Rule,
]


ENTITY_MODELS: Dict[str, type[BaseModel]] = {
    "Agency": Agency,
    "Vehicle": Vehicle,
    "Operator": Operator,
    "Route": Route,
    "Trip": Trip,
    "Yard": Yard,
    "Group": Group,
    "Device": Device,
    "Dispatcher": Dispatcher,
    "Bot": Bot,
    "Channel": Channel,
    "Corridor": Corridor,
    "Rule": Rule,
}

EVENT_MODELS: Dict[str, type[BaseModel]] = {
    "LoginEvent": LoginEvent,
    "PTTEvent": PTTEvent,
    "Transmission": Transmission,
    "PositionUpdate": PositionUpdate,
    "Alarm": Alarm,
    "AccidentReport": AccidentReport,
    "MissedTrip": MissedTrip,
    "LatePullout": LatePullout,
    "SOCAlert": SOCAlert,
    "DeviceHealthEvent": DeviceHealthEvent,
    "RuleFiring": RuleFiring,
    "GroupStateUpdate": GroupStateUpdate,
}

# Maps the lowercase "kind" key used in examples/*.json's entities block
# ({"agency": {...}, "vehicle": {...}}) to the model class.
ENTITY_KEY_TO_MODEL: Dict[str, type[BaseModel]] = {
    key.lower(): model for key, model in ENTITY_MODELS.items()
}

# Reverse: id-prefix (before first ":") to entity model.
ID_PREFIX_TO_MODEL: Dict[str, type[BaseModel]] = {
    "agency": Agency,
    "vehicle": Vehicle,
    "operator": Operator,
    "route": Route,
    "trip": Trip,
    "yard": Yard,
    "group": Group,
    "device": Device,
    "dispatcher": Dispatcher,
    "bot": Bot,
    "channel": Channel,
    "corridor": Corridor,
    "rule": Rule,
}


def parse_entity(kind: str, data: Dict[str, Any]) -> BaseModel:
    """Parse ``data`` as the entity named by ``kind`` (case-insensitive)."""
    key = kind.lower()
    model = ENTITY_KEY_TO_MODEL.get(key)
    if model is None:
        raise KeyError(f"Unknown entity kind: {kind!r}")
    return model.model_validate(data)


def parse_event(data: Dict[str, Any]) -> BaseModel:
    """Parse an event dict using its ``type`` discriminator field."""
    type_ = data.get("type")
    if not isinstance(type_, str):
        raise ValueError("Event dict is missing a string 'type' field")
    model = EVENT_MODELS.get(type_)
    if model is None:
        raise KeyError(f"Unknown event type: {type_!r}")
    return model.model_validate(data)


def entity_model_for_id(entity_id: str) -> type[BaseModel] | None:
    """Return the entity model whose id namespace matches ``entity_id``."""
    prefix = entity_id.split(":", 1)[0] if ":" in entity_id else ""
    return ID_PREFIX_TO_MODEL.get(prefix)
