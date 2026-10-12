"""Premium Streamlit UI for the AI Travel Agent.

Keep this file alongside the existing app/ package. The agent, search tools,
PDF generation, itinerary planner and email service remain in the existing backend.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from html import escape

import streamlit as st
from dotenv import load_dotenv

from app.agent import ask_agent
from app.email_service import send_travel_email
from app.pdf_service import build_trip_pdf
from app.trip_planner import generate_itinerary

load_dotenv()
st.set_page_config(page_title="Wanderwise AI · Travel Planner", page_icon="✈️", layout="wide", initial_sidebar_state="collapsed")

# ------------------------------- Styling -----------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root { --ink:#17213a; --muted:#68738a; --blue:#4f46e5; --blue2:#635bff; --line:#e7eaf2; --paper:#f7f8fc; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background:var(--paper); color:var(--ink); }
    .block-container { max-width:1400px; padding-top:1.2rem; padding-bottom:3rem; }
    h1,h2,h3,h4 { font-family:'Manrope',sans-serif !important; color:var(--ink) !important; letter-spacing:-.035em; }
    h1 { font-size:2.1rem !important; font-weight:800 !important; }
    h2 { font-size:1.45rem !important; font-weight:800 !important; }
    h3 { font-size:1.12rem !important; font-weight:750 !important; }
    p, label, .stCaption { color:var(--muted); }
    [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu { display:none; }
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line) !important; }
    div[data-testid="stForm"] { background:white; border:1px solid var(--line); border-radius:20px; padding:1.2rem 1.25rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:white; border-radius:18px; }
    .brand-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.2rem 0 1.2rem; border-bottom:1px solid var(--line); margin-bottom:1.6rem; }
    .brand { display:flex; align-items:center; gap:.7rem; color:var(--ink); font-family:'Manrope',sans-serif; font-weight:800; font-size:1.15rem; }
    .brand-mark { width:40px; height:40px; border-radius:14px; display:grid; place-items:center; color:white; font-size:1.25rem; background:linear-gradient(135deg,#4f46e5,#818cf8); box-shadow:0 7px 18px #4f46e52b; }
    .brand-sub { color:var(--muted); font-size:.82rem; font-weight:500; }
    .top-pill { border:1px solid #e2e5f0; border-radius:999px; padding:.5rem .85rem; color:#4b556b; background:white; font-size:.82rem; white-space:nowrap; }
    .hero { padding:1.7rem 0 1.2rem; }
    .eyebrow { color:var(--blue); font-size:.76rem; letter-spacing:.12em; font-weight:800; text-transform:uppercase; margin-bottom:.65rem; }
    .hero-title { font-family:'Manrope',sans-serif; font-size:clamp(2rem,3.7vw,3.35rem); line-height:1.13; font-weight:800; letter-spacing:-.055em; color:var(--ink); max-width:800px; }
    .hero-title span { color:var(--blue); }
    .hero-copy { max-width:690px; font-size:1.02rem; line-height:1.7; margin-top:.8rem; color:var(--muted); }
    .section-kicker { color:var(--muted); font-size:.76rem; text-transform:uppercase; letter-spacing:.1em; font-weight:800; margin-bottom:.45rem; }
    .section-intro { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin:1.4rem 0 .8rem; }
    .mini-note { font-size:.78rem; color:var(--muted); }
    .feature-strip { display:flex; gap:.55rem; flex-wrap:wrap; margin:.5rem 0 1.2rem; }
    .feature-chip { background:#eef0ff; color:#4841c9; border:1px solid #e1e4ff; border-radius:999px; padding:.42rem .72rem; font-size:.78rem; font-weight:650; }
    .flight-card { border:1px solid var(--line); background:white; border-radius:18px; padding:1.1rem 1.2rem; margin:.65rem 0; box-shadow:0 3px 12px #17213a05; }
    .flight-top { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; }
    .airline-name { font-size:1rem; font-weight:800; color:var(--ink); }
    .muted-small { color:var(--muted); font-size:.8rem; margin-top:.18rem; }
    .price { font-family:'Manrope',sans-serif; color:var(--ink); font-size:1.45rem; font-weight:800; white-space:nowrap; }
    .route-line { display:flex; align-items:center; gap:.75rem; margin:1rem 0 .6rem; }
    .route-point { font-size:1.1rem; font-weight:800; color:var(--ink); }
    .route-time { font-size:.8rem; color:var(--muted); }
    .route-middle { flex:1; text-align:center; color:var(--muted); font-size:.75rem; }
    .route-rule { border-top:1px solid #cbd1e0; margin:.28rem 0; position:relative; }
    .route-rule:after { content:'✈'; position:absolute; left:50%; top:-.7rem; transform:translateX(-50%); padding:0 .3rem; background:white; color:var(--blue); }
    .hotel-card { border:1px solid var(--line); background:white; border-radius:18px; padding:1.1rem; margin:.65rem 0; }
    .hotel-name { color:var(--ink); font-size:1rem; font-weight:800; }
    .hotel-tag { display:inline-block; background:#f0fdf4; color:#16804a; border-radius:7px; padding:.25rem .45rem; font-size:.72rem; font-weight:750; margin:.35rem .25rem .1rem 0; }
    .assistant-panel { background:linear-gradient(145deg,#22264f,#373b79); border-radius:20px; padding:1.25rem; color:white; }
    .assistant-panel h3 { color:white !important; margin:.2rem 0 .45rem; }
    .assistant-panel p { color:#d7dcff; font-size:.88rem; line-height:1.6; }
    .assistant-icon { display:grid; place-items:center; width:42px; height:42px; border-radius:14px; background:#ffffff1c; font-size:1.35rem; margin-bottom:.8rem; }
    .stat-card { background:white; border:1px solid var(--line); border-radius:15px; padding:.85rem 1rem; min-height:80px; }
    .stat-label { color:var(--muted); font-size:.77rem; }
    .stat-value { color:var(--ink); font-size:1.2rem; font-family:'Manrope',sans-serif; font-weight:800; margin-top:.2rem; }
    .footer-note { border-top:1px solid var(--line); margin-top:2rem; padding-top:1rem; color:var(--muted); font-size:.78rem; }
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius:11px;
        font-weight:750;
        min-height:2.7rem;
        color:var(--blue) !important;
        background:#ffffff !important;
        border:1px solid #cfd3ff !important;
        transition:background .2s ease, border-color .2s ease, color .2s ease, box-shadow .2s ease;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
        color:#3730a3 !important;
        background:#f3f4ff !important;
        border-color:#a5b4fc !important;
        box-shadow:0 4px 12px #4f46e51f;
    }
    button[kind="primary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFormSubmitButton"][kind="primary"] {
        color:#ffffff !important;
        background:linear-gradient(135deg,#4f46e5,#635bff) !important;
        border:1px solid #4f46e5 !important;
        box-shadow:0 6px 14px #4f46e533;
        opacity:1 !important;
    }
    button[kind="primary"] *,
    [data-testid="stBaseButton-primary"] *,
    [data-testid="stFormSubmitButton"] button * {
        color:#ffffff !important;
        opacity:1 !important;
    }
    button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stFormSubmitButton"][kind="primary"]:hover {
        color:#ffffff !important;
        background:linear-gradient(135deg,#4338ca,#4f46e5) !important;
        border-color:#4338ca !important;
        box-shadow:0 8px 18px #4f46e54d;
    }
    .stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible, .stDownloadButton > button:focus-visible {
        outline:3px solid #c7d2fe !important;
        outline-offset:2px;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, [data-baseweb="select"] > div { border-radius:10px !important; }
    [data-testid="stMetric"] { background:#f8f9ff; border:1px solid #eceeff; border-radius:13px; padding:.7rem .8rem; }
    [data-testid="stMetricLabel"] { color:var(--muted) !important; }
    [data-testid="stMetricValue"] { color:var(--ink) !important; font-family:'Manrope',sans-serif; }
    @media (max-width: 800px) { .block-container {padding-left:1rem;padding-right:1rem;} .hero-title {font-size:2.1rem;} .top-pill {display:none;} }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------ Session state ------------------------------
for key, value in {
    "travel_thread_id": str(uuid.uuid4()),
    "travel_result": None,
    "trip_itinerary": None,
    "trip_query": "",
    "pdf_bytes": None,
    "travel_query": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --------------------------------- Header -----------------------------------
head_left, head_right = st.columns([4, .9], vertical_alignment="center")
with head_left:
    st.markdown(
        '<div class="brand"><div class="brand-mark">✈</div><div>Wanderwise AI<div class="brand-sub">Travel planning, made personal</div></div></div>',
        unsafe_allow_html=True,
    )
with head_right:
    if st.button("＋  New trip", type="primary", use_container_width=True):
        st.session_state.travel_thread_id = str(uuid.uuid4())
        st.session_state.travel_result = None
        st.session_state.trip_itinerary = None
        st.session_state.trip_query = ""
        st.session_state.travel_query = ""
        st.session_state.pdf_bytes = None
        for key in ("sort_flights", "sort_hotels", "selected_flight", "selected_hotel"):
            st.session_state.pop(key, None)
        st.rerun()

st.markdown(
    '<div class="hero"><div class="eyebrow">✦ Your AI-powered travel companion</div>'
    '<div class="hero-title">Your next journey,<br><span>thoughtfully planned.</span></div>'
    '<div class="hero-copy">Compare real search results, discover stays, and turn your travel ideas into a day-by-day itinerary — all in one place.</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="feature-strip"><span class="feature-chip">✈ Flight comparison</span><span class="feature-chip">⌂ Hotel discovery</span><span class="feature-chip">✦ AI itinerary</span><span class="feature-chip">⇩ PDF trip report</span></div>',
    unsafe_allow_html=True,
)

# ------------------------------ Search form --------------------------------
st.markdown('<div class="section-kicker">Start exploring</div>', unsafe_allow_html=True)
with st.form("travel_form", border=True):
    query = st.text_area(
        "Tell us about your trip",
        value=st.session_state.get("travel_query", ""),
        height=105,
        placeholder="e.g. Find flights from DEL to BOM on 2026-11-15, returning 2026-11-20, for 1 adult. Find hotels in Mumbai too.",
        label_visibility="visible",
    )
    form_col1, form_col2 = st.columns([3, 1], vertical_alignment="center")
    with form_col1:
        st.caption("Tip: include airport codes, dates, number of travellers and hotel preferences for better results.")
    with form_col2:
        submitted = st.form_submit_button("Search travel options  →", type="primary", use_container_width=True)

if submitted:
    if not query.strip():
        st.warning("Please describe your trip before searching.")
    else:
        with st.spinner("Finding travel options and preparing your trip..."):
            try:
                st.session_state.travel_query = query.strip()
                st.session_state.trip_query = query.strip()
                st.session_state.travel_result = ask_agent(query.strip(), st.session_state.travel_thread_id)
                st.session_state.trip_itinerary = None
                st.session_state.pdf_bytes = None
            except Exception as exc:
                st.error(f"Could not complete the search: {type(exc).__name__}: {exc}")

result = st.session_state.travel_result
selected_flight = None
selected_hotel = None
flights = result.get("flights", []) if result else []
hotels = result.get("hotels", []) if result else []

# ---------------------------- Search results --------------------------------
if result:
    st.markdown('<div class="section-intro"><div><div class="section-kicker">Your search</div><h2 style="margin:0">Travel options</h2></div><div class="mini-note">Live search data · Verify before booking</div></div>', unsafe_allow_html=True)
    if result.get("answer"):
        with st.expander("Read AI travel summary", expanded=True):
            st.markdown(result.get("answer", "No summary returned."))
    for error in result.get("errors", []):
        st.warning(error)

    left_results, right_assistant = st.columns([1.85, 1], gap="large")
    with left_results:
        tab_flights, tab_hotels, tab_plan = st.tabs([f"✈ Flights ({len(flights)})", f"⌂ Hotels ({len(hotels)})", "✦ Itinerary & budget"])

        with tab_flights:
            if flights:
                sort_flights = st.selectbox("Sort by", ["Recommended order", "Lowest price", "Shortest duration", "Fewest stops"], key="sort_flights")
                display_flights = list(flights)
                if sort_flights == "Lowest price":
                    display_flights.sort(key=lambda x: x.get("price") if isinstance(x.get("price"), (int, float)) else float("inf"))
                elif sort_flights == "Shortest duration":
                    display_flights.sort(key=lambda x: x.get("duration_minutes") if isinstance(x.get("duration_minutes"), (int, float)) else float("inf"))
                elif sort_flights == "Fewest stops":
                    display_flights.sort(key=lambda x: x.get("stops") if isinstance(x.get("stops"), (int, float)) else float("inf"))

                flight_labels = []
                for idx, flight in enumerate(display_flights):
                    airline = escape(str(flight.get("airline") or "Airline not provided"))
                    origin = escape(str(flight.get("origin") or "—"))
                    destination = escape(str(flight.get("destination") or "—"))
                    price = f"₹{flight['price']:,.0f}" if isinstance(flight.get("price"), (int, float)) else "Price unavailable"
                    duration = flight.get("duration_minutes")
                    duration_text = f"{duration} min" if isinstance(duration, (int, float)) else "Duration unavailable"
                    stops = flight.get("stops")
                    stops_text = "Non-stop" if stops == 0 else (f"{stops} stop(s)" if isinstance(stops, (int, float)) else "Stops unavailable")
                    dep = escape(str(flight.get("departure_at") or "Departure not provided"))
                    arr = escape(str(flight.get("arrival_at") or "Arrival not provided"))
                    st.markdown(
                        f'<div class="flight-card"><div class="flight-top"><div><div class="airline-name">{airline}</div>'
                        f'<div class="muted-small">{origin} → {destination} &nbsp;·&nbsp; {escape(str(flight.get("flight_number") or "Flight details unavailable"))}</div></div>'
                        f'<div style="text-align:right"><div class="price">{price}</div><div class="muted-small">per traveller, if supplied</div></div></div>'
                        f'<div class="route-line"><div><div class="route-point">{dep}</div><div class="route-time">{origin}</div></div>'
                        f'<div class="route-middle">{escape(duration_text)}<div class="route-rule"></div>{escape(stops_text)}</div>'
                        f'<div style="text-align:right"><div class="route-point">{arr}</div><div class="route-time">{destination}</div></div></div>'
                        f'<div class="muted-small">Source: {escape(str(flight.get("source") or "Search result"))} · Retrieved: {escape(str(flight.get("fetched_at") or "time unavailable"))}</div></div>',
                        unsafe_allow_html=True,
                    )
                    url = flight.get("booking_url")
                    if isinstance(url, str) and url.startswith("https://"):
                        st.markdown(f"[View provider / booking option]({url})")
                    flight_labels.append(f"{idx + 1}. {flight.get('airline') or 'Airline'} | {origin} → {destination} | {price} | {stops_text}")
                selected_flight_label = st.selectbox("Choose a flight for your itinerary and budget", ["None selected"] + flight_labels, key="selected_flight")
                if selected_flight_label != "None selected":
                    selected_flight = display_flights[flight_labels.index(selected_flight_label)]
            else:
                st.info("No flight cards were returned. Try including origin/destination airport codes and exact travel dates in your query.")

        with tab_hotels:
            if hotels:
                sort_hotels = st.selectbox("Sort by", ["Recommended order", "Lowest total price", "Lowest nightly price", "Highest guest rating"], key="sort_hotels")
                display_hotels = list(hotels)
                if sort_hotels == "Lowest total price":
                    display_hotels.sort(key=lambda x: x.get("total_price") if isinstance(x.get("total_price"), (int, float)) else float("inf"))
                elif sort_hotels == "Lowest nightly price":
                    display_hotels.sort(key=lambda x: x.get("price_per_night") if isinstance(x.get("price_per_night"), (int, float)) else float("inf"))
                elif sort_hotels == "Highest guest rating":
                    display_hotels.sort(key=lambda x: x.get("guest_rating") if isinstance(x.get("guest_rating"), (int, float)) else float("-inf"), reverse=True)

                hotel_labels = []
                for idx, hotel in enumerate(display_hotels):
                    name = escape(str(hotel.get("name") or "Hotel name not provided"))
                    location = escape(str(hotel.get("location") or "Location not provided"))
                    nightly = f"₹{hotel['price_per_night']:,.0f}/night" if isinstance(hotel.get("price_per_night"), (int, float)) else "Nightly price unavailable"
                    total = f"₹{hotel['total_price']:,.0f} total" if isinstance(hotel.get("total_price"), (int, float)) else "Total price unavailable"
                    rating = hotel.get("guest_rating")
                    rating_text = str(rating) if rating is not None else "Not rated"
                    amenities = hotel.get("amenities") or []
                    amenities_html = "".join(f'<span class="hotel-tag">{escape(str(a))}</span>' for a in amenities[:5])
                    stars = hotel.get("star_rating")
                    st.markdown(
                        f'<div class="hotel-card"><div class="flight-top"><div><div class="hotel-name">⌂ {name}</div><div class="muted-small">{location}</div>'
                        f'<div style="margin-top:.5rem">{amenities_html}</div></div><div style="text-align:right"><div class="price">{nightly}</div>'
                        f'<div class="muted-small">{total}</div></div></div><div class="muted-small" style="margin-top:.7rem">★ Guest rating: {escape(rating_text)} · Reviews: {escape(str(hotel.get("reviews") or "N/A"))} · Official stars: {escape(str(stars if stars is not None else "Not provided"))}</div>'
                        f'<div class="muted-small">Source: {escape(str(hotel.get("source") or "Search result"))} · Retrieved: {escape(str(hotel.get("fetched_at") or "time unavailable"))}</div></div>',
                        unsafe_allow_html=True,
                    )
                    url = hotel.get("booking_url") or hotel.get("link")
                    if isinstance(url, str) and url.startswith("https://"):
                        st.markdown(f"[View hotel / provider details]({url})")
                    hotel_labels.append(f"{idx + 1}. {hotel.get('name') or 'Hotel'} | {total} | {nightly}")
                selected_hotel_label = st.selectbox("Choose a hotel for your itinerary and budget", ["None selected"] + hotel_labels, key="selected_hotel")
                if selected_hotel_label != "None selected":
                    selected_hotel = display_hotels[hotel_labels.index(selected_hotel_label)]
            else:
                st.info("No hotel cards were returned. Add a destination, check-in/check-out dates and guest count to your query.")

        with tab_plan:
            st.markdown("### Build your day-by-day plan")
            with st.form("itinerary_form"):
                budget = st.number_input("Total trip budget (INR; optional)", min_value=0, value=0, step=1000, help="Set to 0 if you do not want a budget limit.")
                preferences = st.text_input("Interests and travel pace", placeholder="e.g. local food, museums, nature; relaxed pace")
                itinerary_submit = st.form_submit_button("Generate itinerary + budget", type="primary", use_container_width=True)
            if itinerary_submit:
                with st.spinner("Creating your day-by-day plan..."):
                    try:
                        st.session_state.trip_itinerary = generate_itinerary(
                            st.session_state.trip_query,
                            flight=selected_flight,
                            hotel=selected_hotel,
                            budget=float(budget) if budget > 0 else None,
                            preferences=preferences,
                        )
                        st.session_state.pdf_bytes = None
                    except Exception as exc:
                        st.error(f"Could not generate itinerary: {type(exc).__name__}: {exc}")

            itinerary = st.session_state.trip_itinerary
            if itinerary:
                st.markdown(f"### {itinerary.get('destination', 'Your trip')} itinerary")
                for day in itinerary.get("days", []):
                    with st.container(border=True):
                        st.markdown(f"**{day.get('date', 'Date not provided')}**")
                        a, b, c = st.columns(3)
                        a.markdown(f"**☀ Morning**\n\n{day.get('morning', 'Not provided')}")
                        b.markdown(f"**◷ Afternoon**\n\n{day.get('afternoon', 'Not provided')}")
                        c.markdown(f"**☾ Evening**\n\n{day.get('evening', 'Not provided')}")
                        if day.get("notes"):
                            st.caption(day["notes"])
                budget_data = itinerary.get("budget", {})
                st.markdown("### Estimated trip budget")
                budget_rows = [
                    ("Flights", budget_data.get("flight_cost")), ("Hotel", budget_data.get("hotel_cost")),
                    ("Local transport · estimate", budget_data.get("local_transport_estimate")),
                    ("Food · estimate", budget_data.get("food_estimate")), ("Activities · estimate", budget_data.get("activities_estimate")),
                    ("Contingency · estimate", budget_data.get("contingency_estimate")), ("Estimated total", budget_data.get("estimated_total")),
                ]
                cols = st.columns(3)
                for i, (label, amount) in enumerate(budget_rows):
                    shown = f"₹{amount:,.0f}" if isinstance(amount, (int, float)) else "Unavailable"
                    cols[i % 3].metric(label, shown)
                if budget_data.get("user_budget") is not None and budget_data.get("within_budget") is not None:
                    if budget_data["within_budget"]:
                        st.success(f"Estimated total is within your ₹{budget_data['user_budget']:,.0f} budget.")
                    else:
                        st.warning(f"Estimated total exceeds your ₹{budget_data['user_budget']:,.0f} budget. Consider changing selected options.")
                for assumption in itinerary.get("assumptions", []):
                    st.caption("• " + str(assumption))

    with right_assistant:
        st.markdown(
            '<div class="assistant-panel"><div class="assistant-icon">✦</div><h3>Your Trip Copilot</h3>'
            '<p>Tell the assistant what matters to you — budget, food, sightseeing, pace or a destination change. It can search options and help shape your plan.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Try asking**")
        for prompt in [
            "Find the cheapest flight options",
            "Suggest family-friendly hotels",
            "Plan a relaxed 3-day itinerary",
            "Keep the trip within ₹25,000",
        ]:
            if st.button(prompt, key="suggest_" + str(abs(hash(prompt))), use_container_width=True):
                st.session_state.travel_query = prompt
                st.rerun()
        st.markdown("---")
        st.markdown("**Trip snapshot**")
        st.markdown(f'<div class="stat-card"><div class="stat-label">Flight options found</div><div class="stat-value">{len(flights)}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card" style="margin-top:.55rem"><div class="stat-label">Hotel options found</div><div class="stat-value">{len(hotels)}</div></div>', unsafe_allow_html=True)
        st.markdown(" ")
        st.caption("Prices and availability can change. Confirm all details with the provider before booking.")

    # ------------------------ Export and email tools -------------------------
    st.markdown("---")
    st.markdown('<div class="section-kicker">Take your plan with you</div><h2 style="margin-top:0">Export & share</h2>', unsafe_allow_html=True)
    export1, export2, export3 = st.columns([1, 1, 1.3])
    with export1:
        if st.button("Prepare PDF report", type="primary", use_container_width=True):
            try:
                st.session_state.pdf_bytes = build_trip_pdf(
                    st.session_state.trip_query, result.get("answer", ""), flights, hotels,
                    st.session_state.trip_itinerary,
                )
                st.success("PDF report is ready.")
            except Exception as exc:
                st.error(f"Could not prepare PDF: {type(exc).__name__}: {exc}")
    with export2:
        st.download_button("Download raw summary (.txt)", result.get("answer", ""), file_name="travel_results.txt", mime="text/plain", use_container_width=True)
    with export3:
        if st.session_state.pdf_bytes:
            st.download_button("⬇ Download trip report (.pdf)", data=st.session_state.pdf_bytes, file_name="wanderwise_trip_plan.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.caption("Prepare the PDF report first to enable the download and email options.")

    if st.session_state.pdf_bytes:
        with st.expander("Email trip report (approval required)", expanded=False):
            st.info("Review the recipient and report before sending. Email sending does not book flights or hotels.")
            with st.form("email_form"):
                recipient = st.text_input("Recipient email address")
                subject = st.text_input("Email subject", value="My AI Travel Plan")
                body = st.text_area("Email message", value="Hi,\n\nPlease find my AI-generated travel plan attached. Prices and availability should be verified with providers.\n")
                approved = st.checkbox("I approve sending this email with the attached travel report.")
                send = st.form_submit_button("Send approved email", type="primary")
            if send:
                if not approved:
                    st.warning("Please approve the email before sending.")
                elif not recipient.strip():
                    st.warning("Please enter a recipient email address.")
                else:
                    with st.spinner("Sending email..."):
                        try:
                            status = send_travel_email(body, recipient.strip(), subject, st.session_state.pdf_bytes)
                            if str(status).startswith("Email accepted"):
                                st.success(status)
                            else:
                                st.error(status)
                        except Exception as exc:
                            st.error(f"Could not send email: {type(exc).__name__}: {exc}")

# with st.expander("Setup & troubleshooting"):
#     st.markdown(
#         """- Add the API keys required by your current backend to `.env` before searching.
# - Email is optional and requires a configured SendGrid API key and verified sender.
# - Search results, fares and availability can change; confirm details with the provider.
# - This app searches and plans only; it does not book, charge or reserve anything.
# - Conversation checkpoints are stored in `travel_memory.sqlite3` by default. Keep that file private.
# - If deploying, use persistent storage if you need SQLite conversation memory to survive restarts."""
#     )

st.markdown('<div class="footer-note">Made for curious travellers · Wanderwise AI · Search results are informational and are not a booking confirmation.</div>', unsafe_allow_html=True)
