# Nutrition Gap Service

Azure Function (Python) that compares a member's weekly nutrient intake against persona-based targets. See `/docs/nutrition-gap-logic.md` for the design rationale.

## Run locally

Needs [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) and Python 3.11+.

```
cp local.settings.json.example local.settings.json
pip install -r requirements.txt
func start
```

Then test it:

```
curl -X POST http://localhost:7071/api/nutrition_gap \
  -H "Content-Type: application/json" \
  -d '{
        "member_id": "demo-1",
        "persona": "general",
        "week_start": "2026-07-06",
        "consumption": {
          "energy_kcal": 1850, "protein_g": 45, "carbohydrate_g": 240,
          "sugars_g": 55, "fibre_g": 12, "fat_g": 68, "saturates_g": 24, "salt_g": 7.5
        }
      }'
```

Expect a JSON response flagging `fibre_g` and `sugars_g` as `under`/`over`.

## Deploy

Same pattern as the Static Web App: create a **Function App** resource in the Azure Portal (same resource group, e.g. `rg-coop-nutrition`), Runtime stack **Python 3.11**, and on the **Deployment** step connect it to this GitHub repo/branch — Azure auto-generates the workflow file and secret, same as before. Set `app_location` to `functions/nutrition-gap-service` if asked.
