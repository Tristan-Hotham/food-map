# What does the world eat?

An atlas of national dishes, breakfasts, regional dishes and the main meal of the day, built from English Wikipedia and Wikidata: 186 countries and territories with suggested national dishes, breakfast styles for 73 countries, 2,706 dishes placed in 485 regions of 65 countries, and the main meal for 49 countries.

Interactive page: https://maps.tristanhotham.com/food-map/
Paper: https://doi.org/10.5281/zenodo.23761260
Blog post: https://blog.tristanhotham.com/2026/10/29/food-map/

## Headline results

- The first-listed national dish is most often meat or a grill (42 of 186, 23%), then a starchy staple such as a maize or cassava porridge (29), then a soup, stew or curry (27) and a rice dish (24). France has the most suggestions (13); the median country has 2.
- Breakfast: of 25 European countries described, 17 start with bread and savoury toppings and 5 (France, Greece, Italy, Malta, Spain) with coffee and something sweet. Britain and Ireland share a style with North America, Australia and New Zealand.
- 2,706 of 8,363 Wikidata foods with a country (32%) can be placed in a region. Japan (505), Indonesia (490) and Italy (388) hold 51% of them; Mexico has 21, Turkey 45, Ireland 1.
- Spain: 199 dishes in 17 of 19 regions, led by Catalonia (44); fabada in Asturias, paella in the Valencian Community.
- No Wikidata food is tagged with lunch or dinner as its course (0 and 0), against 464 main courses: separate lunch and dinner maps are not supported, so the atlas maps which meal is the main meal instead. Midday in 34 of 49 coded countries, evening in 11.
- Spain's lunch (middle of the window, 14:00 on the clock) is at 12:16 by the sun; its supper (21:15) at 19:31, 24 minutes after Britain's evening meal by the sun (87 minutes on the clock). 17 of 20 countries with stated lunch times eat before 1 pm sun time.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`; page data embedded, `data/regions.json` loaded on use). |
| `header.png` | Social card, 1200 x 630. |
| `data/national_dishes.csv` | Every dish in Wikipedia's 'National dish' list by country (and part of country), in order, with Wikipedia title, Wikidata item, family and source of the family, and the free photo used with its author and licence. |
| `data/breakfast.csv` | Breakfast style and a short summary of foods for each country described in 'Breakfast by country', with the section used. |
| `data/main_meal.csv` | Main meal (midday, evening, shifting, morning), stated lunch and dinner times, the same times by the sun, the country's lead of clock over sun, the note and the source article. |
| `data/dishes.csv` | All 8,363 Wikidata foods kept, with country, family, region (if any), the evidence used and the mapped place. |
| `data/regional_dishes.csv`, `data/region_counts.csv` | The 2,706 placed dishes, and dishes per region. |
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

Needs Python 3 with shapely, pyproj, matplotlib and Pillow, xelatex and pdftotext. Raw inputs were fetched in a browser on 29 October 2026 and are read in place from `/home/claude/hist/_data18/food-map/` (set in `code/common.py`): `foodmap_wd_wp_part1.json.gz` (Wikidata query results and Wikipedia articles), `foodmap_wp_part2.json.gz` (Wikipedia link resolution, cuisine categories, lead image licences), `foodmap_images_part3.json.gz` (Wikidata images and their Commons licences). Natural Earth admin-1 is downloaded to memory by `02_geo.py`. Intermediate files go to `/dev/shm/food/work` (set `FOODTMP` to change).

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

Hotham, T. (2026) What does the world eat? National dishes, breakfasts, regional dishes and the main meal of the day from Wikipedia and Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23761260

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

Code: MIT. Text, figures and derived data: CC BY-SA 4.0.
