"""Blog post and meta (release/blog), Zenodo files and meta (release/zenodo)."""
import re, shutil, zipfile, json as _json
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_What_Does_the_World_Eat"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "list": return ", ".join(v[:-1]) + " and " + v[-1]
    raise ValueError(f)


# facts stated in words in the blog (alt text included)
rows = [m for m in SITE["main"] if not m["regional_statement"] and (m["lunch_mid_clock"] != "" or m["dinner_mid_clock"] != "") and m["clock_ahead_of_sun_min"] != ""]
assert len(rows) == 24, len(rows)
assert R["spain"]["lunch_sun"] == "12:16" and R["spain"]["dinner_sun"] == "19:31" and R["spain"]["dinner_clock"] == "21:15"
fam = {i: c["f"] for i, c in SITE["nat"].items()}
for i in ("RUS", "CHN", "AUS", "ARG"): assert fam[i] == "meat", i
for i in ("BRA", "ETH"): assert fam[i] == "soups", i
for i in ("IND", "PAK", "SAU"): assert fam[i] == "rice", i
assert R["national"]["max_country"] == "France"
assert {"Escargot", "Cassoulet"} <= {x["d"] for x in SITE["nat"]["FRA"]["l"]}
brk = {b["iso3"]: b["style"] for b in SITE["brk"]}
assert brk["ARG"] == "sweet" and brk["FRA"] == "sweet"
mm = {m["iso3"]: m["main_meal"] for m in SITE["main"]}
assert mm["RUS"] == mm["EGY"] == mm["IDN"] == "midday" and mm["PHL"] == mm["ITA"] == mm["IND"] == "evening"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), post)
for img in re.findall(r"\{\{IMG\|([^|]+)\|", post):
    assert os.path.exists(f"{REL}/blog/{img}"), img
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
assert "\u2014" not in vis and "\u2013" not in vis and "--" not in vis
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "What does the world eat? National dishes, breakfasts and regional food on one map",
        "slug": "food-map",
        "excerpt": f"National dishes for {R['national']['n_countries']} countries and territories, breakfast styles for {R['breakfast']['n_countries']}, and {R['regional']['n_dishes']:,} regional dishes from fabada in Asturias to takoyaki in Osaka, mapped from Wikipedia and Wikidata. And why there is no lunch map.",
        "seo_description": f"An atlas of national dishes, breakfasts, {R['regional']['n_dishes']:,} regional dishes and the main meal of the day, from Wikipedia and Wikidata.",
        "tags": ["food", "national dishes", "breakfast", "regional cuisine", "maps", "data visualisation", "Wikidata", "Spain"],
        "header_alt": "Title card reading 'What does the world eat?' in black and tomato red on cream, beside a world map coloured by the family of each country's first-listed national dish: red meat dishes across Russia, China and Australia, yellow starchy staples across Africa and Canada, orange stews in Brazil, purple rice dishes across South Asia. Text: national dishes for " + str(R["national"]["n_countries"]) + " countries and territories, breakfast styles, " + f"{R['regional']['n_dishes']:,}" + " regional dishes and the main meal of the day."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
assert fam["CAN"] == "porridge"
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
shutil.copy(f"{REL}/{NAME}.pdf", f"{Z}/{NAME}.pdf")
for f in ("national_dishes.csv", "breakfast.csv", "main_meal.csv", "regional_dishes.csv", "region_counts.csv", "dishes.csv", "results.json"):
    shutil.copy(f"{DATA}/{f}", f"{Z}/{f}")
zp = f"{Z}/food-map_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"food-map/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"food-map/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "What Does the World Eat? National Dishes, Breakfasts, Regional Dishes and the Main Meal of the Day from Wikipedia and Wikidata",
         "description_html": f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/food-map/. Data and code: https://github.com/Tristan-Hotham/food-map. Blog post: to follow.</p>",
         "keywords": ["food", "national dishes", "breakfast", "regional cuisine", "meal times", "main meal", "Wikidata", "Wikipedia", "solar time", "maps"],
         "licence": "cc-by-sa-4.0",
         "related": [{"identifier": "https://github.com/Tristan-Hotham/food-map", "relation": "issupplementedby", "resource_type": "software"},
                     {"identifier": "https://maps.tristanhotham.com/food-map/", "relation": "issupplementedby", "resource_type": "other"},
                     {"identifier": "https://www.wikidata.org/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://en.wikipedia.org/wiki/National_dish", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://en.wikipedia.org/wiki/Breakfast_by_country", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://en.wikipedia.org/wiki/Lunch", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://en.wikipedia.org/wiki/Dinner", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://www.naturalearthdata.com/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://www.geonames.org/", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://www.ordnancesurvey.co.uk/products/os-open-names", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://maps.tristanhotham.com/clock-vs-sun/", "relation": "isderivedfrom", "resource_type": "other"}]}
jsave(zmeta, f"{Z}/meta.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
print("blog words", words, "; zenodo files", sorted(os.listdir(Z)))
