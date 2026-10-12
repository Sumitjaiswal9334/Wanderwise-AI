# Wanderwise AI Travel Planner

Wanderwise AI is a Streamlit travel-planning assistant. Describe a trip in
natural language and it can search live flight and hotel options, keep context
for follow-up questions, generate a day-by-day itinerary, estimate a budget,
create a PDF report and optionally email the report after explicit approval.

The application uses Google Gemini through LangChain for the assistant and
itinerary generation, SerpApi for Google Flights and Google Hotels search,
SQLite for conversation checkpoints, ReportLab for PDF generation and SendGrid
for optional email delivery.

## Features

- Natural-language trip requests.
- Live flight search through SerpApi Google Flights.
- Live hotel search through SerpApi Google Hotels.
- Structured result cards with prices, routes, dates, durations, stops,
  ratings, amenities and provider links when returned by the provider.
- Sorting for flight price, duration and stops, and hotel prices and ratings.
- Follow-up questions within the same trip conversation.
- New-trip control for starting a fresh conversation thread.
- AI-generated day-by-day itinerary with a transparent INR budget estimate.
- PDF trip report containing the request, search results, itinerary and budget.
- TXT summary download.
- Optional PDF email delivery through SendGrid after the user approves sending.
- Responsive custom Streamlit UI with the default Streamlit navigation hidden.

## Project structure

```text
.
├── frontend.py                 # Streamlit UI and application entry point
├── app/
│   ├── agent.py                # Gemini agent and LangGraph execution
│   ├── email_service.py        # Optional SendGrid email delivery
│   ├── memory.py               # SQLite LangGraph checkpoint storage
│   ├── pdf_service.py          # PDF report generation
│   ├── schemas.py              # Validated flight, hotel and plan models
│   ├── tools.py                # SerpApi flight and hotel search tools
│   └── trip_planner.py         # Itinerary generation and budget estimates
├── requirements.txt
├── .env                       # Local secrets and configuration; do not commit
└── travel_memory.sqlite3       # Local conversation memory; ignored by Git
```

## Requirements

- Python 3.11 or 3.12
- A Google Gemini API key
- A SerpApi API key for live flight and hotel results
- A SendGrid API key and verified sender address only if email delivery is
  needed

## Windows setup

Open PowerShell in the project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks script activation, either allow local scripts for the
current user or run the environment's Python directly:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Environment variables

Create a `.env` file in the project root. Do not paste real keys into the
README, commit them, or share them publicly.

```dotenv
# Required for the Gemini travel assistant
Google_API_KEY=your_gemini_api_key
Google_MODEL=gemini-3.5-flash-lite

# Required for live flight and hotel search
SERPAPI_API_KEY=your_serpapi_api_key

# Optional: enable the email report feature
SENDGRID_API_KEY=
FROM_EMAIL=

# Optional: change the SQLite checkpoint location
TRAVEL_MEMORY_DB=travel_memory.sqlite3
```

`Google_MODEL` can be changed to another Gemini model available to your API
account. The assistant reads `Google_API_KEY` for chat responses. The
itinerary module currently checks `GOOGLE_API_KEY` as well, so set the same
Gemini key under both names if itinerary generation falls back to the
template instead of using Gemini:

```dotenv
GOOGLE_API_KEY=your_gemini_api_key
```

The email feature also requires a verified `FROM_EMAIL` sender in SendGrid.
Leave both SendGrid variables empty if email delivery is not required.

## Run the app

Start Streamlit from the project root:

```powershell
streamlit run frontend.py
```

Then open the local URL shown by Streamlit, normally
`http://localhost:8501`.

## Example requests

```text
Find flights from DEL to BOM on 2026-11-15, returning 2026-11-20,
for 1 adult. Find hotels in Mumbai too.
```

```text
Find nonstop flights from DEL to DXB on 2026-12-10 for 2 adults.
Also find 4-star hotels in Dubai from 2026-12-10 to 2026-12-14.
```

For the best results, include:

- IATA airport codes for flights, such as `DEL` and `BOM`.
- Dates in `YYYY-MM-DD` format.
- Number of adults, children or infants when relevant.
- Hotel destination, check-in/check-out dates and preferred hotel class.
- Budget or travel preferences when requesting an itinerary.

## How the application works

1. `frontend.py` loads `.env` and collects the user's trip request.
2. The Gemini agent decides whether flight or hotel search tools are needed.
3. `app/tools.py` calls SerpApi and normalizes provider responses into
   validated Pydantic models.
4. LangGraph stores the conversation using the trip's thread ID in SQLite.
5. The UI displays structured results and lets the user select flight/hotel
   options for itinerary planning.
6. The itinerary module uses Gemini when available and has a generic fallback
   template if generation fails.
7. The selected results and itinerary can be exported as a PDF or sent through
   SendGrid after approval.

## Memory and generated files

Each browser session starts with a trip thread ID. Clicking **New trip**
creates a new thread and clears the current UI selections. LangGraph
checkpoints are stored in `travel_memory.sqlite3` by default.

Change the location with `TRAVEL_MEMORY_DB` when needed:

```dotenv
TRAVEL_MEMORY_DB=C:\path\to\travel_memory.sqlite3
```

The database and generated PDFs are ignored by Git. Keep the database private
because it may contain travel conversation data.

## Important limitations

- The app searches and plans; it does not book, reserve or pay for travel.
- Prices, availability, ratings, links, baggage rules and cancellation terms
  can change. Verify all final details with the provider.
- Missing provider data is shown as unavailable rather than invented.
- Food, transport, activities and contingency amounts are rough INR planning
  estimates, not live quotes.
- AI itineraries are suggestions. Confirm opening hours, travel times and
  reservations independently.
- SendGrid accepting a message does not guarantee inbox delivery.
- The default SQLite checkpoint setup is intended for a local or single-instance
  deployment. Add authentication, user ownership and production storage before
  exposing the app to multiple users.

## Troubleshooting

### `Google API key missing`

Check that `Google_API_KEY` is present in `.env`, contains a valid Gemini key,
and restart Streamlit after changing the file. For Gemini-powered itinerary
generation, also set `GOOGLE_API_KEY` as described above.

### `SERPAPI_API_KEY is missing`

Add a valid SerpApi key to `.env` and restart the app. Check the SerpApi quota
and use valid airport codes and dates.

### Itinerary uses the fallback template

Verify the Gemini key variable names, selected model and API quota. The app
intentionally returns a generic itinerary when Gemini generation fails.

### Email is not sent

Set `SENDGRID_API_KEY` and a verified `FROM_EMAIL`. Confirm that the SendGrid
API key has mail-send permission and that the sender identity is verified.

### SQLite checkpoint dependency error

Reinstall dependencies inside the active virtual environment:

```powershell
pip install -r requirements.txt
```

## Security

- Never commit `.env`, API keys, `travel_memory.sqlite3` or generated reports.
- Rotate any API key that was accidentally exposed.
- Treat provider links and prices as untrusted external data and verify them
  before booking.
