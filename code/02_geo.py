"""World outlines and food regions.

- data/world.json: Natural Earth 1:50m countries, simplified, keyed by ISO3.
- data/countries_geo.json: label point, continent, population for each country.
- data/regions.json: 'food regions' inside countries, from Natural Earth 1:10m admin-1 (states and
  provinces). Provinces are merged into their region for Spain, Italy, France, Portugal and England
  (Natural Earth 'region' field), and kept as states, provinces or prefectures elsewhere.
- data/cities.json: big-city labels (GeoNames via the sun-and-rain project's cleaned file).
- work/adm1_index.json: full-detail region polygons for point-in-polygon (small, rounded).
The admin-1 file (about 40 MB) is downloaded to memory (/dev/shm) and never written to disk here.
"""
import urllib.request
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from common import *

ne = jload(NE50)
feats, geo = [], {}


def rnd(c, k=2):
    return [rnd(x, k) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], k), round(c[1], k)]


for f in ne["features"]:
    p = f["properties"]
    iso = p.get("ISO_A3")
    if not iso or iso == "-99":
        iso = p.get("ADM0_A3")
    if iso == "ATA":
        continue
    if p.get("ADM0_A3") == "KOS":
        iso = "XKX"
    g = shape(f["geometry"])
    gs = g.simplify(0.06, preserve_topology=True)
    if gs.is_empty:
        continue
    m = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso, "name": p.get("NAME_EN") or p.get("NAME")},
                  "geometry": {"type": m["type"], "coordinates": rnd(m["coordinates"])}})
    rp = g.representative_point()
    lx, ly = p.get("LABEL_X"), p.get("LABEL_Y")
    geo[iso] = {"name": p.get("NAME_EN") or p.get("NAME"), "lon": round(lx if lx is not None else rp.x, 3),
                "lat": round(ly if ly is not None else rp.y, 3), "continent": p.get("CONTINENT"),
                "pop": p.get("POP_EST"), "a2": p.get("ISO_A2_EH") or p.get("ISO_A2")}
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(geo, f"{DATA}/countries_geo.json", indent=0)

# ---- admin-1 regions
src = f"{SHM}/adm1.geojson"
if not os.path.exists(src):
    urllib.request.urlretrieve(NE_ADM1_URL, src)
ad = jload(src)

MERGE = {"ESP", "ITA", "FRA", "PRT"}
EN = {  # English names for merged regions (Natural Earth gives local names)
    "Cataluña": "Catalonia", "País Vasco": "Basque Country", "Andalucía": "Andalusia", "Aragón": "Aragon",
    "Castilla y León": "Castile and León", "Castilla-La Mancha": "Castilla-La Mancha", "Valenciana": "Valencian Community",
    "Islas Baleares": "Balearic Islands", "Canary Is.": "Canary Islands", "Foral de Navarra": "Navarre",
    "Asturias": "Asturias", "Galicia": "Galicia", "Cantabria": "Cantabria", "La Rioja": "La Rioja", "Murcia": "Murcia",
    "Extremadura": "Extremadura", "Madrid": "Madrid", "Ceuta": "Ceuta", "Melilla": "Melilla",
    "Piemonte": "Piedmont", "Lombardia": "Lombardy", "Toscana": "Tuscany", "Sicily": "Sicily", "Sicilia": "Sicily",
    "Sardegna": "Sardinia", "Puglia": "Apulia", "Trentino-Alto Adige": "Trentino-South Tyrol", "Valle d'Aosta": "Aosta Valley",
    "Friuli-Venezia Giulia": "Friuli-Venezia Giulia", "Emilia-Romagna": "Emilia-Romagna", "Lazio": "Lazio",
    "Campania": "Campania", "Calabria": "Calabria", "Basilicata": "Basilicata", "Abruzzo": "Abruzzo", "Molise": "Molise",
    "Marche": "Marche", "Umbria": "Umbria", "Liguria": "Liguria", "Veneto": "Veneto",
    "Hauts-de-France": "Hauts-de-France", "Grand Est": "Grand Est", "Provence-Alpes-Côte-d'Azur": "Provence-Alpes-Côte d'Azur",
    "Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine": "Nouvelle-Aquitaine", "Occitanie": "Occitania",
    "Bretagne": "Brittany", "Normandie": "Normandy", "Île-de-France": "Île-de-France", "Pays de la Loire": "Pays de la Loire",
    "Centre-Val de Loire": "Centre-Val de Loire", "Bourgogne-Franche-Comté": "Bourgogne-Franche-Comté", "Corse": "Corsica",
    "Lisbon": "Lisbon", "Norte": "Norte (north)", "Centro": "Centro (centre)", "Alentejo": "Alentejo", "Algarve": "Algarve",
    "Azores": "Azores", "Madeira": "Madeira",
}
groups = {}
for f in ad["features"]:
    p = f["properties"]
    a3 = p["adm0_a3"]
    iso = {"SDS": "SSD", "KOS": "XKX", "SAH": "ESH", "PSX": "PSE"}.get(a3, a3)
    g = shape(f["geometry"])
    if not g.is_valid:
        g = g.buffer(0)
    if a3 in MERGE and p.get("region"):
        reg = p["region"].split(",")[0].strip()
        key = f"{iso}:{reg}"
        name = EN.get(reg, reg)
        if a3 == "FRA" and p.get("type_en") == "Overseas department":
            name = p.get("name_en") or p["name"]
            key = f"{iso}:{name}"
    elif a3 == "GBR":
        nat = p.get("geonunit")
        if nat == "England":
            reg = p.get("region") or "England"
            key, name = f"GBR:{reg}", {"Eastern": "East of England", "East": "East of England"}.get(reg, reg)
        else:
            key, name = f"GBR:{nat}", nat
    else:
        key, name = f"{iso}:{p.get('adm1_code')}", p.get("name_en") or p.get("name")
    gr = groups.setdefault(key, {"iso": iso, "name": name, "type": p.get("type_en"), "geoms": [], "wd": []})
    gr["geoms"].append(g)
    if p.get("wikidataid"):
        gr["wd"].append(p["wikidataid"])
    if a3 in MERGE or a3 == "GBR":
        gr["type"] = "nation" if a3 == "GBR" and not key.startswith("GBR:") else "region"

regions, index = [], []
for key, gr in groups.items():
    g = unary_union(gr["geoms"]) if len(gr["geoms"]) > 1 else gr["geoms"][0]
    area = g.area
    tol = 0.015 if area < 5 else 0.03 if area < 60 else 0.06
    gs = g.simplify(tol, preserve_topology=True)
    if gs.is_empty:
        continue
    rp = g.representative_point()
    m = mapping(gs)
    regions.append({"type": "Feature", "properties": {"k": key, "iso": gr["iso"], "name": gr["name"], "t": gr["type"],
                                                      "lat": round(rp.y, 3), "lon": round(rp.x, 3)},
                    "geometry": {"type": m["type"], "coordinates": rnd(m["coordinates"], 3)}})
    gi = mapping(g.simplify(0.01, preserve_topology=True))
    index.append({"k": key, "iso": gr["iso"], "name": gr["name"], "wd": gr["wd"],
                  "geometry": {"type": gi["type"], "coordinates": rnd(gi["coordinates"], 3)}})
jsave({"type": "FeatureCollection", "features": regions}, f"{WORK}/regions_all.json")
jsave(index, f"{WORK}/adm1_index.json")

c = jload("/home/claude/hist/sun-and-rain/data/cities_page.json")
ix = {k: i for i, k in enumerate(c["cols"])}
rows = sorted(c["rows"], key=lambda r: -(r[ix["pop"]] or 0))[:1500]
cities = [{"name": r[ix["name"]], "lat": round(r[ix["lat"]], 3), "lon": round(r[ix["lon"]], 3), "pop": r[ix["pop"]]} for r in rows]
jsave(cities, f"{DATA}/cities.json")
print(len(feats), "countries;", len(regions), "regions;", os.path.getsize(f"{WORK}/regions_all.json") // 1024, "KB regions;",
      os.path.getsize(f"{WORK}/adm1_index.json") // 1024, "KB index")
