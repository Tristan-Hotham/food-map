"""results.json (every number used in the page, paper, blog and collage) and the page data files.
Outputs: data/results.json, data/site.json, data/regions.json, data/regional_dishes.csv, data/region_counts.csv
"""
import csv, collections, re, statistics
from shapely.geometry import shape, mapping
from common import *

geo = jload(f"{DATA}/countries_geo.json")
dishes = jload(f"{WORK}/dishes.json"); nat = jload(f"{WORK}/national.json"); meals = jload(f"{WORK}/meals.json")
P18 = jload(f"{WORK}/images_p18.json"); regall = jload(f"{WORK}/regions_all.json")
FREE = re.compile(r"^(CC BY|CC0|Public domain|GFDL|FAL|Attribution|Copyrighted free use|KOGL)", re.I)
FAMNAME = {"rice": "Rice dishes", "noodles": "Noodles and pasta", "dumplings": "Dumplings, pies and pastries",
           "soups": "Soups, stews and curries", "fish": "Fish and seafood", "meat": "Meat and grills",
           "bread": "Breads, pancakes and sandwiches", "porridge": "Starchy staples: porridges, grains, potatoes",
           "veg": "Beans, vegetables and eggs", "sweets": "Sweets and desserts", "cheese": "Cheese", "drinks": "Drinks and sauces",
           "other": "Other"}
SHORT = {"CHN": "China", "USA": "United States", "COD": "DR Congo", "COG": "Republic of the Congo", "PRK": "North Korea",
         "KOR": "South Korea", "GBR": "United Kingdom", "RUS": "Russia", "CZE": "Czechia", "BIH": "Bosnia and Herzegovina"}
for k, v in SHORT.items():
    if k in geo: geo[k]["name"] = v
cname = lambda i: geo[i]["name"] if i in geo else i


def photo_for(qid):
    f = P18["p18"].get(qid)
    inf = P18["info"].get(f) if f else None
    if inf and FREE.match(inf["lic"] or "") and inf.get("thumb"):
        return {"t": inf["thumb"], "p": inf["page"], "a": inf["artist"][:80], "l": inf["lic"], "u": inf["licurl"]}
    return None


R = {"meta": {"retrieved": "29 October 2026", "doi": DOI}}

# ---------------- national dishes
natc = [r for r in nat if not r["part"] and r["iso3"] in geo]
by_c = collections.defaultdict(list)
for r in natc:
    by_c[r["iso3"]].append(r)
first = {i: L[0] for i, L in by_c.items()}
famc = collections.Counter(r["family"] for r in first.values())
R["national"] = {
    "n_countries": len(by_c), "n_mentions": len(natc), "n_distinct": len({(r["qid"] or r["dish"].lower()) for r in natc}),
    "n_parts": len({(r["iso3"], r["part"]) for r in nat if r["part"]}),
    "median_per_country": statistics.median(len(v) for v in by_c.values()),
    "max_country": cname(max(by_c, key=lambda i: len(by_c[i]))), "max_n": max(len(v) for v in by_c.values()),
    "n_one": sum(1 for v in by_c.values() if len(v) == 1),
    "family_first": [{"f": f, "name": FAMNAME[f], "n": n, "share": n / len(first)} for f, n in famc.most_common()],
}
shared = collections.defaultdict(set)
for r in natc:
    shared[(r["qid"] or r["dish"].lower())].add(r["iso3"])
top_shared = sorted(shared.items(), key=lambda kv: -len(kv[1]))[:8]
qname = {(r["qid"] or r["dish"].lower()): (r["wikipedia"] or r["dish"]) for r in natc}
R["national"]["shared"] = [{"dish": qname[k], "n": len(v), "countries": sorted(cname(i) for i in v)} for k, v in top_shared if len(v) >= 3]
R["national"]["n_with_photo_first"] = 0

site_nat = {}
for i, L in by_c.items():
    L2 = []
    for r in L:
        ph = None
        if r["img_thumb"] and FREE.match(r["img_licence"] or ""):
            ph = {"t": r["img_thumb"], "p": r["img_page"], "a": r["img_artist"][:80], "l": r["img_licence"], "u": r["img_licence_url"]}
        elif r["qid"]:
            ph = photo_for(r["qid"])
        L2.append({"d": r["dish"], "w": r["wikipedia"], "q": r["qid"], "f": r["family"], "ph": ph, "x": r["description"][:90]})
    parts = collections.defaultdict(list)
    for r in nat:
        if r["iso3"] == i and r["part"]:
            parts[r["part"]].append(r["dish"])
    site_nat[i] = {"f": first[i]["family"], "l": L2, "parts": [{"n": k, "d": v} for k, v in parts.items()]}
    if L2[0]["ph"]:
        R["national"]["n_with_photo_first"] += 1
R["national"]["photo_share_first"] = R["national"]["n_with_photo_first"] / len(by_c)

# ---------------- regional dishes
reg_feats = {f["properties"]["k"]: f for f in regall["features"]}
placed = [d for d in dishes if d["regions"]]
byreg = collections.defaultdict(list)
for d in placed:
    for k in d["regions"].split("|"):
        byreg[k].append(d)
cty_placed = collections.Counter()
cty_all = collections.Counter()
for d in dishes:
    for c in d["countries"].split("|"):
        cty_all[c] += 1
for d in placed:
    for c in {reg_feats[k]["properties"]["iso"] for k in d["regions"].split("|")}:
        cty_placed[{"HKG": "CHN", "MAC": "CHN"}.get(c, c)] += 1
ev = collections.Counter(d["region_evidence"] for d in placed)
regc = sorted(((k, len(v)) for k, v in byreg.items()), key=lambda kv: -kv[1])
FOCUS = ["ESP", "ITA", "FRA", "GBR", "IRL", "DEU", "MEX", "USA", "CHN", "IND", "JPN", "TUR", "IDN", "PRT", "BRA", "KOR"]
fc = {}
for c in FOCUS:
    regs_c = [f["properties"]["k"] for f in regall["features"] if f["properties"]["iso"] == c]
    with_d = [k for k in regs_c if k in byreg]
    best = max(with_d, key=lambda k: len(byreg[k])) if with_d else None
    fc[c] = {"name": cname(c), "dishes": cty_placed[c], "regions": len(regs_c), "regions_with": len(with_d),
             "top_region": reg_feats[best]["properties"]["name"] if best else "", "top_n": len(byreg[best]) if best else 0,
             "all_dishes": cty_all[c]}
R["regional"] = {"n_dishes": len(placed), "n_regions": len(byreg), "n_countries": len(cty_placed),
                 "n_wikidata_food": len(dishes), "share_placed": len(placed) / len(dishes),
                 "evidence": {k: ev[k] for k in ("place", "origin", "cuisine", "cat", "name")},
                 "top": [{"k": k, "name": reg_feats[k]["properties"]["name"], "country": cname(reg_feats[k]["properties"]["iso"]), "n": n} for k, n in regc[:15]],
                 "focus": fc,
                 "top_countries": [{"iso": c, "name": cname(c), "n": n} for c, n in cty_placed.most_common(12)]}
# named examples used in the text (checked here so the words stay true)
def where(name):
    for d in placed:
        if d["name"].lower() == name.lower():
            return d["region_names"].split("|")[0]
    return None
EX = {n: where(n) for n in ["Fabada asturiana", "paella", "crema catalana", "Cornish pasty", "Lancashire hotpot", "Yorkshire pudding",
                            "Peking duck", "Kung Pao chicken", "Cochinita pibil", "Adana kebabı", "Weisswurst", "takoyaki",
                            "Risotto alla milanese", "jambalaya", "Bakewell tart", "Eccles cake", "pa amb tomàquet", "Caldo galego", "gazpacho"]}
R["regional"]["examples"] = EX
es = [x for x in R["regional"]["top"]]
R["regional"]["uk"] = sorted([{"name": reg_feats[k]["properties"]["name"], "n": len(v), "d": [x["name"] for x in v[:6]]} for k, v in byreg.items() if k.startswith("GBR:")], key=lambda x: -x["n"])
R["regional"]["spain"] = sorted([{"name": reg_feats[k]["properties"]["name"], "n": len(v), "d": [x["name"] for x in v[:6]]} for k, v in byreg.items() if k.startswith("ESP:")], key=lambda x: -x["n"])

with open(f"{DATA}/regional_dishes.csv", "w", newline="", encoding="utf-8") as f:
    cols = ["qid", "name", "enwiki", "desc", "sitelinks", "family", "countries", "regions", "region_names", "region_evidence", "place", "lat", "lon"]
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(dash(placed))
with open(f"{DATA}/region_counts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["region_key", "region", "country_iso3", "dishes"])
    for k, n in regc:
        w.writerow([k, reg_feats[k]["properties"]["name"], reg_feats[k]["properties"]["iso"], n])

# regions file for the page: every region of a country that has at least one placed dish
cty_with = {reg_feats[k]["properties"]["iso"] for k in byreg}
feats = []
for f in regall["features"]:
    p = f["properties"]
    if p["iso"] not in cty_with:
        continue
    g = shape(f["geometry"])
    g = g.simplify(0.02 if g.area < 20 else 0.05, preserve_topology=True)
    m = mapping(g)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 2), round(c[1], 2)]
    feats.append({"type": "Feature", "properties": {"k": p["k"], "i": p["iso"], "n": p["name"], "c": len(byreg.get(p["k"], []))},
                  "geometry": {"type": m["type"], "coordinates": rnd(m["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/regions.json")

# dishes for the page: compact rows
site_d = []
for d in placed:
    site_d.append([d["name"], d["qid"], d["family"], d["region_evidence"], d["regions"], d["sitelinks"],
                   d["lat"] if d["lat"] != "" else None, d["lon"] if d["lon"] != "" else None, d["place"], d["enwiki"], d["desc"][:90]])
reg_photo = {}
for k, L in byreg.items():
    for d in sorted(L, key=lambda x: -x["sitelinks"])[:2]:
        ph = photo_for(d["qid"])
        if ph:
            reg_photo[k] = {"q": d["qid"], "n": d["name"], **ph}
            break
R["regional"]["regions_with_photo"] = len(reg_photo)
R["regional"]["n_wikidata_food_all"] = len(jload(f"{WORK}/items.json"))
R["regional"]["share_top3"] = sum(cty_placed[c] for c in ("JPN", "IDN", "ITA")) / len(placed)
_cl = jload(f"{WORK}/cuisine_links.json"); _cats = jload(f"{WORK}/cats.json")
R["meta"]["n_cuisine_articles"] = len(_cl); R["meta"]["n_cuisine_cats"] = len(_cats)
R["meta"]["n_famfix"] = sum(1 for r in nat if r["fam_src"] != "wikidata"); R["meta"]["n_mentions_all"] = len(nat)

# ---------------- breakfast
brk = meals["breakfast"]
bs = collections.Counter(b["style"] for b in brk)
STY = {b["style"]: b["style_label"] for b in brk}
R["breakfast"] = {"n_countries": len(brk), "styles": [{"s": s, "name": STY[s], "n": n} for s, n in bs.most_common()],
                  "wd_breakfast_items": sum(v.get("breakfast", 0) for v in meals["course"].values()),
                  "wd_breakfast_countries": sum(1 for v in meals["course"].values() if v.get("breakfast"))}
eu = [b for b in brk if geo.get(b["iso3"], {}).get("continent") == "Europe"]
R["breakfast"]["europe"] = {"n": len(eu), "sweet": sum(b["style"] == "sweet" for b in eu), "bread": sum(b["style"] == "bread" for b in eu),
                            "sweet_names": sorted(cname(b["iso3"]) for b in eu if b["style"] == "sweet")}

# ---------------- main meal
mm = meals["main"]
mc = collections.Counter(m["main_meal"] for m in mm if m["main_meal"])
R["main_meal"] = {"n_coded": sum(1 for m in mm if m["main_meal"]), "n_named": sum(1 for m in mm if m["main_meal"] and not m["regional_statement"]),
                  "counts": dict(mc), "n_times": sum(1 for m in mm if m["lunch_mid_clock"] != "" or m["dinner_mid_clock"] != ""),
                  "wd_lunch_items": sum(v.get("lunch", 0) for v in meals["course"].values()),
                  "wd_dinner_items": sum(v.get("dinner", 0) for v in meals["course"].values()),
                  "wd_main_items": sum(v.get("main", 0) for v in meals["course"].values()),
                  "wd_main_countries": sum(1 for v in meals["course"].values() if v.get("main"))}
mid_named = sorted(cname(m["iso3"]) for m in mm if m["main_meal"] == "midday" and not m["regional_statement"])
eve_named = sorted(cname(m["iso3"]) for m in mm if m["main_meal"] == "evening")
R["main_meal"]["midday_names"] = mid_named; R["main_meal"]["evening_names"] = eve_named
tm = {m["iso3"]: m for m in mm}
def hhmm(h):
    m = int(round(float(h) * 60)); return f"{m // 60}:{m % 60:02d}"
sp, gb, us = tm["ESP"], tm["GBR"], tm["USA"]
R["spain"] = {"lunch_clock": hhmm(sp["lunch_mid_clock"]), "lunch_sun": hhmm(sp["lunch_mid_sun"]),
              "dinner_clock": hhmm(sp["dinner_mid_clock"]), "dinner_sun": hhmm(sp["dinner_mid_sun"]),
              "ahead_min": sp["clock_ahead_of_sun_min"], "gb_dinner_clock": hhmm(gb["dinner_mid_clock"]), "gb_dinner_sun": hhmm(gb["dinner_mid_sun"]),
              "gb_ahead_min": gb["clock_ahead_of_sun_min"], "us_dinner_clock": hhmm(us["dinner_mid_clock"]), "us_dinner_sun": hhmm(us["dinner_mid_sun"]),
              "gap_clock_min": round((float(sp["dinner_mid_clock"]) - float(gb["dinner_mid_clock"])) * 60),
              "gap_sun_min": round((float(sp["dinner_mid_sun"]) - float(gb["dinner_mid_sun"])) * 60),
              "lunch_from": sp["lunch_from"], "lunch_to": sp["lunch_to"], "dinner_from": sp["dinner_from"], "dinner_to": sp["dinner_to"]}
times = [m for m in mm if m["lunch_mid_clock"] != "" and not m["regional_statement"]]
R["times"] = {"latest_lunch": cname(max(times, key=lambda m: float(m["lunch_mid_clock"]))["iso3"]),
              "latest_lunch_clock": hhmm(max(float(m["lunch_mid_clock"]) for m in times)),
              "latest_lunch_sun": hhmm(max(times, key=lambda m: float(m["lunch_mid_clock"]))["lunch_mid_sun"]),
              "latest_sun": [{"name": cname(m["iso3"]), "sun": hhmm(m["lunch_mid_sun"])} for m in sorted(times, key=lambda m: -float(m["lunch_mid_sun"]))[:2]],
              "n_lunch": len(times),
              "n_lunch_sun_before_1": sum(1 for m in times if float(m["lunch_mid_sun"]) < 13),
              "spain_sun_vs_noon_min": round((float(sp["lunch_mid_sun"]) - 12) * 60)}

# ---------------- headline numbers for the hero
R["hero"] = {"countries_any": len(set(by_c) | {b["iso3"] for b in brk} | {m["iso3"] for m in mm} | set(cty_placed))}
site = {"nat": site_nat, "fam": FAMNAME, "brk": brk, "styles": STYLES if (STYLES := STY) else {}, "main": mm,
        "course": meals["course"], "dishes": site_d, "regphoto": reg_photo, "focus": FOCUS,
        "cname": {k: v["name"] for k, v in geo.items()}}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print({k: (os.path.getsize(f"{DATA}/{k}") // 1024) for k in ("site.json", "regions.json", "results.json")}, "KB")
print(R["national"]["family_first"][:5], R["national"]["shared"][:4])
print(R["regional"]["evidence"], R["regional"]["n_dishes"], R["regional"]["n_regions"], R["regional"]["n_countries"])
print(R["spain"], R["times"])
print(EX)
