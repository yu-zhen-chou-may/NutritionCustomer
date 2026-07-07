# Nutrition Gap Service — logic design

## What counts as a "gap"

For each tracked nutrient, compare the member's rolling 7-day intake (summed from purchase history + barcode scans + meal photos) against a **target range** for their persona. The gap is the difference, expressed as a status:

- **Under** — below target range
- **On track** — within range
- **Over** — above target range

A tolerance band (±10% of target, configurable) avoids flagging trivial deviations.

## Nutrients tracked (v1)

Matches what's already on a UK nutrition label (and what CoFID/Open Food Facts/USDA all report), so lookups are simple:

`energy_kcal, protein_g, carbohydrate_g, sugars_g, fibre_g, fat_g, saturates_g, salt_g`

## Targets are data, not code

Targets live in `functions/nutrition-gap-service/nutrient-targets.json`, one row per persona, **not hardcoded in the service logic**. This matters because of the earlier point about shifting dietary guidance (e.g. lower-carb consensus for diabetes management evolving through 2023–2025) — updating a target means editing a number in a config file, not redeploying logic. Personas for v1:

- `general` — Eatwell Guide-based baseline
- `chronic_diabetes` — lower carbohydrate ceiling, informed by current NICE/Diabetes UK guidance
- `fitness` — higher protein target
- `children` — lower energy/salt ceilings, age-adjusted
- `elderly` — adjusted energy, higher calcium/fibre emphasis

(Numbers in the v1 config are placeholders for prototyping — before this goes near real members, a nutritionist/dietitian should sign off on the actual target values per persona, especially `chronic_diabetes`.)

## Persona source

Persona is set once at login/onboarding (per the revised architecture) and passed into every request — this service does not infer or classify it.

## Aggregation window

Rolling 7 days, recalculated whenever new purchase/scan/photo data lands. "Weekly nutrient summary" and "weekend shopping-list notification" both read from the same gap computation — summary reports the numbers, the shopping list generator uses the "under" nutrients to bias suggestions.

## Output contract

```json
{
  "member_id": "string",
  "persona": "general | fitness | chronic_diabetes | children | elderly",
  "week_start": "YYYY-MM-DD",
  "gaps": [
    {
      "nutrient": "fibre_g",
      "actual": 12.4,
      "target": 24,
      "status": "under",
      "delta_pct": -48.3
    }
  ]
}
```

This is what the Shopping List Generator and Azure OpenAI explanation step consume downstream.

## What this does NOT do (scope boundary)

No medical claims, no diagnosis, no medication interaction. Persona is a member's self-declared preference, not a clinical assessment — copy shown to members should reflect that (e.g. "you said you're managing diabetes" not "you have diabetes").
