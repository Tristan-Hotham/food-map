"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (site.json, world.json, cities) is embedded; data/regions.json is loaded by the page on use.
Facts stated in words are checked here."""
import json, re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "f1": return f"{v:.1f}"
    if f == "len": return str(len(v))
    if f == "list": return ", ".join(v[:-1]) + " and " + v[-1] if len(v) > 1 else v[0]
    raise ValueError(f)


# facts stated in words in the page
mm = {m["iso3"]: m["main_meal"] for m in SITE["main"]}
for i in ("ESP", "PRT", "GRC", "MEX", "BRA", "ARG", "POL", "RUS", "EGY", "IDN"):
    assert mm[i] == "midday", i
for i in ("GBR", "USA", "CAN", "SWE", "FIN", "IND", "ITA"):
    assert mm[i] == "evening", i
for i in ("DEU", "AUT", "SVK"):
    assert mm[i] == "shifting", i
fam = {i: c["f"] for i, c in SITE["nat"].items()}
for i, f in (("ARG", "meat"), ("AUT", "meat"), ("CHN", "meat"), ("TUR", "meat"), ("GHA", "porridge"), ("ZMB", "porridge"),
             ("ZWE", "porridge"), ("KEN", "porridge"), ("ROU", "porridge"), ("BEL", "porridge"), ("UZB", "rice"), ("BHR", "rice"), ("QAT", "rice")):
    assert fam[i] == f, (i, fam[i])
assert [x["f"] for x in R["national"]["family_first"][:4]] == ["meat", "porridge", "soups", "rice"]
brk = {b["iso3"]: b["style"] for b in SITE["brk"]}
for i in ("GBR", "IRL", "USA", "CAN", "AUS", "NZL"):
    assert brk[i] == "cooked"
for i in ("JPN", "KOR", "IDN", "PHL"):
    assert brk[i] == "rice"
for i in ("TUR", "IRN", "EGY"):
    assert brk[i] == "mezze"
ex = R["regional"]["examples"]
assert ex["Fabada asturiana"] == "Asturias" and ex["paella"] == "Valencian Community" and ex["Caldo galego"] == "Galicia"
assert R["regional"]["spain"][0]["name"] == "Catalonia" and R["regional"]["spain"][1]["name"] == "Andalusia"
assert {"crema catalana", "pa amb tomàquet", "fuet"} <= set(R["regional"]["spain"][0]["d"])
uk = {u["name"]: u["d"] for u in R["regional"]["uk"]}
assert R["regional"]["uk"][0]["name"] == "South West" and R["regional"]["uk"][1]["name"] == "Scotland"
assert {"Eccles cake", "Lancashire hotpot", "Kendal Mint Cake"} <= set(uk["North West"])
assert {"Yorkshire pudding", "Pontefract cake"} <= set(uk["Yorkshire and the Humber"])
assert R["regional"]["focus"]["JPN"]["regions_with"] == R["regional"]["focus"]["JPN"]["regions"]
assert R["main_meal"]["wd_lunch_items"] == 0 and R["main_meal"]["wd_dinner_items"] == 0
assert {x["name"] for x in R["times"]["latest_sun"]} <= {"Poland", "Mexico"} and mm["POL"] == mm["MEX"] == "midday"
assert R["national"]["shared"][0]["dish"] == "Ugali" and R["national"]["shared"][1]["dish"] == "Couscous"

if __name__ == "__main__":
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), tpl)
    assert "{{" not in html
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")
