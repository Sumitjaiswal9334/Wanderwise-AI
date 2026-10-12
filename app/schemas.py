"""Validated canonical models for search results and trip plans."""
from typing import Any, Optional
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class FlightOption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    airline: str = "Airline not provided"
    flight_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_at: Optional[str] = None
    arrival_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    stops: Optional[int] = None
    price: Optional[float] = None
    currency: str = "INR"
    booking_url: Optional[str] = None
    source: str = "SerpApi Google Flights"
    fetched_at: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class HotelOption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    star_rating: Optional[float] = None
    guest_rating: Optional[float] = None
    reviews: Optional[int] = None
    price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "INR"
    location: Optional[str] = None
    amenities: list[str] = Field(default_factory=list)
    booking_url: Optional[str] = None
    source: str = "SerpApi Google Hotels"
    fetched_at: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ItineraryDay(BaseModel):
    date: str
    morning: str
    afternoon: str
    evening: str
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None


class TripPlan(BaseModel):
    destination: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travellers: int = 1
    currency: str = "INR"
    user_budget: Optional[float] = None
    flight_cost: Optional[float] = None
    hotel_cost: Optional[float] = None
    local_transport_estimate: Optional[float] = None
    food_estimate: Optional[float] = None
    activities_estimate: Optional[float] = None
    contingency_estimate: Optional[float] = None
    estimated_total: Optional[float] = None
    days: list[ItineraryDay] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
