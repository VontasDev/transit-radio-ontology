"""Reference mapper: GTFS rows -> ontology entities.

Covers the three files whose GTFS -> ontology alignment is claimed in
``docs/04-alignments.md``:

* ``agency.txt`` -> :class:`Agency`
* ``routes.txt`` -> :class:`Route`
* ``trips.txt`` -> :class:`Trip` (plus a service_date argument since GTFS trips
  are schedule-only; the ontology Trip is one specific service-date run)

Keep it tiny. Real production mappers will want route_type lookups, stop_times
joining, calendar.txt / calendar_dates.txt resolution, etc. The purpose here is
to prove the alignment doc with executable code and to give consumers a
starting point they can extend.
"""

from __future__ import annotations

import re
from datetime import datetime, time, timezone
from typing import Dict

from ..models import Agency, Route, Trip

__all__ = ["map_agency", "map_route", "map_trip"]


_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slug(s: str) -> str:
    """Produce a lowercase slug suitable for the agency-short-code slot."""
    cleaned = _SLUG_RE.sub("-", s.strip().lower()).strip("-")
    return cleaned or "x"


def _hhmmss_to_time(value: str) -> time:
    """Parse a GTFS ``HH:MM:SS`` string, clamping hours into the 0-23 range.

    GTFS allows ``25:30:00`` for owl runs. This helper clamps modulo 24 and
    returns a naive ``time``; the caller combines it with a service date to
    build an aware datetime.
    """
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"bad GTFS time: {value!r}")
    h, m, s = (int(p) for p in parts)
    return time(hour=h % 24, minute=m, second=s)


def _service_date_to_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def map_agency(row: Dict[str, str], short_code: str) -> Agency:
    """Map one row of ``agency.txt`` to an :class:`Agency`.

    ``short_code`` is the lowercase slug used in all subsequent entity ids
    (``agency:<short_code>``). It is not in GTFS; agencies pick it.
    """
    sc = _slug(short_code)
    return Agency(
        id=f"agency:{sc}",
        shortCode=sc,
        name=row["agency_name"],
        timezone=row["agency_timezone"],
        gtfsAgencyId=row.get("agency_id") or None,
        defaultLocale=row.get("agency_lang") or None,
    )


def map_route(row: Dict[str, str], agency_id: str) -> Route:
    """Map one row of ``routes.txt`` to a :class:`Route`.

    ``agency_id`` must be a full ontology agency id (``agency:lbt``).
    """
    sc = agency_id.split(":", 1)[1]
    short_name = row.get("route_short_name") or row.get("route_long_name") or row["route_id"]
    route_slug = _slug(row.get("route_short_name") or row["route_id"])
    long_name = row.get("route_long_name") or None
    route_type_raw = row.get("route_type")
    route_type = int(route_type_raw) if route_type_raw not in (None, "") else None
    return Route(
        id=f"route:{sc}:{route_slug}",
        agencyId=agency_id,
        gtfsRouteId=row["route_id"],
        routeShortName=short_name,
        routeLongName=long_name,
        routeType=route_type,
    )


def map_trip(
    row: Dict[str, str],
    agency_id: str,
    service_date: str,
    scheduled_start: str,
    scheduled_end: str,
    route_id: str,
) -> Trip:
    """Map one row of ``trips.txt`` + schedule window to a :class:`Trip`.

    GTFS ``trips.txt`` does not carry scheduled start/end; those come from
    ``stop_times.txt`` joined on ``trip_id`` (min arrival, max departure). We
    take them as explicit arguments to keep the mapper small.

    ``scheduled_start`` / ``scheduled_end`` are GTFS-style ``HH:MM:SS`` in the
    agency timezone; we materialise them as UTC-offset-aware datetimes using
    ``service_date`` as the anchoring day. The anchor is UTC; downstream
    consumers that need wall-clock-accurate timestamps should convert using
    the agency timezone from :class:`Agency`.
    """
    sc = agency_id.split(":", 1)[1]
    trip_slug = _slug(row.get("trip_short_name") or row["trip_id"])
    date_ = _service_date_to_date(service_date)
    start_dt = datetime.combine(date_, _hhmmss_to_time(scheduled_start), tzinfo=timezone.utc)
    end_dt = datetime.combine(date_, _hhmmss_to_time(scheduled_end), tzinfo=timezone.utc)

    direction_raw = row.get("direction_id")
    if direction_raw == "0":
        direction = "outbound"
    elif direction_raw == "1":
        direction = "inbound"
    else:
        direction = "unknown"

    return Trip(
        id=f"trip:{sc}:{trip_slug}:{service_date}",
        agencyId=agency_id,
        routeId=route_id,
        gtfsTripId=row["trip_id"],
        blockId=row.get("block_id") or None,
        serviceDate=service_date,
        scheduledStart=start_dt,
        scheduledEnd=end_dt,
        direction=direction,
    )
