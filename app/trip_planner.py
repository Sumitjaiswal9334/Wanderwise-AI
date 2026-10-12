"""Itinerary generation and transparent budget estimation."""
import json
import re
from datetime import date, timedelta
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI


def _extract_dates(text: str):
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text or "")
    valid = []
    for item in dates:
        try:
            valid.append(date.fromisoformat(item))
        except ValueError:
            pass
    return valid


def _extract_destination(text: str) -> str:
    # Prefer an explicit city after "hotels in ..." over an airport code after "to ...".
    patterns = [
        r"\bhotels?\s+in\s+([A-Za-z][A-Za-z .'-]{1,40}?)(?:\s+for\b|\s+on\b|,|\.|$)",
        r"\bin\s+([A-Za-z][A-Za-z .'-]{1,40}?)(?:\s+for\b|\s+from\b|,|\.|$)",
        r"\bto\s+([A-Za-z][A-Za-z .'-]{1,40}?)(?:\s+on\b|\s+from\b|,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in {"flights", "flight", "hotels", "hotel"}:
                return candidate
    return "Your destination"


def generate_itinerary(query: str, flight: Optional[dict] = None, hotel: Optional[dict] = None,
                       budget: Optional[float] = None, preferences: str = "") -> dict:
    """Generate a compact day-wise itinerary; prices not supplied by search are labeled estimates."""
    dates = _extract_dates(query)
    start = dates[0] if dates else None
    end = dates[1] if len(dates) > 1 else start
    if start and end and end < start:
        start, end = end, start
    number_days = min(max((end - start).days + 1, 1), 14) if start and end else 1
    destination = _extract_destination(query)
    flight_cost = flight.get("price") if flight else None
    hotel_cost = hotel.get("total_price") if hotel else None
    if hotel_cost is None and hotel and hotel.get("price_per_night") is not None and start and end:
        hotel_cost = hotel["price_per_night"] * max((end - start).days, 1)

    prompt = f"""Create a realistic but clearly tentative travel itinerary as valid JSON only.
Destination: {destination}
Dates: {start.isoformat() if start else 'not provided'} through {end.isoformat() if end else 'not provided'}
User request: {query[:2500]}
Preferences: {preferences or 'balanced sightseeing, local food and rest'}
Selected flight data (may be null): {json.dumps(flight or {}, ensure_ascii=False)[:1500]}
Selected hotel data (may be null): {json.dumps(hotel or {}, ensure_ascii=False)[:1500]}
Return JSON object with keys destination, days. days is a list of objects with date, morning, afternoon, evening, notes.
Use only plausible general suggestions, do not claim live opening hours or confirmed reservations. If dates are missing, return one sample day with date 'Date not provided'. Keep activities geographically sensible where possible. Do not include invented prices in day objects."""
    try:
        if not __import__("os").getenv("GOOGLE_API_KEY", "").strip():
            raise RuntimeError("Google_API_KEY missing")
        llm = ChatGoogleGenerativeAI(model=__import__("os").getenv("Google_MODEL", "gemini-3.5-flash-lite"))
        raw = llm.invoke(prompt).content
        if isinstance(raw, list):
            raw = "\n".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in raw)
        raw = str(raw).strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
        generated = json.loads(raw)
        days = generated.get("days", [])
        if not isinstance(days, list) or not days:
            raise ValueError("No itinerary days returned")
    except Exception:
        days = []
        if start:
            for i in range(number_days):
                d = start + timedelta(days=i)
                days.append({
                    "date": d.isoformat(),
                    "morning": "Choose one nearby major attraction; verify opening hours before leaving.",
                    "afternoon": "Explore a nearby neighbourhood or museum and allow time for lunch.",
                    "evening": "Plan a relaxed local-food or waterfront experience, depending on destination.",
                    "notes": "Fallback itinerary template; personalize attractions before travel."
                })
        else:
            days = [{
                "date": "Date not provided",
                "morning": "Select a major attraction near your accommodation.",
                "afternoon": "Explore a nearby neighbourhood and plan lunch.",
                "evening": "Choose a local dining or cultural activity.",
                "notes": "Add dates and destination details to generate a more specific plan."
            }]
    # Non-LLM calculations. Hotel total is only included when returned or computable from a nightly rate.
    nights = max((end - start).days, 0) if start and end else None
    local_transport = 1000.0 * nights if nights is not None else None
    food = 1200.0 * nights if nights is not None else None
    activities = 800.0 * nights if nights is not None else None
    known_subtotal = sum(v for v in (flight_cost, hotel_cost, local_transport, food, activities) if isinstance(v, (int, float)))
    contingency = round(known_subtotal * 0.10, 2) if known_subtotal else None
    total = round(known_subtotal + (contingency or 0), 2) if known_subtotal else None
    return {
        "destination": generated.get("destination", destination) if "generated" in locals() and isinstance(generated, dict) else destination,
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "nights": nights,
        "days": days,
        "budget": {
            "currency": "INR",
            "user_budget": budget,
            "flight_cost": flight_cost,
            "hotel_cost": hotel_cost,
            "local_transport_estimate": local_transport,
            "food_estimate": food,
            "activities_estimate": activities,
            "contingency_estimate": contingency,
            "estimated_total": total,
            "within_budget": total <= budget if total is not None and budget is not None else None,
        },
        "assumptions": [
            "Transport, food and activities are rough planning estimates, not provider quotes.",
            "Flight price is used only when returned by the selected search result.",
            "Hotel total is used only when returned or calculated from the returned nightly rate and stay length.",
            "Confirm all live prices, schedules, opening hours and availability with providers."
        ],
    }
