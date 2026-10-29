"""Build the dish table: every Wikidata food item with a country and, where the evidence allows, a region.

Evidence for a region, strongest first (recorded per dish in 'how'):
  place   Wikidata 'indigenous to', 'location', 'located in', 'location of creation', 'place of origin' (P2341, P276,
          P131, P1071, P189, P740) pointing at a place inside a country
  origin  Wikidata 'country of origin' (P495) that is a place inside a country (e.g. Asturias)
  cuisine Wikidata 'cuisine' (P2012) that is a regional cuisine with a place
  cat     the English Wikipedia article sits in the category of a regional cuisine (e.g. Category:Asturian cuisine)
  link    a regional cuisine article on English Wikipedia links to the dish (weakest; only used when the dish is
          linked from no more than two regional cuisine articles of its country)
Places are put into regions by point in polygon (Natural Earth admin-1, see 02_geo.py).
Broad areas (continents, historical or cultural regions, ethnic groups, 'England') never place a dish in a region.
Outputs: data/dishes.csv, work/dishes.json
"""
import csv, collections, re
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

items = jload(f"{WORK}/items.json"); locs = jload(f"{WORK}/locs.json"); iso = jload(f"{WORK}/iso.json")
cuis = jload(f"{WORK}/cuisines.json"); cats = jload(f"{WORK}/cats.json"); cl = jload(f"{WORK}/classes.json")
clinks = jload(f"{WORK}/cuisine_links.json")
edges, clabels = cl["edges"], cl["labels"]
geo = jload(f"{DATA}/countries_geo.json")

# ---- items to leave out: brands, products, fictional foods, museum objects, generic dish types, cuisines
EXCL = {"Q127658477", "Q16323605", "Q10855061", "Q2424752", "Q167270", "Q431289", "Q15731648", "Q105815873",
        "Q129175596", "Q1778821", "Q94951"}
# historical or ambiguous 'countries of origin' mapped to today's country (as in the dog-breeds project)
HIST = {"Q18097": "KOR", "Q29520": "CHN", "Q500568": "JPN", "Q713750": "DEU", "Q8733": "CHN", "Q28179": "KOR",
        "Q26888": "PRT", "Q26253": "PRT", "Q3336843": None}
# broad areas: never used to place a dish in a region
BROAD_P31 = {"Q82794", "Q3502482", "Q1620908", "Q2221906", "Q5107", "Q41710", "Q3024240", "Q28171280", "Q137186904",
             "Q2418896", "Q207520", "Q5284036", "Q130533870", "Q3115110", "Q137834770", "Q6256", "Q15304003",
             "Q3624078", "Q1763527", "Q133442", "Q48349", "Q417175", "Q1250464", "Q1048835", "Q15239622", "Q7275",
             "Q11396118", "Q9357527", "Q855697", "Q15642541",
             "Q123615496", "Q518261", "Q33837", "Q1945590", "Q83828", "Q108788952", "Q25380035", "Q164509", "Q16887380",
             "Q2577883", "Q23442"}
ISLAND_OK = {"Mallorca", "Menorca", "Ibiza", "Crete", "Corsica", "Hainan", "Jeju Island", "Zanzibar", "Lemnos", "Chios",
             "Okinawa Island", "Cheung Chau", "Fuerteventura", "Gozo", "Bornholm", "Gotland", "Rügen", "Capri", "Ischia"}
BROAD_Q = {"Q21", "Q23666", "Q22", "Q25", "Q26", "Q145", "Q174193", "Q18097", "Q29520", "Q46", "Q48", "Q15", "Q49",
           "Q18", "Q828", "Q27611", "Q7204", "Q12557", "Q1032", "Q27468", "Q170072"}

# ---- country of each Wikidata place
def place_iso(q):
    if q in HIST:
        return HIST[q]
    if q in iso:
        return iso[q]
    L = locs.get(q)
    if not L:
        return None
    for c in L["country"]:
        if c in iso:
            return iso[c]
        if c in HIST and HIST[c]:
            return HIST[c]
    return None

FIX_ISO = {"HKG": "CHN", "MAC": "CHN"}   # Natural Earth draws these inside China at 1:50m; keep them with China
def fix(i):
    return FIX_ISO.get(i, i) if i else i

# ---- regions (point in polygon)
idx = jload(f"{WORK}/adm1_index.json")
polys = [shape(r["geometry"]) for r in idx]
tree = STRtree(polys)
wd2reg = {}
for r in idx:
    for q in r["wd"]:
        wd2reg[q] = r["k"]
regname = {r["k"]: r["name"] for r in idx}
regiso = {r["k"]: r["iso"] for r in idx}


def region_of(q):
    """Region key for a Wikidata place, or None if broad, unknown or unlocated."""
    if q in BROAD_Q or q in iso or q in HIST:
        return None
    L = locs.get(q)
    if not L or (set(L["p31"]) & BROAD_P31 and not (L["label"] in ISLAND_OK and "Q23442" in L["p31"])):
        return None
    if q in wd2reg:
        return wd2reg[q]
    if L["lat"] is None:
        return None
    p = Point(L["lon"], L["lat"])
    for i in tree.query(p):
        if polys[i].contains(p):
            return idx[i]["k"]
    # coastal places just outside a simplified outline: nearest region within about 10 km
    best, bd = None, 0.1
    for i in tree.query(p.buffer(0.1)):
        d = polys[i].distance(p)
        if d < bd:
            best, bd = idx[i]["k"], d
    return best


from families import family, FAMORDER

# ---- regional cuisines: their places and regions
cuis_region = {}
for q, c in cuis.items():
    regs = {region_of(l) for l in c["locs"]} - {None}
    if len(regs) == 1:
        cuis_region[q] = regs.pop()
cat_region = {c["cat"]: cuis_region[q] for q, c in cuis.items() if c["cat"] and q in cuis_region}
art_region = {c["enwiki"]: cuis_region[q] for q, c in cuis.items() if c["enwiki"] and q in cuis_region}

# category members -> regions
cat_hits = collections.defaultdict(set)
for cat, v in cats.items():
    r = cat_region.get(cat)
    if not r:
        continue
    for title, q in v["pages"]:   # direct members only: subcategories proved too loose
        if q:
            cat_hits[q].add(r)

title2q = {}
for q, it in items.items():
    if it["enwiki"]:
        title2q[it["enwiki"]] = q
        title2q[it["enwiki"][0].lower() + it["enwiki"][1:]] = q
link_hits = collections.defaultdict(set)
for art, links in clinks.items():
    r = art_region.get(art)
    if not r:
        continue
    for t in links:
        q = title2q.get(t) or title2q.get(t[:1].upper() + t[1:])
        if q:
            link_hits[q].add(r)

# ---- places named in dish names ('Bath bun', 'Fabada asturiana', 'Adana kebabı')
A2 = {v["a2"]: k for k, v in geo.items() if v.get("a2") and v["a2"] != "-99"}
gaz = collections.defaultdict(dict)   # iso3 -> norm name -> place
cp = jload("/home/claude/hist/sun-and-rain/data/cities_page.json")
ci = {k: i for i, k in enumerate(cp["cols"])}
for r in cp["rows"]:
    i3 = fix(A2.get(r[ci["cc"]]))
    n = norm(r[ci["name"]])
    if i3 and len(n) >= 4 and (n not in gaz[i3] or gaz[i3][n]["pop"] < r[ci["pop"]]):
        gaz[i3][n] = {"name": r[ci["name"]], "lat": round(r[ci["lat"]], 3), "lon": round(r[ci["lon"]], 3), "pop": r[ci["pop"]]}
import csv as _csv
county_pts = collections.defaultdict(list)
with open("/home/claude/hist/osnames_gb.tsv", encoding="utf-8") as f:   # OS Open Names towns and cities (GB)
    for r in _csv.DictReader(f, delimiter="\t"):
        if r["local_type"] in ("Town", "City", "Village") and r["county"]:
            county_pts[r["county"]].append((float(r["lat"]), float(r["lon"])))
        if r["local_type"] in ("Town", "City"):
            n = norm(r["name1"])
            if len(n) >= 4 and n not in gaz["GBR"]:
                gaz["GBR"][n] = {"name": r["name1"], "lat": round(float(r["lat"]), 3), "lon": round(float(r["lon"]), 3), "pop": 20000}
for cn, pts in county_pts.items():   # GB counties: mean position of their towns and villages
    n = norm(cn)
    if n not in gaz["GBR"]:
        gaz["GBR"][n] = {"name": cn, "lat": round(sum(p[0] for p in pts) / len(pts), 3), "lon": round(sum(p[1] for p in pts) / len(pts), 3), "pop": 10 ** 6}
for r in idx:   # region names themselves
    n = norm(r["name"])
    if len(n) >= 4:
        c = shape(r["geometry"]).representative_point()
        gaz[fix(r["iso"])].setdefault(n, {"name": r["name"], "lat": round(c.y, 3), "lon": round(c.x, 3), "pop": 10 ** 7, "reg": r["k"]})
# adjectives used in dish names, mapped to the place they refer to (my own table of common forms)
DEMONYM = {
 "ESP": {"asturiana": "Asturias", "asturiano": "Asturias", "gallega": "Galicia", "gallego": "Galicia", "galega": "Galicia", "galego": "Galicia",
         "vasca": "Basque Country", "vasco": "Basque Country", "catalana": "Catalonia", "catala": "Catalonia", "andaluz": "Andalusia",
         "andaluza": "Andalusia", "valenciana": "Valencian Community", "valenciano": "Valencian Community", "madrileno": "Madrid",
         "madrilena": "Madrid", "manchego": "Castilla-La Mancha", "manchega": "Castilla-La Mancha", "riojana": "La Rioja", "riojano": "La Rioja",
         "extremena": "Extremadura", "extremeno": "Extremadura", "murciano": "Murcia", "murciana": "Murcia", "canario": "Canary Islands",
         "canaria": "Canary Islands", "canarias": "Canary Islands", "navarra": "Navarre", "aragonesa": "Aragon", "aragones": "Aragon",
         "mallorquina": "Balearic Islands", "segoviano": "Segovia", "malaguena": "Malaga", "cordobes": "Cordoba", "sevillana": "Sevilla"},
 "ITA": {"napoletana": "Naples", "napoletano": "Naples", "neapolitan": "Naples", "siciliana": "Sicily", "siciliano": "Sicily", "sicilian": "Sicily",
         "romana": "Rome", "romano": "Rome", "milanese": "Milan", "bolognese": "Bologna", "genovese": "Genoa", "veneziana": "Venice",
         "veneziano": "Venice", "fiorentina": "Florence", "fiorentino": "Florence", "toscana": "Tuscany", "toscano": "Tuscany",
         "sarda": "Sardinia", "sardo": "Sardinia", "pugliese": "Apulia", "calabrese": "Calabria", "piemontese": "Piedmont",
         "ligure": "Liguria", "abruzzese": "Abruzzo", "parmigiana": "Parma", "modenese": "Modena", "trentina": "Trentino-South Tyrol",
         "valdostana": "Aosta Valley", "lombarda": "Lombardy", "friulana": "Friuli-Venezia Giulia", "marchigiana": "Marche",
         "umbra": "Umbria", "lucana": "Basilicata", "amatriciana": "Amatrice", "carbonara": None},
 "FRA": {"lyonnaise": "Lyon", "lyonnais": "Lyon", "provencale": "Provence-Alpes-Côte d'Azur", "provencal": "Provence-Alpes-Côte d'Azur",
         "nicoise": "Nice", "bretonne": "Brittany", "breton": "Brittany", "alsacienne": "Grand Est", "alsacien": "Grand Est",
         "normande": "Normandy", "normand": "Normandy", "parisienne": "Paris", "parisien": "Paris", "bordelaise": "Bordeaux",
         "toulousaine": "Toulouse", "savoyarde": "Auvergne-Rhône-Alpes", "basquaise": "Nouvelle-Aquitaine", "lorraine": "Grand Est",
         "bourguignon": "Bourgogne-Franche-Comté", "bourguignonne": "Bourgogne-Franche-Comté", "dauphinois": "Auvergne-Rhône-Alpes",
         "dauphinoise": "Auvergne-Rhône-Alpes", "marseillaise": "Marseille", "corse": "Corsica", "auvergnat": "Auvergne-Rhône-Alpes",
         "landaise": "Nouvelle-Aquitaine", "nantais": "Nantes", "nantaise": "Nantes", "lilloise": "Lille"},
 "GBR": {"cornish": "Cornwall", "welsh": "Wales", "scottish": "Scotland", "yorkshire": "Yorkshire and the Humber",
         "lancashire": "Lancashire", "devonshire": "Devon", "devon": "Devon", "cumberland": "Cumbria", "glamorgan": "The Vale of Glamorgan",
         "ulster": "Northern Ireland", "shropshire": "Shropshire", "staffordshire": "Staffordshire", "norfolk": "Norfolk",
         "suffolk": "Suffolk", "lincolnshire": "Lincolnshire", "derbyshire": "Derbyshire", "kentish": "Kent", "kent": "Kent",
         "wiltshire": "Wiltshire", "somerset": "Somerset", "dorset": "Dorset", "gloucester": "Gloucester", "cheshire": "Cheshire East",
         "london": "Greater London", "isle of wight": "Isle of Wight", "shetland": "Shetland Islands", "orkney": "Orkney Islands"},
 "DEU": {"bayerische": "Bavaria", "bavarian": "Bavaria", "schwabische": "Baden-Württemberg", "swabian": "Baden-Württemberg",
         "thuringer": "Thuringia", "berliner": "Berlin", "frankfurter": "Frankfurt am Main", "nurnberger": "Nuremberg",
         "munchner": "Munich", "hamburger": None, "westfalischer": "Nordrhein-Westfalen", "sachsische": "Sachsen", "badische": "Baden-Württemberg",
         "frankische": "Bavaria", "rheinischer": "Nordrhein-Westfalen", "pfalzer": "Rheinland-Pfalz", "hessische": "Hessen",
         "aachener": "Aachen", "dresdner": "Dresden", "kolsch": None, "leipziger": "Leipzig", "lubecker": "Lübeck"},
 "CHN": {"sichuan": "Sichuan", "szechuan": "Sichuan", "szechwan": "Sichuan", "cantonese": "Guangdong", "hunan": "Hunan",
         "peking": "Beijing", "hainanese": "Hainan", "yunnan": "Yunnan", "hokkien": "Fujian", "fujian": "Fujian", "teochew": "Guangdong",
         "shanghainese": "Shanghai", "xinjiang": "Xinjiang", "lanzhou": "Lanzhou", "wuhan": "Wuhan", "chongqing": "Chongqing"},
 "IND": {"goan": "Goa", "hyderabadi": "Telangana", "mysore": "Karnataka", "kashmiri": "Jammu and Kashmir", "gujarati": "Gujarat",
         "rajasthani": "Rajasthan", "chettinad": "Tamil Nadu", "bombay": "Mumbai", "madras": "Tamil Nadu", "malabar": "Kerala",
         "kerala": "Kerala", "punjabi": "Punjab", "bengali": "West Bengal", "lucknowi": "Lucknow", "awadhi": "Uttar Pradesh",
         "kolkata": "Kolkata", "calcutta": "Kolkata", "delhi": "Delhi", "mangalorean": "Karnataka", "udupi": "Karnataka",
         "assamese": "Assam", "odia": "Odisha", "bihari": "Bihar", "sindhi": None, "parsi": None, "andhra": "Andhra Pradesh"},
 "MEX": {"oaxaqueno": "Oaxaca", "oaxaquena": "Oaxaca", "oaxacan": "Oaxaca", "yucateco": "Yucatán", "yucateca": "Yucatán",
         "yucatecan": "Yucatán", "poblano": "Puebla", "poblana": "Puebla", "veracruzana": "Veracruz", "veracruzano": "Veracruz",
         "tapatio": "Guadalajara", "jalisciense": "Jalisco", "sonorense": "Sonora", "sinaloense": "Sinaloa", "norteno": None,
         "michoacana": "Michoacán", "regiomontano": "Monterrey", "potosino": "San Luis Potosí", "queretano": "Querétaro"},
 "JPN": {"hakata": "Fukuoka", "sanuki": "Kagawa", "edomae": "Tokyo", "kyo": None, "satsuma": "Kagoshima", "okinawan": "Okinawa"},
 "TUR": {"urfa": "Şanlıurfa", "antep": "Gaziantep", "adana": "Adana"},
 "USA": {"texan": "Texas", "louisiana": "Louisiana", "cajun": "Louisiana", "creole": None, "hawaiian": "Hawaii", "philly": "Philadelphia",
         "new england": "Massachusetts", "chicago": "Chicago", "maryland": "Maryland", "kentucky": "Kentucky", "carolina": None,
         "memphis": "Memphis", "nashville": "Nashville", "cincinnati": "Cincinnati", "buffalo": "Buffalo", "boston": "Boston",
         "manhattan": "New York", "brooklyn": "New York", "detroit": "Detroit", "california": "California", "florida": "Florida",
         "key lime": "Florida", "smithfield": "Virginia", "virginia": "Virginia", "georgia": None, "mississippi": "Mississippi"},
 "PRT": {"alentejana": "Alentejo", "alentejano": "Alentejo", "transmontana": "Norte (north)", "lisboa": "Lisbon", "porto": "Porto",
         "algarvia": "Algarve", "madeirense": "Madeira", "acoriana": "Azores", "belem": "Lisbon", "tripas": None, "minhota": "Norte (north)"},
}
NAME_STOP = {"royal", "imperial", "victoria", "union", "grand", "split", "nice", "sale", "mold", "bread", "cake", "rice", "pasta",
             "sugar", "salt", "butter", "cream", "black", "white", "green", "golden", "national", "orange", "lemon", "lime",
             "bacon", "chocolate", "honey", "pepper", "cheese", "olive", "garlic", "coffee", "ginger", "apple", "plum",
             "mango", "banana", "pear", "cherry", "coco", "coconut", "india", "china", "jersey", "york", "washington",
             "lincoln", "march", "may", "eccles cake", "shepherd", "king", "queen", "prince", "princess", "bishop", "abbey",
             "saint", "san", "santa", "santo", "sainte", "mount", "lake", "river", "port", "bay", "beach", "valley", "island",
             "london", "paris", "american", "english", "french", "german", "spanish", "italian", "turkish", "chinese", "indian",
             "mexican", "japanese", "korean", "british", "irish", "dutch", "swiss", "greek", "russian", "polish", "danish",
             "swedish", "belgian", "brazil", "peru", "chile", "cuba", "jamaica", "manila", "carolina", "mission", "pueblo",
             "wellington", "windsor", "nisshin", "ichiban", "albert", "napoleon", "garden", "market", "station", "bridge", "castle", "church", "hall", "farm", "mill", "park", "college", "school"}


def region_at(lat, lon):
    p = Point(lon, lat)
    for i in tree.query(p):
        if polys[i].contains(p):
            return idx[i]["k"]
    return None


def name_region(label, countries):
    """A region named, or implied by an adjective, in the dish's English label, inside one of its countries."""
    words = [w for w in re.split(r"[\s,()'’\-]+", label) if w]
    if len(words) < 2:
        return None
    nwords = [norm(w) for w in words]
    if any(n in NAME_STOP and n in ("wellington", "windsor", "nisshin", "ichiban", "albert", "napoleon") for n in nwords):
        return None
    for c in countries:
        dm = DEMONYM.get(c, {})
        G = gaz.get(c, {})
        hits = []
        for k in range(len(words)):
            for span in (3, 2, 1):
                if k + span > len(words):
                    continue
                n = " ".join(nwords[k:k + span])
                if n in dm:
                    tgt = dm[n]
                    if tgt and norm(tgt) in G:
                        hits.append((span, G[norm(tgt)]))
                    elif tgt:
                        for r in idx:
                            if fix(r["iso"]) == c and r["name"] == tgt:
                                hits.append((span, {"name": tgt, "reg": r["k"], "lat": None, "lon": None}))
                    continue
                if n in NAME_STOP or len(n) < 4 or not words[k][:1].isupper():
                    continue
                if n in G and (G[n]["pop"] >= 30000 or c == "GBR"):
                    hits.append((span, G[n]))
        for span, pl in sorted(hits, key=lambda h: -h[0]):
            reg = pl.get("reg") or (region_at(pl["lat"], pl["lon"]) if pl["lat"] is not None else None)
            if reg and fix(regiso[reg]) == c:
                if pl["lat"] is None:
                    pl = dict(pl); c0 = shape([r for r in idx if r["k"] == reg][0]["geometry"]).representative_point()
                    pl["lat"], pl["lon"] = round(c0.y, 3), round(c0.x, 3)
                return reg, pl
    return None


NOT_DISHES = {"Mercato Metropolitano in Elephant and Castle", "Casa Mira"}   # a market and a shop
rows = []
stats = collections.Counter()
for q, it in items.items():
    if set(it["p31"]) & EXCL or not it["label"] or "fictional" in it["desc"].lower():
        stats["excluded"] += 1
        continue
    if it["label"].lower() == it["label"] and len(it["label"]) < 3:
        continue
    if it["label"] in NOT_DISHES:
        continue
    countries = [fix(place_iso(p)) for p in it["p495"]]
    countries = list(dict.fromkeys(c for c in countries if c))
    reg, how = [], None
    cand = []
    for l in it["locs"]:
        r = region_of(l)
        if r: cand.append(("place", r, l))
    for l in it["p495"]:
        r = region_of(l)
        if r: cand.append(("origin", r, l))
    for c in it["p2012"]:
        if c in cuis_region: cand.append(("cuisine", cuis_region[c], c))
    ch = sorted(cat_hits.get(q, ()))
    if len(ch) <= 2 and countries and {fix(regiso[r]) for r in ch} <= set(countries):
        for r in ch:
            cand.append(("cat", r, ""))
    for strength in ("place", "origin", "cuisine", "cat"):
        rr = list(dict.fromkeys(r for h, r, _ in cand if h == strength))
        if rr:
            reg, how = rr[:3], strength
            break
    if False and not reg and q in link_hits:   # article links proved too loose (Welsh cuisine links trifle, toffee)
        lr = sorted(link_hits[q])
        cset = {regiso[r] for r in lr}
        if len(lr) <= 2 and countries and {fix(c) for c in cset} <= set(countries):
            reg, how = lr, "link"
    if not reg and countries:
        nm = name_region(it["label"], countries)
        if nm:
            reg, how = [nm[0]], "name"
            cand.append(("name", nm[0], nm[1]))
    # keep only regions that agree with the stated country (when there is one)
    if countries and reg:
        ok = [r for r in reg if fix(regiso[r]) in countries]
        if ok:
            reg = ok
        elif how in ("cat", "link", "cuisine"):
            reg, how = [], None
    if not countries and reg:
        countries = list(dict.fromkeys(fix(regiso[r]) for r in reg))
    if not countries:
        stats["no_country"] += 1
        continue
    pt = None
    for h, r, l in cand:
        if h in ("place", "origin") and r in reg and locs.get(l, {}).get("lat") is not None:
            pt = (round(locs[l]["lat"], 3), round(locs[l]["lon"], 3), locs[l]["label"])
            break
        if h == "name" and r in reg:
            pt = (l["lat"], l["lon"], l["name"])
            break
    fam = family(it, q)
    rows.append({"qid": q, "name": it["label"], "enwiki": it["enwiki"], "desc": it["desc"], "sitelinks": it["sl"],
                 "family": fam, "kinds": "|".join(it["kinds"]), "countries": "|".join(countries),
                 "regions": "|".join(reg), "region_names": "|".join(regname[r] for r in reg), "region_evidence": how or "",
                 "place": pt[2] if pt else "", "lat": pt[0] if pt else "", "lon": pt[1] if pt else "",
                 "course": "|".join(it["course"]), "image": it["image"]})
    stats["kept"] += 1
    stats["with_region"] += bool(reg)
    if how: stats["how_" + how] += 1

rows.sort(key=lambda r: (-r["sitelinks"], r["name"]))
with open(f"{DATA}/dishes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(dash(rows))
jsave(rows, f"{WORK}/dishes.json")
print(dict(stats))
by = collections.Counter(r for x in rows for r in x["regions"].split("|") if r)
print([(regname[k], n) for k, n in by.most_common(25)])
print(collections.Counter(x["family"] for x in rows).most_common())
