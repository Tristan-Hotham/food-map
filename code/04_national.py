"""National dishes from the English Wikipedia list 'National dish' (section 'By country').

Each line '* [[Country]]: [[dish]], ...' gives the country and the dishes suggested for it; '**' lines give dishes for
parts of a country (England, Scotland, Asturias, Hawaii...). The article itself says it is 'not a definitive list'.
Links are resolved to Wikidata items through the Wikipedia API (redirects followed). Photos: the lead image of each
dish's English Wikipedia article, only when Wikimedia Commons gives a free licence, with author and licence kept.
Outputs: data/national_dishes.csv, work/national.json
"""
import csv, collections, re
from common import *

raw = jload(f"{WORK}/national_raw.json"); T = jload(f"{WORK}/titles.json"); IMG = jload(f"{WORK}/images.json")
items = jload(f"{WORK}/items.json"); geo = jload(f"{DATA}/countries_geo.json")
from families import family, family_from_text

name2iso = {norm(v["name"]): k for k, v in geo.items()}
ALIAS = {"china": "CHN", "korea north": "PRK", "korea south": "KOR", "united states": "USA", "united kingdom": "GBR", "czech republic": "CZE", "czechia": "CZE", "ivory coast": "CIV",
         "cote d ivoire": "CIV", "democratic republic of the congo": "COD", "republic of the congo": "COG", "congo": "COG",
         "the gambia": "GMB", "gambia": "GMB", "the bahamas": "BHS", "bahamas": "BHS", "east timor": "TLS", "timor leste": "TLS",
         "eswatini": "SWZ", "swaziland": "SWZ", "north macedonia": "MKD", "macedonia": "MKD", "russia": "RUS", "south korea": "KOR",
         "north korea": "PRK", "korea": "KOR", "laos": "LAO", "vietnam": "VNM", "syria": "SYR", "iran": "IRN", "bolivia": "BOL",
         "venezuela": "VEN", "tanzania": "TZA", "moldova": "MDA", "brunei": "BRN", "cape verde": "CPV", "cabo verde": "CPV",
         "federated states of micronesia": "FSM", "micronesia": "FSM", "palestine": "PSE", "state of palestine": "PSE",
         "taiwan": "TWN", "vatican city": "VAT", "bosnia and herzegovina": "BIH", "sao tome and principe": "STP",
         "saint kitts and nevis": "KNA", "saint lucia": "LCA", "saint vincent and the grenadines": "VCT",
         "trinidad and tobago": "TTO", "antigua and barbuda": "ATG", "united arab emirates": "ARE", "dominican republic": "DOM",
         "central african republic": "CAF", "equatorial guinea": "GNQ", "papua new guinea": "PNG", "solomon islands": "SLB",
         "marshall islands": "MHL", "hong kong": "HKG", "macau": "MAC", "puerto rico": "PRI", "kosovo": "XKX", "greenland": "GRL",
         "faroe islands": "FRO", "curacao": "CUW", "aruba": "ABW", "guam": "GUM", "american samoa": "ASM",
         "northern mariana islands": "MNP", "united states virgin islands": "VIR", "british virgin islands": "VGB",
         "cayman islands": "CYM", "bermuda": "BMU", "new caledonia": "NCL", "french polynesia": "PYF", "isle of man": "IMN",
         "jersey": "JEY", "guernsey": "GGY", "gibraltar": "GIB", "turkiye": "TUR", "burma": "MMR", "myanmar": "MMR",
         "sint maarten": "SXM", "northern cyprus": "CYN", "somaliland": "SOL", "western sahara": "ESH", "tibet": None}
SUBREG = {("ESP", "asturias"): "ESP:Asturias", ("ESP", "catalonia"): "ESP:Cataluña", ("ESP", "galicia"): "ESP:Galicia",
          ("ESP", "madrid"): "ESP:Madrid", ("ESP", "valencia"): "ESP:Valenciana", ("GBR", "scotland"): "GBR:Scotland",
          ("GBR", "wales"): "GBR:Wales", ("GBR", "northern ireland"): "GBR:Northern Ireland",
          ("GBR", "cornwall"): "GBR:South West", ("GBR", "devon"): "GBR:South West", ("GBR", "shetland isles"): "GBR:Scotland"}


def to_iso(place):
    n = norm(place)
    if n in ALIAS:
        return ALIAS[n]
    return name2iso.get(n)


def resolve(title):
    if not title:
        return "", {}
    t = title[:1].upper() + title[1:]
    t = T["norm"].get(t, t)
    t = T["redirects"].get(t, t)
    return t, T["res"].get(t, {})


# hand-set families for dishes the Wikidata class tree does not place (my reading of each dish's description)
FAMFIX = {"couscous": "porridge", "keshi yena": "cheese", "crack conch": "fish", "kuli-kuli": "veg", "ambuyat": "porridge",
          "riz gras": "rice", "boule": "porridge", "casado": "rice", "zagorski štrukli": "dumplings", "vepřo knedlo zelo": "meat",
          "skoudehkaris": "rice", "ful medames": "veg", "succotash": "veg", "kama": "porridge", "caldo de mancarra": "soups",
          "griot": "meat", "baleada": "bread", "atcheke": "porridge", "kimchi": "veg", "flia": "dumplings", "dumboy": "porridge",
          "stuffat tal-fenek": "soups", "dholl": "veg", "barbagiuan": "dumplings", "coconut fish": "fish", "dambou": "porridge",
          "tavče gravče": "veg", "maqluba": "rice", "bariis iskukaris": "rice", "chipsi mayai": "veg", "pulaka": "porridge",
          "matooke": "porridge", "fry-up": "meat", "tortilla de patatas": "veg", "la bandera": "rice", "shisa nyama": "meat", "curry crab": "fish", "kelaguen": "meat", "fettuccine alla papalina": "noodles", "dumplings": "dumplings", "ajiaco": "soups", "dolma": "veg", "harees": "porridge", "laplap": "porridge", "mountain chicken": "meat"}


def fam_of(it, q, text, dish=""):
    if dish.lower() in FAMFIX:
        return FAMFIX[dish.lower()], "description"
    f = family(it, q) if it else "other"
    return (f, "wikidata") if f != "other" else (family_from_text(text), "description")


rows, unmatched = [], []
cur = None
for r in raw:
    if r["depth"] == 1:
        cur = to_iso(r["place"])
        if not cur:
            unmatched.append(r["place"]); continue
        iso, sub, subname = cur, "", ""
    else:
        if not cur:
            continue
        iso2 = to_iso(r["place"])
        if iso2 and iso2 != cur and iso2 in geo:
            iso, sub, subname = iso2, "", ""          # territories with their own outline (Puerto Rico, Guam...)
        else:
            iso, sub, subname = cur, SUBREG.get((cur, norm(r["place"])), ""), r["place"]
    links = r["links"] or [{"target": "", "shown": p.strip()} for p in re.split(r",| and ", re.sub(r"\(.*?\)", "", r["text"])) if p.strip()]
    for k, l in enumerate(links):   # lines without links: the plain dish names are kept, with no Wikidata item
        title, info = resolve(l["target"])
        q = info.get("q", "")
        img = IMG.get(info.get("img", ""), {}) if info.get("img") else {}
        it = items.get(q)
        rows.append({"iso3": iso, "country": geo.get(iso, {}).get("name", r["place"]), "part": subname, "region": sub,
                     "rank_in_line": k + 1, "dish": l["shown"][:1].upper() + l["shown"][1:], "wikipedia": title, "qid": q,
                     "description": info.get("d", ""), "family": fam_of(it, q, info.get("d", "") + " " + title, l["shown"])[0],
                     "fam_src": fam_of(it, q, info.get("d", "") + " " + title, l["shown"])[1],
                     "in_wikidata_food": int(bool(it)),
                     "img_thumb": img.get("thumb", ""), "img_page": img.get("page", ""), "img_artist": img.get("artist", ""),
                     "img_licence": img.get("lic", ""), "img_licence_url": img.get("licurl", "")})
with open(f"{DATA}/national_dishes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(dash(rows))
jsave(rows, f"{WORK}/national.json")
nat = [r for r in rows if not r["part"]]
print(len(rows), "dish mentions;", len({r['iso3'] for r in nat}), "countries;", "unmatched places:", unmatched)
print(collections.Counter(r["family"] for r in nat if r["rank_in_line"] == 1).most_common())
print(collections.Counter(r["dish"].lower() for r in nat).most_common(12))
print(sum(1 for r in nat if r["img_thumb"]), "with free photo")
