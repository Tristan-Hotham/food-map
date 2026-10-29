"""r/dataisbeautiful collage for 'What does the world eat?' (2400 x 3000 px). Run from anywhere: python3 reddit/collage.py"""
import json, os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.lines import Line2D
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); D = os.path.join(ROOT, "data")
F = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, HOT, OLV = "#FCF4E2", "#2A211B", "#73685A", "#EDE2CC", "#C2412D", "#5E7A2E"   # butter-cream tablecloth
R = json.load(open(os.path.join(D, "results.json"))); S = json.load(open(os.path.join(D, "site.json"))); W = json.load(open(os.path.join(D, "world.json")))
G = json.load(open(os.path.join(D, "countries_geo.json")))
FAMC = {"meat": "#A8322D", "porridge": "#E0AE2E", "soups": "#D46A25", "rice": "#6B5B95", "fish": "#2F6F8F", "veg": "#6E9F3F",
        "bread": "#B98B57", "noodles": "#3E8E8A", "dumplings": "#7E4B30", "sweets": "#D06A8E", "cheese": "#E9D27E", "drinks": "#8A8A8A", "other": "#A9A29A"}
STYC = {"sweet": "#C77D3A", "bread": "#7A5230", "cooked": "#A8322D", "beans": "#4F7A3A", "rice": "#6B5B95", "porridge": "#E0AE2E", "southasia": "#D9662B", "mezze": "#2F7F8F"}
MEALC = {"midday": "#E09A16", "evening": "#2E3F70", "shifting": "#8C6BB1", "morning": "#F2C979"}
tr = Transformer.from_crs(4326, 8857, always_xy=True)
plt.rcParams["hatch.linewidth"] = 1.0; plt.rcParams["hatch.color"] = "#FFFFFF"
BRK = {b["iso3"]: b for b in S["brk"]}; MEAL = {m["iso3"]: m for m in S["main"]}


def draw_world(ax, col, lw=.4, ext=(-12.3e6, 15.8e6, -5.6e6, 8.0e6)):
    for f in W["features"]:
        iso = f["properties"]["iso"]; c = col(iso); hatch = None
        if isinstance(c, tuple): c, hatch = c
        g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in cs:
            a = np.array(poly[0]); x, y = tr.transform(np.clip(a[:, 0], -179.9, 179.9), a[:, 1])
            ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=c or LAND, ec=BG, lw=lw, hatch=hatch))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(.045, .972, "What does the world eat?", fontproperties=DISP, fontsize=56, color=FG, va="top")
fig.text(.045, .915, f"Each country's first-listed national dish on Wikipedia, coloured by kind of dish ({R['national']['n_countries']} countries\nand territories), with breakfasts, regional dishes and the main meal of the day below.",
         family=SER, fontsize=16, color=FG, va="top", linespacing=1.35)

# ---------- hero: national dishes with names ----------
ax = fig.add_axes([0, .505, 1, .345]); draw_world(ax, lambda i: FAMC[S["nat"][i]["f"]] if i in S["nat"] else None)
LBL = {  # country: (label lon, lat) where the name is written; a short line joins it to the country
    "USA": (-112, 33), "CAN": (-100, 58), "MEX": (-113, 18), "BRA": (-48, -8), "ARG": (-82, -38), "PER": (-95, -10),
    "GBR": (-37, 60.5), "ESP": (-34, 40), "FRA": (-31, 47.5), "ITA": (-12, 30.5), "DEU": (-26, 52.5), "SWE": (-6, 70),
    "UKR": (26, 63), "RUS": (78, 64), "TUR": (24, 31.5), "EGY": (11, 21), "MAR": (-28, 27), "NGA": (-14, 7),
    "ETH": (58, 4), "KEN": (58, -6), "ZAF": (36, -36), "IND": (64, 12), "CHN": (104, 33), "JPN": (156, 41), "KOR": (150, 30),
    "THA": (86, 5), "IDN": (107, -14), "PHL": (140, 13), "AUS": (134, -24), "IRN": (55, 38), "SAU": (35, 15), "HUN": (40, 52), "MNG": (100, 52)}
for iso, (lo, la) in LBL.items():
    d = S["nat"][iso]["l"][0]["d"]
    x, y = tr.transform(lo, la); cx, cy = tr.transform(G[iso]["lon"], G[iso]["lat"])
    inside = abs(lo - G[iso]["lon"]) < 1 and abs(la - G[iso]["lat"]) < 1
    if not (abs(lo - G[iso]["lon"]) < 6 and abs(la - G[iso]["lat"]) < 6):
        ax.plot([cx, x], [cy, y], color=FG, lw=.7, alpha=.75, zorder=5)
        ax.scatter([cx], [cy], s=7, color=FG, zorder=6)
    ax.text(x, y, d, ha="center", va="center", fontsize=9.6, color=FG, family=MONO, zorder=7,
            bbox=dict(boxstyle="round,pad=0.18", fc=(1, 1, 1, .82), ec="none"))
used = [f for f in FAMC if f in {c["f"] for c in S["nat"].values()} and f not in ("other", "drinks")]
NAMES = {"meat": "Meat and grills", "porridge": "Starchy staples", "soups": "Soups, stews, curries", "rice": "Rice dishes", "fish": "Fish and seafood",
         "veg": "Beans, veg and eggs", "bread": "Breads and pancakes", "noodles": "Noodles and pasta", "dumplings": "Dumplings and pies", "sweets": "Sweets", "cheese": "Cheese"}
fam_n = {f["f"]: f["n"] for f in R["national"]["family_first"]}
fig.legend(handles=[Patch(fc=FAMC[f], label=f"{NAMES[f]} {fam_n[f]}") for f in used], loc="upper left", bbox_to_anchor=(.04, .512), ncol=4, frameon=False,
           fontsize=11.2, handlelength=1.1, columnspacing=1.2, labelspacing=.45)

# ---------- big numbers ----------
NUM = [(f"{R['regional']['n_dishes']:,}", HOT, f"dishes placed in\n{R['regional']['n_regions']} regions, from\nfabada in Asturias\nto takoyaki in Osaka"),
       (f"{R['breakfast']['europe']['bread']} v {R['breakfast']['europe']['sweet']}", "#7A5230", f"European breakfasts:\nbread and cheese v\ncoffee and something\nsweet (Italy, Spain...)"),
       ("0", "#2E3F70", f"Wikidata foods tagged\nlunch or dinner, v\n{R['main_meal']['wd_main_items']} main courses: so\nno lunch map"),
       (R["spain"]["lunch_sun"], "#E09A16", f"Spain's 2 pm lunch,\nby the sun: clocks\nrun {round(R['spain']['ahead_min'])} minutes\nahead of the sun")]
for k, (big, c, txt) in enumerate(NUM):
    x = .045 + k * .235
    fig.text(x, .455, big, fontproperties=DISP, fontsize=40, color=c, va="top")
    fig.text(x, .408, txt, family=MONO, fontsize=11, color=FG, va="top", linespacing=1.22)

# ---------- small multiples ----------
fig.text(.045, .342, "Breakfast style", fontproperties=DISP, fontsize=19, color=FG, va="top")
a1 = fig.add_axes([.02, .205, .47, .11]); draw_world(a1, lambda i: STYC[BRK[i]["style"]] if i in BRK else None, lw=.25, ext=(-12.3e6, 15.8e6, -5.4e6, 7.9e6))
SN = {"sweet": "Coffee and something sweet", "bread": "Bread, cheese, cold meats", "cooked": "Cereal or a fry-up", "beans": "Eggs, beans, tortillas",
      "rice": "Rice, soup, sides", "porridge": "Porridge, congee, buns", "southasia": "Flatbreads and curries", "mezze": "Flatbread, cheese, olives"}
fig.legend(handles=[Patch(fc=STYC[s], label=SN[s]) for s in STYC], loc="upper left", bbox_to_anchor=(.035, .205), ncol=2, frameon=False, fontsize=9.4,
           handlelength=1.0, columnspacing=.8, labelspacing=.35)
fig.text(.53, .342, "Main meal of the day", fontproperties=DISP, fontsize=19, color=FG, va="top")


def mcol(i):
    m = MEAL.get(i)
    if not m or not m["main_meal"]: return None
    return (MEALC[m["main_meal"]], "////") if m["regional_statement"] else MEALC[m["main_meal"]]


a2 = fig.add_axes([.51, .205, .47, .11]); draw_world(a2, mcol, lw=.25, ext=(-12.3e6, 15.8e6, -5.4e6, 7.9e6))
MN = {"midday": f"Midday ({R['main_meal']['counts']['midday']})", "evening": f"Evening ({R['main_meal']['counts']['evening']})",
      "shifting": f"Shifting to evening ({R['main_meal']['counts']['shifting']})", "morning": "Morning (1)"}
fig.legend(handles=[Patch(fc=MEALC[k], label=MN[k]) for k in MEALC] + [Patch(fc=MEALC["midday"], hatch="////", label="Regional statement")],
           loc="upper left", bbox_to_anchor=(.525, .205), ncol=2, frameon=False, fontsize=9.4, handlelength=1.0, columnspacing=.8, labelspacing=.35)

# clock versus sun strip
ax3 = fig.add_axes([.10, .08, .86, .042]); ax3.set_facecolor(BG)
rows = [m for m in S["main"] if m["iso3"] in ("ESP", "GBR", "USA", "FRA", "MEX") and m["clock_ahead_of_sun_min"] != ""]
order = ["ESP", "FRA", "GBR", "USA", "MEX"]; rows.sort(key=lambda m: order.index(m["iso3"]))
CNs = {"ESP": "Spain", "FRA": "France", "GBR": "UK", "USA": "US", "MEX": "Mexico"}
for i, m in enumerate(rows[::-1]):
    for kk, c in (("lunch", MEALC["midday"]), ("dinner", MEALC["evening"])):
        cl, sn = m[kk + "_mid_clock"], m[kk + "_mid_sun"]
        if cl == "" or sn == "": continue
        ax3.plot([float(cl), float(sn)], [i, i], color=c, lw=1.6, alpha=.6)
        ax3.scatter([float(cl)], [i], s=26, facecolor=BG, edgecolor=c, lw=1.5, zorder=3); ax3.scatter([float(sn)], [i], s=30, color=c, zorder=4)
    ax3.text(10.85, i, CNs[m["iso3"]], ha="right", va="center", fontsize=9.6, color=FG, fontweight="bold" if m["iso3"] == "ESP" else "normal")
ax3.axvline(12, color="#D99A1E", ls="--", lw=1.2)
ax3.set_xlim(11, 22.5); ax3.set_ylim(-.6, len(rows) - .4); ax3.set_yticks([])
ax3.set_xticks(range(12, 23, 2)); ax3.set_xticklabels([f"{h}:00" for h in range(12, 23, 2)], fontsize=9.4, color=MUT)
for s in ("top", "right", "left"): ax3.spines[s].set_visible(False)
ax3.spines["bottom"].set_color(MUT)
fig.text(.045, .143, "Lunch and dinner on the clock (hollow) and by the sun (solid)", fontproperties=DISP, fontsize=15, color=FG, va="top")

# footer
fig.text(.045, .028, "Sources: English Wikipedia 'National dish', 'Breakfast by country', 'Lunch', 'Dinner' and cuisine articles (CC BY-SA 4.0); Wikidata (CC0) via QLever;\n"
         "Natural Earth; clock offsets from maps.tristanhotham.com/clock-vs-sun. Lists are claims, not surveys; regional coverage is uneven.",
         family=MONO, fontsize=8.8, color=MUT, va="bottom", linespacing=1.4)
fig.text(.045, .012, "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/food-map", family=MONO, fontsize=9.4, color=FG, va="bottom")
out = os.path.join(HERE, "what_the_world_eats.png")
fig.savefig(out, dpi=200, facecolor=BG); plt.close(fig)
print(out)
