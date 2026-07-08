#!/usr/bin/env bash
# Run this in Git Bash, from inside the NutritionCustomer repo folder:
#   bash 00-data/download-datasets.sh
#
# Downloads the open datasets used to prototype the Nutrition Gap Service.
# Skips the huge ones (full Open Food Facts dump, Nutrition5k images/video) —
# see the notes at the bottom for those.

set -e
cd "$(dirname "$0")"

echo "== CoFID (UK nutrient reference values) =="
mkdir -p cofid
curl -m 30 -L -o cofid/CoFID_2021.xlsx "https://assets.publishing.service.gov.uk/media/60538b91e90e07527df82ae4/McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021..xlsx"
curl -m 30 -L -o cofid/CoFID_user_guide.pdf "https://assets.publishing.service.gov.uk/media/60538e66d3bf7f03249bac58/McCance_and_Widdowsons_Composition_of_Foods_integrated_dataset_2021.pdf"

echo "== USDA FoodData Central — Foundation Foods (small, curated subset) =="
mkdir -p usda-fdc
curl -m 30 -L -o usda-fdc/foundation_foods_csv.zip "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip"
unzip -o usda-fdc/foundation_foods_csv.zip -d usda-fdc/foundation_foods

echo "== Tesco Grocery 1.0 — annual aggregates + category lookup (~17MB) =="
mkdir -p tesco-grocery-1.0
curl -m 30 -L -o tesco-grocery-1.0/year_borough_grocery.csv "https://ndownloader.figshare.com/files/18848321"
curl -m 30 -L -o tesco-grocery-1.0/year_lsoa_grocery.csv    "https://ndownloader.figshare.com/files/18848363"
curl -m 30 -L -o tesco-grocery-1.0/year_msoa_grocery.csv    "https://ndownloader.figshare.com/files/18848378"
curl -m 30 -L -o tesco-grocery-1.0/year_osward_grocery.csv  "https://ndownloader.figshare.com/files/18848387"
curl -m 30 -L -o tesco-grocery-1.0/food_categories.csv      "https://ndownloader.figshare.com/files/15961511"

echo "== Open Food Facts — small UK sample via API (swap category/country as needed) =="
mkdir -p open-food-facts
curl -m 30 -sL "https://world.openfoodfacts.org/api/v2/search?categories_tags_en=Breakfast%20cereals&countries_tags_en=United%20Kingdom&fields=code,product_name,nutriments,nutriscore_grade&page_size=200" \
  -o open-food-facts/uk-breakfast-cereals-sample.json

echo ""
echo "Done. NOT downloaded (too large to bulk-fetch, grab manually if/when needed):"
echo "  - Tesco Grocery 1.0 monthly-level files (191MB total incl. above) — https://figshare.com/articles/dataset/7796666"
echo "  - Full Open Food Facts dump (multi-GB) — https://world.openfoodfacts.org/data ; use the API sample above for prototyping instead"
echo "  - Nutrition5k images/video (181GB) — only grab the metadata CSVs if needed:"
echo "      curl -m 30 -L -o nutrition5k/dish_metadata_cafe1.csv https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/metadata/dish_metadata_cafe1.csv"
echo "      curl -m 30 -L -o nutrition5k/dish_metadata_cafe2.csv https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/metadata/dish_metadata_cafe2.csv"
