"""Dish families from the Wikidata class tree (subclass of), with a text fallback for items outside the food tree."""
from common import *

cl = jload(f"{WORK}/classes.json")
edges = cl["edges"]
FAM = [("rice", ["Q21976260"]), ("noodles", ["Q192874", "Q98826752", "Q178", "Q2625877"]),
       ("dumplings", ["Q1854639", "Q13360264", "Q138859370", "Q138860055", "Q477248", "Q5503624"]),
       ("soups", ["Q41415", "Q107289424", "Q2920963", "Q6501890", "Q164606"]),
       ("fish", ["Q18679149", "Q11559422", "Q28100907"]),
       ("meat", ["Q1427844", "Q28100368", "Q27994917", "Q18697490", "Q28100020", "Q98163379", "Q179010", "Q1323569", "Q17062980", "Q131419"]),
       ("bread", ["Q7802", "Q666242", "Q44541", "Q123459407", "Q28803", "Q111836983"]),
       ("porridge", ["Q186817", "Q10514020"]),
       ("veg", ["Q84431525", "Q125302741", "Q125246075", "Q28100194", "Q9266"]),
       ("sweets", ["Q182940", "Q13276", "Q12048097", "Q13270", "Q13266", "Q47505416", "Q5159627", "Q56250611", "Q9053", "Q2382369", "Q185583"]),
       ("cheese", ["Q10943"]),
       ("drinks", ["Q40050", "Q178359", "Q2596997"])]
FAMQ = {q: f for f, qs in FAM for q in qs}
FAMORDER = [f for f, _ in FAM]
anc_cache = {}


def ancestors(q, depth=0):
    if q in anc_cache:
        return anc_cache[q]
    anc_cache[q] = set()
    out = {q}
    if depth < 25:
        for b in edges.get(q, []):
            out |= ancestors(b, depth + 1)
    anc_cache[q] = out
    return out


def family(it, q):
    a = set(ancestors(q))
    for t in it["p31"]:
        a |= ancestors(t)
    hits = {FAMQ[x] for x in a if x in FAMQ}
    for f in FAMORDER:
        if f in hits:
            return f
    k = it["kinds"]
    return {"bread": "bread", "cheese": "cheese", "sausage": "meat", "pastry": "dumplings", "dessert": "sweets"}.get(k[0], "other") if k else "other"




TEXT = [("rice", r"\b(rice|pilaf|pilau|plov|biryani|risotto|paella|palaw|pulao|jollof)\b"),
        ("noodles", r"\b(noodle|pasta|ramen|spaghetti|pho|laksa)\b"),
        ("dumplings", r"\b(dumpling|pie|pastry|pasties|empanada|turnover|pierogi|momo|varenyky|burek|samosa)\b"),
        ("soups", r"\b(soup|stew|broth|curry|chowder|casserole|goulash|borscht)\b"),
        ("fish", r"\b(fish|seafood|herring|cod|crab|shrimp|prawn|octopus|eel|salmon|tuna|ceviche)\b"),
        ("meat", r"\b(meat|beef|pork|lamb|mutton|chicken|goat|sausage|kebab|barbecue|roast|steak|duck|ham|bacon)\b"),
        ("bread", r"\b(bread|flatbread|pancake|sandwich|crepe|tortilla|taco|bun|roll|toast)\b"),
        ("porridge", r"\b(porridge|fufu|ugali|nshima|sadza|polenta|mash|potato|cassava|plantain|maize|cornmeal)\b"),
        ("veg", r"\b(salad|vegetable|bean|lentil|chickpea|egg|tofu)\b"),
        ("sweets", r"\b(dessert|cake|sweet|pudding|biscuit|cookie|confection|candy|custard|tart)\b"),
        ("cheese", r"\b(cheese)\b"),
        ("drinks", r"\b(drink|beverage|wine|whisky|whiskey|beer|tea|coffee|spirit|liquor|sauce|condiment)\b")]


def family_from_text(t):
    import re
    t = t.lower()
    for f, rx in TEXT:
        if re.search(rx, t):
            return f
    return "other"
