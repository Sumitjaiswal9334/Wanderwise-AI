"""Create a printable travel-plan PDF in memory."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


def _safe(value):
    if value is None or value == "":
        return "Not provided"
    return str(value)


def _paragraph_text(value):
    return escape(_safe(value)).replace("\\n", "<br/>")


def build_trip_pdf(query: str, answer: str, flights=None, hotels=None, itinerary=None) -> bytes:
    flights, hotels = flights or [], hotels or []
    itinerary = itinerary or {}
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=16*mm, bottomMargin=16*mm, title="AI Travel Plan")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], alignment=TA_CENTER,
                              textColor=colors.HexColor("#124559"), spaceAfter=12))
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"], fontSize=8, leading=10,
                              textColor=colors.HexColor("#555555")))
    story = [Paragraph("AI Travel Plan", styles["CoverTitle"]),
             Paragraph("Generated from search results and user-provided trip details.", styles["BodyText"]),
             Spacer(1, 8),
             Paragraph("Trip request", styles["Heading2"]),
             Paragraph(_paragraph_text(query), styles["BodyText"]),
             Spacer(1, 8),
             Paragraph("AI summary", styles["Heading2"]),
             Paragraph(_safe(answer).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"), styles["BodyText"]),
             Spacer(1, 10)]
    if flights:
        story.append(Paragraph("Flight options", styles["Heading2"]))
        data = [["Airline", "Route", "Departure", "Duration", "Stops", "Price (INR)"]]
        for f in flights[:10]:
            data.append([
                _safe(f.get("airline")), f"{_safe(f.get('origin'))}–{_safe(f.get('destination'))}",
                _safe(f.get("departure_at")), _safe(f.get("duration_minutes")),
                _safe(f.get("stops")), _safe(f.get("price"))
            ])
        table = Table(data, repeatRows=1, colWidths=[29*mm, 24*mm, 32*mm, 20*mm, 15*mm, 24*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#124559")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 7),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f7f8")]),
            ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story += [table, Spacer(1, 10)]
    if hotels:
        story.append(Paragraph("Hotel options", styles["Heading2"]))
        data = [["Hotel", "Stars", "Guest rating", "Per night", "Total", "Link"]]
        for h in hotels[:10]:
            link = h.get("booking_url") or h.get("link")
            link_cell = Paragraph(f'<link href="{link}">Open</link>', styles["BodyText"]) if isinstance(link, str) and link.startswith("http") else "Not provided"
            data.append([_safe(h.get("name")), _safe(h.get("star_rating")), _safe(h.get("guest_rating")),
                         _safe(h.get("price_per_night")), _safe(h.get("total_price")), link_cell])
        table = Table(data, repeatRows=1, colWidths=[40*mm, 13*mm, 20*mm, 20*mm, 20*mm, 18*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#124559")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 7),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f7f8")]),
        ]))
        story += [table, Spacer(1, 10)]
    if itinerary:
        story.append(Paragraph("Day-by-day itinerary", styles["Heading2"]))
        for day in itinerary.get("days", []):
            story.append(Paragraph(f"<b>{_paragraph_text(day.get('date'))}</b>", styles["Heading3"]))
            for period in ("morning", "afternoon", "evening"):
                story.append(Paragraph(f"<b>{period.title()}:</b> {_paragraph_text(day.get(period))}", styles["BodyText"]))
            if day.get("notes"):
                story.append(Paragraph(f"<i>{_paragraph_text(day.get('notes'))}</i>", styles["SmallNote"]))
            story.append(Spacer(1, 5))
        budget = itinerary.get("budget", {})
        story.append(Paragraph("Estimated budget (INR)", styles["Heading2"]))
        rows = [["Category", "Amount"]]
        for key, label in [
            ("flight_cost", "Flights"), ("hotel_cost", "Hotel"),
            ("local_transport_estimate", "Local transport (estimate)"),
            ("food_estimate", "Food (estimate)"), ("activities_estimate", "Activities (estimate)"),
            ("contingency_estimate", "Contingency (estimate)"), ("estimated_total", "Estimated total"),
        ]:
            rows.append([label, _safe(budget.get(key))])
        table = Table(rows, colWidths=[95*mm, 40*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#124559")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
            ("LEFTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 5),
        ]))
        story += [table, Spacer(1, 8)]
        for note in itinerary.get("assumptions", []):
            story.append(Paragraph(f"• {_paragraph_text(note)}", styles["SmallNote"]))
    story += [Spacer(1, 12), Paragraph(
        "Important: Search prices and availability can change. This document is not a booking confirmation. "
        "Verify final fares, hotel classification, taxes, cancellation terms and opening hours with the provider.",
        styles["SmallNote"])]
    doc.build(story)
    return buffer.getvalue()
