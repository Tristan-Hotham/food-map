"""Shared paths and helpers for the food-map project."""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/home/claude/hist/_data18/food-map"            # raw browser bundles (read in place)
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("FOODTMP", "/dev/shm/food"), "work")   # intermediates live in memory, not in the repo
SHM = os.environ.get("FOODTMP", "/dev/shm/food")      # large downloads kept in memory, not on disk
NE50 = "/home/claude/hist/_data3/ne/geojson/ne_50m_admin_0_countries.geojson"
NE_ADM1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"
for d in (DATA, WORK, SHM):
    os.makedirs(d, exist_ok=True)

DOI = "10.5281/zenodo.23761260"
SLUG = "food-map"
PAGE = "https://maps.tristanhotham.com/food-map/"
REPO = "https://github.com/Tristan-Hotham/food-map"
BLOG = "https://blog.tristanhotham.com/2026/10/29/food-map/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikipedia and Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[\u2013\u2014]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" \u2014 ", ", ").replace("\u2014", ", ").replace(" \u2013 ", ", ").replace("\u2013", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def tsv(text):
    """Parse a QLever TSV result into a list of dicts with plain values."""
    lines = text.rstrip("\n").split("\n")
    head = [h.lstrip("?") for h in lines[0].split("\t")]
    out = []
    for ln in lines[1:]:
        f = ln.split("\t")
        row = {}
        for h, v in zip(head, f + [""] * (len(head) - len(f))):
            v = v.strip()
            if v.startswith("<http://www.wikidata.org/entity/"):
                v = v[len("<http://www.wikidata.org/entity/"):-1]
            elif v.startswith("<") and v.endswith(">"):
                v = v[1:-1]
            else:
                m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
                if m:
                    v = m.group(1).replace('\\"', '"').replace("\\\\", "\\").replace("\\t", " ").replace("\\n", " ")
            row[h] = v
        out.append(row)
    return out


def split(v):
    return [x for x in (v or "").split("|") if x]
