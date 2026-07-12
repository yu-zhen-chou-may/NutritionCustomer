"""
Nutrition Gap Service — Azure Function (Python v4 programming model).

Input: nutrient totals for a member over some period (already aggregated
upstream from purchase history + barcode scans + meal-photo recognition —
see docs/nutrition-gap-logic.md for how those feed in), plus how many days
that total covers.

Output: per-nutrient gap vs. the member's persona target, consumed by the
Shopping List Generator, the weekly summary notification, and the front-end
Tracker page (week / month / year views).

Note: targets in nutrient-targets.json are DAILY reference values, so the
period total is averaged by `days_in_window` before comparison — comparing
a raw period sum directly against a daily target would flag almost
everything as "over" regardless of actual diet quality. `days_in_window`
defaults to 7 (weekly) for backward compatibility, but the Tracker page
passes ~30 for a monthly view and ~365 for a yearly one.
"""

import json
import logging
import pathlib

import azure.functions as func

# FUNCTION-level key auth: the Nutri Coach front end (Lovable/TanStack) calls
# this endpoint from a server function, not directly from the browser — so the
# key lives server-side as a secret env var and is never shipped to client JS.
# That makes FUNCTION auth strictly better here than ANONYMOUS (keeps random
# public callers out) with none of the "key leaks into public repo JS" risk
# a browser-side caller would have had.
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

TARGETS_PATH = pathlib.Path(__file__).parent / "nutrient-targets.json"
with open(TARGETS_PATH) as f:
    _CONFIG = json.load(f)

TOLERANCE_PCT = _CONFIG["tolerance_pct"]
PERSONA_TARGETS = _CONFIG["personas"]
DEFAULT_DAYS_IN_WINDOW = 7
MIN_DAYS_IN_WINDOW = 1
MAX_DAYS_IN_WINDOW = 366


def compute_gaps(persona: str, period_consumption: dict, days_in_window: int = DEFAULT_DAYS_IN_WINDOW) -> list[dict]:
    if persona not in PERSONA_TARGETS:
        raise ValueError(f"Unknown persona '{persona}'. Valid: {list(PERSONA_TARGETS)}")

    targets = PERSONA_TARGETS[persona]
    gaps = []
    for nutrient, daily_target in targets.items():
        period_actual = period_consumption.get(nutrient, 0)
        daily_avg = period_actual / days_in_window
        delta_pct = ((daily_avg - daily_target) / daily_target) * 100 if daily_target else 0

        if delta_pct < -TOLERANCE_PCT:
            status = "under"
        elif delta_pct > TOLERANCE_PCT:
            status = "over"
        else:
            status = "on_track"

        gaps.append({
            "nutrient": nutrient,
            "weekly_actual": round(period_actual, 1),  # field name kept for backward compatibility
            "daily_avg": round(daily_avg, 1),
            "daily_target": daily_target,
            "status": status,
            "delta_pct": round(delta_pct, 1),
        })
    return gaps


@app.route(route="nutrition_gap", methods=["POST"])
def nutrition_gap(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Request body must be JSON.", status_code=400)

    member_id = body.get("member_id")
    persona = body.get("persona", "general")
    week_start = body.get("week_start")
    consumption = body.get("consumption", {})
    days_in_window = body.get("days_in_window", DEFAULT_DAYS_IN_WINDOW)

    if not member_id or not consumption:
        return func.HttpResponse(
            "Body must include 'member_id' and 'consumption' (nutrient totals for the period).",
            status_code=400,
        )

    try:
        days_in_window = int(days_in_window)
    except (TypeError, ValueError):
        return func.HttpResponse("'days_in_window' must be a number.", status_code=400)

    if not (MIN_DAYS_IN_WINDOW <= days_in_window <= MAX_DAYS_IN_WINDOW):
        return func.HttpResponse(
            f"'days_in_window' must be between {MIN_DAYS_IN_WINDOW} and {MAX_DAYS_IN_WINDOW}.",
            status_code=400,
        )

    try:
        gaps = compute_gaps(persona, consumption, days_in_window)
    except ValueError as e:
        return func.HttpResponse(str(e), status_code=400)

    result = {
        "member_id": member_id,
        "persona": persona,
        "week_start": week_start,
        "days_in_window": days_in_window,
        "gaps": gaps,
    }

    logging.info(
        "Computed nutrition gap for member_id=%s persona=%s days_in_window=%s",
        member_id, persona, days_in_window,
    )
    return func.HttpResponse(json.dumps(result), mimetype="application/json")
