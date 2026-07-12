import json
import logging
import pathlib
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

TARGETS_PATH = pathlib.Path(__file__).parent / "nutrient-targets.json"
with open(TARGETS_PATH) as f:
    _CONFIG = json.load(f)

TOLERANCE_PCT = _CONFIG["tolerance_pct"]
PERSONA_TARGETS = _CONFIG["personas"]
DAYS_IN_WINDOW = 7


def compute_gaps(persona: str, weekly_consumption: dict) -> list[dict]:
    if persona not in PERSONA_TARGETS:
        raise ValueError(f"Unknown persona '{persona}'. Valid: {list(PERSONA_TARGETS)}")

    targets = PERSONA_TARGETS[persona]
    gaps = []
    for nutrient, daily_target in targets.items():
        weekly_actual = weekly_consumption.get(nutrient, 0)
        daily_avg = weekly_actual / DAYS_IN_WINDOW
        delta_pct = ((daily_avg - daily_target) / daily_target) * 100 if daily_target else 0

        if delta_pct < -TOLERANCE_PCT:
            status = "under"
        elif delta_pct > TOLERANCE_PCT:
            status = "over"
        else:
            status = "on_track"

        gaps.append({
            "nutrient": nutrient,
            "weekly_actual": round(weekly_actual, 1),
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

    if not member_id or not consumption:
        return func.HttpResponse(
            "Body must include 'member_id' and 'consumption' (nutrient totals for the week).",
            status_code=400,
        )

    try:
        gaps = compute_gaps(persona, consumption)
    except ValueError as e:
        return func.HttpResponse(str(e), status_code=400)

    result = {
        "member_id": member_id,
        "persona": persona,
        "week_start": week_start,
        "gaps": gaps,
    }

    logging.info("Computed nutrition gap for member_id=%s persona=%s", member_id, persona)
    return func.HttpResponse(json.dumps(result), mimetype="application/json")
