"""External search tools for the AI Travel Agent."""
import os
from datetime import datetime, timezone
from typing import Optional

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field

SERPAPI_URL = "https://serpapi.com/search.json"


def _serpapi_search(params: dict) -> dict:
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return {"error": "SERPAPI_API_KEY is missing. Add it to your .env file."}
    request_params = dict(params)
    request_params["api_key"] = api_key
    try:
        response = requests.get(SERPAPI_URL, params=request_params, timeout=35)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            return {"error": data["error"]}
        return data
    except requests.RequestException as exc:
        return {"error": f"SerpAPI request failed: {exc}"}
    except ValueError:
        return {"error": "SerpAPI returned invalid JSON."}


def _number(value):
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("₹", "").strip()
        return float(value)
    except (TypeError, ValueError):
        return None


def _duration_minutes(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _booking_link(flight: dict) -> Optional[str]:
    options = flight.get("booking_options") or []
    for option in options:
        for key in ("booking_url", "url", "link"):
            link = option.get(key) if isinstance(option, dict) else None
            if isinstance(link, str) and link.startswith(("https://", "http://")):
                return link
    return None


class FlightSearchInput(BaseModel):
    departure_airport: str = Field(description="Origin IATA airport code, e.g. DEL")
    arrival_airport: str = Field(description="Destination IATA airport code, e.g. BOM")
    outbound_date: str = Field(description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(default=None, description="Return date YYYY-MM-DD for round trip; omit for one-way")
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    infants_in_seat: int = Field(default=0, ge=0, le=8)
    infants_on_lap: int = Field(default=0, ge=0, le=8)
    stops: int = Field(default=1, ge=0, le=2, description="Maximum stops: 0 nonstop, 1 one stop, 2 any")


@tool("search_flights", args_schema=FlightSearchInput)
def search_flights(departure_airport: str, arrival_airport: str, outbound_date: str,
                   return_date: Optional[str] = None, adults: int = 1, children: int = 0,
                   infants_in_seat: int = 0, infants_on_lap: int = 0, stops: int = 1) -> dict:
    """Search Google Flights via SerpApi. Airport codes must be IATA codes."""
    params = {
        "engine": "google_flights", "hl": "en", "gl": "in", "currency": "INR",
        "departure_id": departure_airport.upper(), "arrival_id": arrival_airport.upper(),
        "outbound_date": outbound_date, "adults": adults, "children": children,
        "infants_in_seat": infants_in_seat, "infants_on_lap": infants_on_lap,
        "stops": str(stops),
    }
    if return_date:
        params["return_date"] = return_date
    data = _serpapi_search(params)
    if "error" in data:
        return data
    flights = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    simplified = []
    seen = set()
    fetched_at = datetime.now(timezone.utc).isoformat()
    for flight in flights[:12]:
        legs = flight.get("flights") or []
        first_leg = legs[0] if legs else {}
        last_leg = legs[-1] if legs else {}
        layovers = flight.get("layovers") or []
        stop_count = len(layovers) if layovers else max(0, len(legs) - 1)
        item = {
            "airline": first_leg.get("airline") or "Airline not provided",
            "flight_number": first_leg.get("flight_number"),
            "origin": (first_leg.get("departure_airport") or {}).get("id") or departure_airport.upper(),
            "destination": (last_leg.get("arrival_airport") or {}).get("id") or arrival_airport.upper(),
            "departure_at": (first_leg.get("departure_airport") or {}).get("time"),
            "arrival_at": (last_leg.get("arrival_airport") or {}).get("time"),
            "duration_minutes": _duration_minutes(flight.get("total_duration")),
            "stops": stop_count,
            "price": _number(flight.get("price")),
            "currency": "INR",
            "booking_url": _booking_link(flight),
            "source": "SerpApi Google Flights",
            "fetched_at": fetched_at,
            "legs": [{
                "airline": leg.get("airline"),
                "flight_number": leg.get("flight_number"),
                "departure": leg.get("departure_airport"),
                "arrival": leg.get("arrival_airport"),
                "duration_minutes": _duration_minutes(leg.get("duration")),
                "airplane": leg.get("airplane"),
            } for leg in legs],
            "booking_options": flight.get("booking_options", [])[:3],
        }
        key = (item["airline"], item["departure_at"], item["price"], item["duration_minutes"])
        if key not in seen:
            seen.add(key)
            simplified.append(item)
    return {"currency": "INR", "results": simplified,
            "source": "SerpApi Google Flights", "fetched_at": fetched_at,
            "note": "Search results can change. Verify fare, baggage and final itinerary with the provider."}


class HotelSearchInput(BaseModel):
    location: str = Field(description="City or destination, e.g. Mumbai, India")
    check_in_date: str = Field(description="Check-in date YYYY-MM-DD")
    check_out_date: str = Field(description="Check-out date YYYY-MM-DD")
    adults: int = Field(default=2, ge=1, le=20)
    rooms: int = Field(default=1, ge=1, le=10)
    hotel_class: Optional[str] = Field(default=None, description="Optional star class such as 4 or 5")


@tool("search_hotels", args_schema=HotelSearchInput)
def search_hotels(location: str, check_in_date: str, check_out_date: str,
                  adults: int = 2, rooms: int = 1, hotel_class: Optional[str] = None) -> dict:
    """Search Google Hotels via SerpApi for a destination and stay dates."""
    params = {"engine": "google_hotels", "hl": "en", "gl": "in", "currency": "INR",
              "q": location, "check_in_date": check_in_date, "check_out_date": check_out_date,
              "adults": adults, "rooms": rooms, "sort_by": "8"}
    if hotel_class:
        params["hotel_class"] = hotel_class
    data = _serpapi_search(params)
    if "error" in data:
        return data
    fetched_at = datetime.now(timezone.utc).isoformat()
    simplified = []
    for hotel in (data.get("properties") or [])[:12]:
        rate = hotel.get("rate_per_night") or {}
        total = hotel.get("total_rate") or {}
        hotel_class_value = hotel.get("hotel_class")
        if isinstance(hotel_class_value, str):
            digits = "".join(ch for ch in hotel_class_value if ch.isdigit() or ch == ".")
            hotel_class_value = _number(digits) if digits else None
        simplified.append({
            "name": hotel.get("name") or "Hotel name not provided",
            "star_rating": _number(hotel_class_value),
            "guest_rating": _number(hotel.get("overall_rating")),
            "reviews": _number(hotel.get("reviews")),
            "price_per_night": _number(rate.get("lowest")),
            "total_price": _number(total.get("lowest")),
            "currency": "INR",
            "link": hotel.get("link"),
            "booking_url": hotel.get("link"),
            "location": hotel.get("description") or hotel.get("neighborhood"),
            "amenities": (hotel.get("amenities") or [])[:10],
            "source": "SerpApi Google Hotels",
            "fetched_at": fetched_at,
        })
    return {"currency": "INR", "results": simplified,
            "source": "SerpApi Google Hotels", "fetched_at": fetched_at,
            "note": "Prices and availability are indicative search results; verify taxes, cancellation rules and availability with the provider."}


TOOLS = [search_flights, search_hotels]
