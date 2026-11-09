"""GTFS -> ontology reference mapper tests."""

from __future__ import annotations

from transit_radio_ontology.mappers.gtfs import (
    map_agency,
    map_route,
    map_trip,
)


def test_map_agency_minimal() -> None:
    row = {
        "agency_id": "LBT",
        "agency_name": "Long Beach Transit",
        "agency_timezone": "America/Los_Angeles",
        "agency_lang": "en-US",
        "agency_url": "https://lbtransit.com",
    }
    agency = map_agency(row, short_code="lbt")
    assert agency.id == "agency:lbt"
    assert agency.shortCode == "lbt"
    assert agency.name == "Long Beach Transit"
    assert agency.timezone == "America/Los_Angeles"
    assert agency.gtfsAgencyId == "LBT"
    assert agency.defaultLocale == "en-US"


def test_map_route_minimal() -> None:
    row = {
        "route_id": "LBT-94",
        "agency_id": "LBT",
        "route_short_name": "94",
        "route_long_name": "Anaheim St",
        "route_type": "3",
    }
    route = map_route(row, agency_id="agency:lbt")
    assert route.id == "route:lbt:94"
    assert route.agencyId == "agency:lbt"
    assert route.gtfsRouteId == "LBT-94"
    assert route.routeShortName == "94"
    assert route.routeLongName == "Anaheim St"
    assert route.routeType == 3


def test_map_trip_minimal() -> None:
    row = {
        "trip_id": "94-AM-01",
        "route_id": "LBT-94",
        "service_id": "WK",
        "trip_short_name": "94-am-01",
        "direction_id": "0",
        "block_id": "B-94-AM",
    }
    trip = map_trip(
        row,
        agency_id="agency:lbt",
        service_date="2026-11-09",
        scheduled_start="05:30:00",
        scheduled_end="07:14:00",
        route_id="route:lbt:94",
    )
    assert trip.id == "trip:lbt:94-am-01:2026-11-09"
    assert trip.agencyId == "agency:lbt"
    assert trip.routeId == "route:lbt:94"
    assert trip.gtfsTripId == "94-AM-01"
    assert trip.blockId == "B-94-AM"
    assert trip.serviceDate == "2026-11-09"
    assert trip.direction == "outbound"


def test_map_trip_owl_hour_wraps() -> None:
    """GTFS allows 25:xx; the mapper should clamp into a legal time-of-day."""
    row = {
        "trip_id": "94-OWL-01",
        "route_id": "LBT-94",
        "service_id": "WK",
    }
    trip = map_trip(
        row,
        agency_id="agency:lbt",
        service_date="2026-11-09",
        scheduled_start="25:10:00",
        scheduled_end="25:45:00",
        route_id="route:lbt:94",
    )
    assert trip.scheduledStart.hour == 1
    assert trip.scheduledEnd.hour == 1
