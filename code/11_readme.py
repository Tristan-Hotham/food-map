"""README.md and LICENSE, with every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
n, rg, b, mm, sp, t = R["national"], R["regional"], R["breakfast"], R["main_meal"], R["spain"], R["times"]
fc = rg["focus"]
readme = f"""# What does the world eat?

An atlas of national dishes, breakfasts, regional dishes and the main meal of the day, built from English Wikipedia and Wikidata: {n['n_countries']} countries and territories with suggested national dishes, breakfast styles for {b['n_countries']} countries, {rg['n_dishes']:,} dishes placed in {rg['n_regions']} regions of {rg['n_countries']} countries, and the main meal for {mm['n_coded']} countries.

Interactive page: https://maps.tristanhotham.com/food-map/
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- The first-listed national dish is most often meat or a grill ({n['family_first'][0]['n']} of {n['n_countries']}, {round(n['family_first'][0]['share'] * 100)}%), then a starchy staple such as a maize or cassava porridge ({n['family_first'][1]['n']}), then a soup, stew or curry ({n['family_first'][2]['n']}) and a rice dish ({n['family_first'][3]['n']}). {n['max_country']} has the most suggestions ({n['max_n']}); the median country has {int(n['median_per_country'])}.
- Breakfast: of {b['europe']['n']} European countries described, {b['europe']['bread']} start with bread and savoury toppings and {b['europe']['sweet']} ({', '.join(b['europe']['sweet_names'])}) with coffee and something sweet. Britain and Ireland share a style with North America, Australia and New Zealand.
- {rg['n_dishes']:,} of {rg['n_wikidata_food']:,} Wikidata foods with a country ({round(rg['share_placed'] * 100)}%) can be placed in a region. Japan ({fc['JPN']['dishes']}), Indonesia ({fc['IDN']['dishes']}) and Italy ({fc['ITA']['dishes']}) hold {round(rg['share_top3'] * 100)}% of them; Mexico has {fc['MEX']['dishes']}, Turkey {fc['TUR']['dishes']}, Ireland {fc['IRL']['dishes']}.
- Spain: {fc['ESP']['dishes']} dishes in {fc['ESP']['regions_with']} of {fc['ESP']['regions']} regions, led by {rg['spain'][0]['name']} ({rg['spain'][0]['n']}); fabada in {rg['examples']['Fabada asturiana']}, paella in the {rg['examples']['paella']}.
- No Wikidata food is tagged with lunch or dinner as its course ({mm['wd_lunch_items']} and {mm['wd_dinner_items']}), against {mm['wd_main_items']} main courses: separate lunch and dinner maps are not supported, so the atlas maps which meal is the main meal instead. Midday in {mm['counts']['midday']} of {mm['n_coded']} coded countries, evening in {mm['counts']['evening']}.
- Spain's lunch (middle of the window, {sp['lunch_clock']} on the clock) is at {sp['lunch_sun']} by the sun; its supper ({sp['dinner_clock']}) at {sp['dinner_sun']}, {sp['gap_sun_min']} minutes after Britain's evening meal by the sun ({sp['gap_clock_min']} minutes on the clock). {t['n_lunch_sun_before_1']} of {t['n_lunch']} countries with stated lunch times eat before 1 pm sun time.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; page data embedded, `data/regions.json` loaded on use). |
| `header.png` | Social card, 1200 x 630. |
| `data/national_dishes.csv` | Every dish in Wikipedia's 'National dish' list by country (and part of country), in order, with Wikipedia title, Wikidata item, family and source of the family, and the free photo used with its author and licence. |
| `data/breakfast.csv` | Breakfast style and a short summary of foods for each country described in 'Breakfast by country', with the section used. |
| `data/main_meal.csv` | Main meal (midday, evening, shifting, morning), stated lunch and dinner times, the same times by the sun, the country's lead of clock over sun, the note and the source article. |
| `data/dishes.csv` | All {rg['n_wikidata_food']:,} Wikidata foods kept, with country, family, region (if any), the evidence used and the mapped place. |
| `data/regional_dishes.csv`, `data/region_counts.csv` | The {rg['n_dishes']:,} placed dishes, and dishes per region. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/world.json`, `data/regions.json`, `data/cities.json`, `data/countries_geo.json` | Page data; simplified Natural Earth countries and states or provinces; GeoNames city labels. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- National dishes: the 'By country' section of English Wikipedia's 'National dish', parsed line by line; links resolved to Wikidata through the Wikipedia API. Families from Wikidata's subclass tree, with a precedence order; where the tree does not reach, from the dish's description.
- Breakfast: one of eight styles per country, summarising each section of 'Breakfast by country'.
- Regional dishes: Wikidata foods (dishes, breads, cheeses, sausages, pastries, desserts), minus brands, products, fictional foods and museum objects. A region comes from, in order: a Wikidata location property; a sub-national country of origin; a regional cuisine; an English Wikipedia regional cuisine category (same country, at most two regions); a place named in the English name (region names, GeoNames cities of 30,000 or more, OS Open Names towns and counties, a short table of adjectives). Broad areas never place a dish. Point in polygon against Natural Earth admin-1 units, merged into regions for Spain, Italy, France, Portugal and England.
- Main meal: coded only where a sentence in the cuisine, 'Lunch' or 'Dinner' articles says which meal is the main one or gives times. Sun time subtracts each country's population-weighted mean lead of clock over sun from the clock-vs-sun study.
- Caveats: this maps what the open record claims, not what people eat; coverage is very uneven between countries; 'named after' a place is not 'invented there'; summaries of short texts are not surveys.

## How to rerun

Needs Python 3 with shapely, pyproj, matplotlib and Pillow, xelatex and pdftotext. Raw inputs were fetched in a browser on {R['meta']['retrieved']} and are read in place from `/home/claude/hist/_data18/food-map/` (set in `code/common.py`): `foodmap_wd_wp_part1.json.gz` (Wikidata query results and Wikipedia articles), `foodmap_wp_part2.json.gz` (Wikipedia link resolution, cuisine categories, lead image licences), `foodmap_images_part3.json.gz` (Wikidata images and their Commons licences). Natural Earth admin-1 is downloaded to memory by `02_geo.py`. Intermediate files go to `/dev/shm/food/work` (set `FOODTMP` to change).

```
python3 code/02_geo.py         # world outlines, regions, city labels
python3 code/01_parse.py       # parse the browser bundles
python3 code/03_dishes.py      # dish table and regional placement
python3 code/04_national.py    # national dishes
python3 code/05_meals.py       # breakfast styles, main meal, meal times
python3 code/06_results.py     # results.json and page data
python3 code/07_build_site.py  # index.html
python3 code/08_figures.py     # header, blog and paper figures
python3 code/09_paper.py       # paper PDF
python3 code/11_readme.py      # README and LICENSE
python3 code/10_release.py     # blog post, Zenodo files
python3 reddit/collage.py      # collage
```

## Sources and licences

- English Wikipedia: 'National dish', 'Breakfast by country', 'Lunch', 'Dinner', and the cuisine articles and categories. CC BY-SA 4.0. The breakfast and main-meal summaries are derived from this text, so derived data are CC BY-SA 4.0.
- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Wikimedia Commons: dish photos shown on the page are linked, not copied, each with its author and licence (recorded in `data/national_dishes.csv` and `data/site.json`).
- Natural Earth: admin-0 countries (1:50m) and admin-1 states and provinces (1:10m). Public domain.
- GeoNames city names (via the sun-and-rain project's cleaned file). CC BY 4.0.
- OS Open Names. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0.
- Clock and sun offsets: https://maps.tristanhotham.com/clock-vs-sun/ (its time zone boundaries are from timezone-boundary-builder, ODbL).
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) What does the world eat? National dishes, breakfasts, regional dishes and the main meal of the day from Wikipedia and Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

Code: MIT. Text, figures and derived data: CC BY-SA 4.0.
"""
for bad in ("—", "–", "--"):
    assert bad not in readme.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/ and the page scripts. The text of the
page, the figures and the derived data files in data/ are released under
CC BY-SA 4.0, because they summarise and quote material from English Wikipedia
(CC BY-SA 4.0). Wikidata is CC0. Dish photos on the page are linked from
Wikimedia Commons, each under its own licence as credited. Place data contain
OS Open Names (Open Government Licence v3.0, contains OS data (c) Crown
copyright and database right 2026) and GeoNames data (CC BY 4.0). Country and
province outlines are Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
