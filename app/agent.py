"""LangGraph-powered travel assistant with persistent conversation memory."""
import ast
import json
import os
from functools import lru_cache
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.prebuilt import create_react_agent

from .memory import get_checkpointer
from .schemas import FlightOption, HotelOption
from .tools import TOOLS

SYSTEM_PROMPT = """You are a careful AI travel planning assistant.
Use search_flights for flight prices and search_hotels for hotel options when the user asks for them.
Ask a concise follow-up if a required airport code, date, destination, or stay date is missing.
Dates must be YYYY-MM-DD for tools. Never invent prices, flight availability, hotel ratings, or links.
When tool results are available, accurately summarize prices, dates, stops, hotel guest ratings and source links.
Explain that search results can change and the user must confirm details with the provider.
Use clear headings and tables where useful. Search prices are in INR unless the result states otherwise.
Do not claim to book tickets or hotels; this app only searches and summarizes options.
Do not treat an absent rating, booking URL, price, or star classification as known."""



def _make_agent():
    api_key = (
        os.getenv("Google_API_KEY", "").strip()
        or os.getenv("Google_API_KEY", "").strip()
    )
    if not api_key:
        raise RuntimeError(
            "Google API key missing. Add GOOGLE_API_KEY to .env."
        )

    model_name = os.getenv("Google_MODEL", "gemini-3.5-flash-lite")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
    )

    from langchain.agents import create_agent

    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_checkpointer(),
    )



@lru_cache(maxsize=1)
def _agent():
    return _make_agent()


def _content_to_text(content: Any) -> str:
    """Handle normal strings and multimodal/content-block message formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    if content is None:
        return ""
    return str(content)


def _parse_tool_content(content: Any):
    if isinstance(content, dict):
        return content
    text = _content_to_text(content)
    for parser in (json.loads, ast.literal_eval):
        try:
            value = parser(text)
            if isinstance(value, dict):
                return value
        except (ValueError, SyntaxError, TypeError):
            pass
    return None


def ask_agent(query: str, thread_id: str = "default") -> dict:
    """Run the existing agent and return both its summary and structured tool data."""
    if not query.strip():
        return {"answer": "Please enter a travel query.", "flights": [], "hotels": [], "errors": []}
    result = _agent().invoke(
        {"messages": [{"role": "user", "content": query.strip()}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    messages = result.get("messages", [])
    answer = _content_to_text(messages[-1].content) if messages else "No response was returned. Please try again."
    flights, hotels, errors = [], [], []
    for message in messages:
        name = getattr(message, "name", None)
        if name not in {"search_flights", "search_hotels"}:
            continue
        data = _parse_tool_content(getattr(message, "content", None))
        if not data:
            continue
        if data.get("error"):
            errors.append(str(data["error"]))
            continue
        results = data.get("results") or []
        if name == "search_flights":
            for item in results:
                if isinstance(item, dict):
                    try:
                        flights.append(FlightOption.model_validate(item).model_dump())
                    except Exception:
                        # Keep malformed provider data out of the UI rather than crashing the full search.
                        continue
        elif name == "search_hotels":
            for item in results:
                if isinstance(item, dict):
                    try:
                        hotels.append(HotelOption.model_validate(item).model_dump())
                    except Exception:
                        continue
    return {"answer": answer, "flights": flights, "hotels": hotels, "errors": errors}
