"""Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png, 1520 px wide) and paper figures
(release/paper/f_*.png). World maps use Natural Earth outlines (data/world.json) in the Equal Earth projection."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.lines import Line2D
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape
from common import *

F = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 13, "axes.edgecolor": "#6E665A", "axes.labelcolor": "#24201B",
                     "xtick.color": "#6E665A", "ytick.color": "#6E665A", "hatch.linewidth": 0.9, "hatch.color": "#FFFFFF"})
BG, FG, MUT, LAND, RULE, HOT = "#FAF5EC", "#24201B", "#6E665A", "#ECE4D6", "#E4DACA", "#C2412D"
FAMC = {"meat": "#A8322D", "porridge": "#E0AE2E", "soups": "#D46A25", "rice": "#6B5B95", "fish": "#2F6F8F", "veg": "#6E9F3F",
        "bread": "#B98B57", "noodles": "#3E8E8A", "dumplings": "#7E4B30", "sweets": "#D06A8E", "cheese": "#E9D27E", "drinks": "#8A8A8A", "other": "#A9A29A"}
STYC = {"sweet": "#C77D3A", "bread": "#7A5230", "cooked": "#A8322D", "beans": "#4F7A3A", "rice": "#6B5B95", "porridge": "#E0AE2E", "southasia": "#D9662B", "mezze": "#2F7F8F"}
MEALC = {"midday": "#E09A16", "evening": "#2E3F70", "shifting": "#8C6BB1", "morning": "#F2C979"}
MEALN = {"midday": "Main meal at midday", "evening": "Main meal in the evening", "shifting": "Shifting from midday to evening", "morning": "Most filling meal in the morning"}
REGRAMP = ["#F6E7CF", "#EFCB9C", "#E5A56C", "#D47A48", "#BB4F31", "#8F2F1F"]; RB = [1, 3, 8, 20, 50, 150]
R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json"); W = jload(f"{DATA}/world.json")
CN = SITE["cname"]
REL = os.path.join(ROOT, "release"); os.makedirs(f"{REL}/blog", exist_ok=True); os.makedirs(f"{REL}/paper", exist_ok=True)
tr = Transformer.from_crs(4326, 8857, always_xy=True)
FAMN = SITE["fam"]


def rcol(n):
    k = -1
    for i, b in enumerate(RB):
        if n >= b: k = i
    return REGRAMP[k] if k >= 0 else None


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    ps = []
    for ring in rings(f["geometry"]):
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        ps.append(np.column_stack([x, y]))
    SHAPES.append((f["properties"]["iso"], ps))


def world(ax, colour_of, lw=.35, extent=(-12.5e6, 15.6e6, -6.2e6, 8.4e6)):
    for iso, ps in SHAPES:
        c = colour_of(iso)
        hatch = None
        if isinstance(c, tuple):
            c, hatch = c
        for p in ps:
            ax.add_patch(MPoly(p, closed=True, fc=c or LAND, ec="#FFFFFF", lw=lw, hatch=hatch))
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


natf = lambda iso: FAMC[SITE["nat"][iso]["f"]] if iso in SITE["nat"] else None
BRK = {b["iso3"]: b for b in SITE["brk"]}
MEAL = {m["iso3"]: m for m in SITE["main"]}
brkf = lambda iso: STYC[BRK[iso]["style"]] if iso in BRK else None


def mealf(iso):
    m = MEAL.get(iso)
    if not m or not m["main_meal"]:
        return None
    return (MEALC[m["main_meal"]], "////") if m["regional_statement"] else MEALC[m["main_meal"]]


def legend(fig, items, y, ncol=3, x=.03, fs=11.5):
    h = [Patch(fc=c, ec="none", hatch=ht, label=l) for l, c, ht in items]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=fs, handlelength=1.2,
               handleheight=1.0, columnspacing=1.4, labelspacing=.5)


used = [f for f in FAMC if f in {c["f"] for c in SITE["nat"].values()}]
FAMITEMS = [(FAMN[f], FAMC[f], None) for f in used]
for out in (f"{REL}/blog/b_national_map.png", f"{REL}/paper/f_national_map.png"):
    fig = plt.figure(figsize=(7.6, 5.2), facecolor=BG)
    ax = fig.add_axes([0, .25, 1, .75]); world(ax, natf)
    legend(fig, FAMITEMS, .25, ncol=2, fs=9.6)
    save(fig, out)

STYN = {s["s"]: s["name"] for s in R["breakfast"]["styles"]}
for out in (f"{REL}/blog/b_breakfast_map.png", f"{REL}/paper/f_breakfast_map.png"):
    fig = plt.figure(figsize=(7.6, 5.0), facecolor=BG)
    ax = fig.add_axes([0, .22, 1, .78]); world(ax, brkf)
    legend(fig, [(f"{STYN[s]} ({sum(b['style'] == s for b in SITE['brk'])})", STYC[s], None) for s in STYC], .22, ncol=2, fs=9.6)
    save(fig, out)

for out in (f"{REL}/blog/b_main_meal_map.png", f"{REL}/paper/f_main_meal_map.png"):
    fig = plt.figure(figsize=(7.6, 4.7), facecolor=BG)
    ax = fig.add_axes([0, .17, 1, .83]); world(ax, mealf)
    legend(fig, [(MEALN[k], MEALC[k], None) for k in MEALC] + [("Regional statement (most Arab countries)", MEALC["midday"], "////")], .17, ncol=2, fs=9.6)
    save(fig, out)

# ---------- regional maps: Spain and Portugal; Britain and Ireland ----------
regall = jload(f"{WORK}/regions_all.json")
D = SITE["dishes"]
byreg = {}
for d in D:
    for k in d[4].split("|"):
        byreg.setdefault(k, []).append(d)
for v in byreg.values():
    v.sort(key=lambda d: -d[5])


def regmap(out, isos, ext, label_regs, figsize, lab_n=2, fs=8.2, ctry_ext=None, pick=None, legloc="lower right"):
    fig = plt.figure(figsize=figsize, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    lat0 = (ext[2] + ext[3]) / 2; k = np.cos(np.radians(lat0))
    for f in W["features"]:   # neighbours in plain land
        for ring in rings(f["geometry"]):
            ax.add_patch(MPoly(np.column_stack([ring[:, 0] * k, ring[:, 1]]), closed=True, fc=LAND, ec="#FFFFFF", lw=.6))
    for f in regall["features"]:
        p = f["properties"]
        if p["iso"] not in isos:
            continue
        n = len(byreg.get(p["k"], []))
        for ring in rings(f["geometry"]):
            ax.add_patch(MPoly(np.column_stack([ring[:, 0] * k, ring[:, 1]]), closed=True, fc=rcol(n) or "#F3EEE4", ec="#FFFFFF", lw=.8))
    placed = []
    for f in regall["features"]:
        p = f["properties"]
        if p["iso"] not in isos or p["k"] not in label_regs:
            continue
        L = byreg.get(p["k"], [])
        if not L:
            continue
        lon, lat = label_regs[p["k"]]   # label position (lon, lat), placed by eye over sea or open land
        x, y = lon * k, lat
        names = [d[0] for d in (pick(p["k"], L) if pick else L[:lab_n])]
        txt = f"{p['name']} ({len(L)})\n" + "\n".join(n if len(n) < 24 else n[:22] + "." for n in names)
        ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=FG, linespacing=1.15,
                bbox=dict(boxstyle="round,pad=0.25", fc=(1, 1, 1, .78), ec="none"))
    ax.set_xlim(ext[0] * k, ext[1] * k); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
    ax.legend(handles=[Patch(fc=c, label=(f"{b}" + (f" to {RB[i + 1] - 1}" if i < len(RB) - 1 else " or more"))) for i, (b, c) in enumerate(zip(RB, REGRAMP)) if b <= 60],
              loc=legloc, frameon=False, fontsize=9, title="dishes in region", title_fontsize=9)
    save(fig, out)


ES = {"ESP:Galicia": (-9.9, 43.7), "ESP:Asturias": (-6.6, 44.6), "ESP:Cantabria": (-3.2, 44.6), "ESP:País Vasco": (0.3, 44.6),
      "PRT:Norte": (-10.2, 41.6), "PRT:Lisbon": (-10.4, 38.7), "ESP:Castilla y León": (-4.6, 41.9), "ESP:Madrid": (-3.7, 40.45),
      "ESP:Castilla-La Mancha": (-2.6, 39.2), "ESP:Extremadura": (-6.4, 39.1), "ESP:Andalucía": (-4.6, 37.4), "ESP:Murcia": (0.6, 37.3),
      "ESP:Valenciana": (1.2, 39.5), "ESP:Cataluña": (3.4, 41.3), "ESP:Islas Baleares": (3.9, 38.2), "ESP:Aragón": (-0.8, 41.5)}
spanish_pick = {"ESP:Asturias": ["Fabada asturiana", "Morcilla de Asturias"], "ESP:Galicia": ["polbo á feira", "Caldo galego"],
                "ESP:Valenciana": ["paella", "fideuà"], "ESP:Cataluña": ["crema catalana", "pa amb tomàquet"],
                "ESP:Andalucía": ["gazpacho", "salmorejo"], "ESP:Madrid": ["Cocido madrileño", "Callos a la madrileña"]}


def pick_es(k, L):
    want = spanish_pick.get(k)
    if want:
        got = [d for d in L if d[0] in want]
        if len(got) == len(want):
            return got
    return L[:2]


for out in (f"{REL}/blog/b_spain_regions.png", f"{REL}/paper/f_spain_regions.png"):
    regmap(out, {"ESP", "PRT"}, (-12.6, 5.6, 35.6, 45.3), ES, (7.6, 6.2), pick=pick_es, legloc="lower left")
UKL = {"GBR:Scotland": (-4.0, 57.3), "GBR:Northern Ireland": (-8.9, 55.5), "GBR:North West": (-4.6, 54.15), "GBR:Yorkshire and the Humber": (0.9, 54.5),
       "GBR:Wales": (-5.9, 52.4), "GBR:West Midlands": (-2.0, 52.55), "GBR:East Midlands": (0.2, 53.2), "GBR:South West": (-5.6, 50.15),
       "GBR:Greater London": (1.9, 51.8), "GBR:South East": (0.2, 50.35)}
for out in (f"{REL}/blog/b_uk_regions.png", f"{REL}/paper/f_uk_regions.png"):
    regmap(out, {"GBR", "IRL"}, (-10.8, 3.2, 49.6, 59.0), UKL, (7.6, 9.2), lab_n=3, fs=8.0, legloc="upper left")

# ---------- coverage bar chart ----------
for out in (f"{REL}/blog/b_coverage.png", f"{REL}/paper/f_coverage.png"):
    tc = R["regional"]["top_countries"]
    fig, ax = plt.subplots(figsize=(7.6, 4.6), facecolor=BG); ax.set_facecolor(BG)
    y = np.arange(len(tc))[::-1]
    ax.barh(y, [c["n"] for c in tc], color=HOT, height=.62)
    for yi, c in zip(y, tc):
        fc = R["regional"]["focus"].get(c["iso"])
        ax.text(c["n"] + 6, yi, f"{c['n']}" + (f"  ({fc['regions_with']} of {fc['regions']} regions)" if fc else ""), va="center", fontsize=10.5, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([c["name"] for c in tc], fontsize=11)
    ax.set_xlim(0, max(c["n"] for c in tc) * 1.42); ax.set_xlabel("dishes placed in a region (Wikidata and Wikipedia)", fontsize=10.5)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); save(fig, out)

# ---------- meal times, clock and sun ----------
rows = [m for m in SITE["main"] if not m["regional_statement"] and (m["lunch_mid_clock"] != "" or m["dinner_mid_clock"] != "") and m["clock_ahead_of_sun_min"] != ""]
rows.sort(key=lambda m: -float(m["lunch_mid_sun"] if m["lunch_mid_sun"] != "" else m["dinner_mid_sun"]))
for out in (f"{REL}/blog/b_meal_times.png", f"{REL}/paper/f_meal_times.png"):
    fig, ax = plt.subplots(figsize=(7.6, 7.4), facecolor=BG); ax.set_facecolor(BG)
    for i, m in enumerate(rows):
        for kk, c in (("lunch", MEALC["midday"]), ("dinner", MEALC["evening"])):
            cl, sn = m[kk + "_mid_clock"], m[kk + "_mid_sun"]
            if cl == "" or sn == "":
                continue
            ax.plot([float(cl), float(sn)], [i, i], color=c, lw=1.8, alpha=.6)
            ax.scatter([float(cl)], [i], s=34, facecolor=BG, edgecolor=c, lw=1.8, zorder=3)
            ax.scatter([float(sn)], [i], s=40, color=c, zorder=4)
    ax.axvline(12, color="#D99A1E", ls="--", lw=1.4)
    ax.text(12.08, len(rows) - .3, "solar noon", fontsize=9.5, color=MUT, va="bottom")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([CN.get(m["iso3"], m["iso3"]) for m in rows], fontsize=10.5)
    for t, m in zip(ax.get_yticklabels(), rows):
        if m["iso3"] == "ESP": t.set_fontweight("bold")
    ax.set_xlim(10, 23); ax.set_xticks(range(10, 24, 2)); ax.set_xticklabels([f"{h}:00" for h in range(10, 24, 2)], fontsize=10)
    ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", mfc=BG, mec=FG, label="clock time"), Line2D([], [], marker="o", ls="", color=FG, label="sun time"),
                       Line2D([], [], color=MEALC["midday"], lw=3, label="lunch"), Line2D([], [], color=MEALC["evening"], lw=3, label="dinner")],
              loc="center", bbox_to_anchor=(.62, .74), fontsize=9.5, frameon=False)
    fig.tight_layout(); save(fig, out)

# ---------- families bar (paper) ----------
ff = R["national"]["family_first"]
fig, ax = plt.subplots(figsize=(7.6, 4.4), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(ff))[::-1]
ax.barh(y, [f["n"] for f in ff], color=[FAMC[f["f"]] for f in ff], height=.65)
for yi, f in zip(y, ff):
    ax.text(f["n"] + .6, yi, f"{f['n']} ({f['share'] * 100:.0f}%)", va="center", fontsize=10)
ax.set_yticks(y); ax.set_yticklabels([f["name"] for f in ff], fontsize=10)
ax.set_xlim(0, ff[0]["n"] * 1.25); ax.set_xlabel("countries and territories (first-listed national dish)", fontsize=10)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); save(fig, f"{REL}/paper/f_families.png")

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.33, .04, .68, .92]); world(ax, natf, lw=.3, extent=(-12.5e6, 15.6e6, -6.0e6, 8.4e6))
fig.text(.04, .88, "What does the", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(.04, .74, "world eat?", fontproperties=DISP, fontsize=54, color=HOT, va="top")
fig.text(.04, .52, f"National dishes for {R['national']['n_countries']} countries\nand territories, breakfast styles,\n{R['regional']['n_dishes']:,} regional dishes and\nthe main meal of the day.", family=SER, fontsize=16, color=FG, va="top", linespacing=1.3)
fig.text(.04, .22, "Map: family of each country's\nfirst-listed national dish", family=MONO, fontsize=11.5, color=MUT, va="top", linespacing=1.3)
fig.text(.04, .06, "maps.tristanhotham.com/food-map", family=MONO, fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
print("figures done")
