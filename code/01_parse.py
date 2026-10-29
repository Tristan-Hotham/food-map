"""Parse the browser bundles (Wikidata via QLever, English Wikipedia) into compact working tables in work/.

Inputs (read in place from RAW): foodmap_wd_wp_part1.json.gz, foodmap_wp_part2.json.gz, foodmap_images_part3.json.gz
Outputs: work/items.json, work/locs.json, work/cuisines.json, work/iso.json, work/classes.json,
         work/national_raw.json, work/titles.json, work/images.json, work/cats.json, work/cuisine_links.json
"""
import re
from common import *

P1 = jload(f"{RAW}/foodmap_wd_wp_part1.json.gz")
P2 = jload(f"{RAW}/foodmap_wp_part2.json.gz")
P3 = jload(f"{RAW}/foodmap_images_part3.json.gz")
wd, wp = P1["wd"], P1["wp"]

# ---- Wikidata food items (dishes, breads, cheeses, sausages, pastries, desserts)
items = {}
for r in tsv(wd["items_tsv"]):
    q = r["x"]
    it = items.setdefault(q, {"kinds": [], "label": r["label"], "enwiki": r["enwiki"], "p495": split(r["p495"]),
                              "p2012": split(r["p2012"]), "locs": split(r["locs"]), "course": split(r["course"]),
                              "image": r["image"].replace("http://commons.wikimedia.org/wiki/Special:FilePath/", ""),
                              "p31": split(r["p31"])})
    it["kinds"].append(r["kind"])
for r in tsv(wd["items_extra_tsv"]):
    if r["x"] in items:
        items[r["x"]]["sl"] = int(r["sl"] or 0)
        items[r["x"]]["desc"] = r["desc"]
for it in items.values():
    it["kinds"] = sorted(set(it["kinds"]))
    it.setdefault("sl", 0); it.setdefault("desc", "")
jsave(items, f"{WORK}/items.json")

locs = {}
for r in tsv(wd["locations_tsv"]):
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", r["coord"] or "")
    locs[r["x"]] = {"label": r["label"], "lon": float(m.group(1)) if m else None, "lat": float(m.group(2)) if m else None,
                    "country": split(r["country"]), "iso3": r["iso3"], "p31": split(r["p31"])}
jsave(locs, f"{WORK}/locs.json")

iso = {}
for r in tsv(wd["countries_tsv"]):
    if re.fullmatch(r"[A-Z]{3}", r["iso3"] or ""):
        iso[r["x"]] = r["iso3"]
jsave(iso, f"{WORK}/iso.json")

cuis = {}
for r in tsv(wd["cuisines_tsv"]):
    cuis[r["x"]] = {"label": r["label"], "enwiki": r["enwiki"], "locs": split(r["locs"]), "country": split(r["country"]),
                    "cat": r["cat"]}
jsave(cuis, f"{WORK}/cuisines.json")

# class graph (P279 edges inside the food tree) and labels
edges = {}
for ln in wd["p279_edges"].split("\n"):
    a, _, b = ln.partition("\t")
    if a and b:
        edges.setdefault(a, []).append(b)
labels = {}
for ln in wd["class_label_map"].split("\n"):
    a, _, b = ln.partition("\t")
    if a.startswith("Q"):
        labels[a] = b.strip('"')
jsave({"edges": edges, "labels": labels}, f"{WORK}/classes.json")

# ---- English Wikipedia
def strip_refs(w):
    w = re.sub(r"<ref[^>]*/>", "", w)
    return re.sub(r"<ref.*?</ref>", "", w, flags=re.S)


# National dish list: '* [[Country]]: [[dish]], [[dish|shown]] ...' with '**' sub-national lines
nd = strip_refs(wp["pages"]["National dish"]["wikitext"])
body = nd[nd.index("==By country=="):nd.index("==Latin American dishes==")]
rows, parents = [], {}
for ln in body.split("\n"):
    m = re.match(r"^(\*+)\s*\[\[([^\]]+)\]\]\s*:\s*(.*)$", ln)
    if not m:
        continue
    depth = len(m.group(1))
    tgt, _, shown = m.group(2).partition("|")
    place = (shown or tgt).strip()
    if place.lower().startswith("cuisine of "):
        place = place[11:].strip()
    rest = re.sub(r"\{\{[^{}]*\}\}", "", m.group(3))
    links = []
    for lm in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]", rest):
        links.append({"target": lm.group(1).strip(), "shown": (lm.group(2) or lm.group(1)).strip()})
    plain = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", rest)
    plain = re.sub(r"''+", "", plain).strip()
    parents[depth] = place
    rows.append({"depth": depth, "place": place, "place_target": tgt.strip(), "parent": parents.get(depth - 1) if depth > 1 else None,
                 "links": links, "text": plain})
jsave(rows, f"{WORK}/national_raw.json", indent=0)

T = P2["titles"]
jsave(T, f"{WORK}/titles.json")
jsave(P2["images"], f"{WORK}/images.json")
jsave({"p18": P3["p18"], "info": P3["info"]}, f"{WORK}/images_p18.json")
jsave(P2["cats"], f"{WORK}/cats.json")

# links in each cuisine article (used as weak regional evidence)
jsave({t: a["links"] for t, a in wp["cuisine_articles"].items()}, f"{WORK}/cuisine_links.json")
print(len(items), "items;", len(locs), "locations;", len(iso), "ISO countries;", len(cuis), "cuisines;",
      len(rows), "national dish lines;", len(T["res"]), "titles;", len(P2["images"]), "images;", len(P2["cats"]), "categories")
