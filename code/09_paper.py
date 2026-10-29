"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex."""
import re, shutil, subprocess
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_What_Does_the_World_Eat"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "list": return tex(", ".join(v[:-1]) + " and " + v[-1])
    return tex(str(v))


CN = SITE["cname"]
ex = {}
for i, c in SITE["nat"].items():
    ex.setdefault(c["f"], []).append(c["l"][0]["d"])
rows = "".join(f"{tex(f['name'])} & {f['n']} & {f['share'] * 100:.0f}\\% & {tex(', '.join(sorted(set(ex.get(f['f'], [])))[:5]))}\\\\\n" for f in R["national"]["family_first"])
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{Families of the first-listed national dish, with examples.}\\label{tab:fam}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{4.4cm}rr>{\\raggedright\\arraybackslash}p{7.2cm}}\\toprule Family & Countries & Share & Examples\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
EVN = [("place", "A place in a Wikidata location property"), ("origin", "Sub-national country of origin"), ("cuisine", "Regional cuisine (Wikidata)"),
       ("cat", "Wikipedia regional cuisine category"), ("name", "Place named in the English name")]
rows = "".join(f"{tex(n)} & {R['regional']['evidence'][k]:,} & {R['regional']['evidence'][k] / R['regional']['n_dishes'] * 100:.0f}\\%\\\\\n" for k, n in EVN)
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{Strongest evidence used to place each dish in a region.}\\label{tab:ev}"
      "\\begin{tabular}{lrr}\\toprule Evidence & Dishes & Share\\\\\\midrule\n" + rows + f"\\midrule All placed dishes & {R['regional']['n_dishes']:,} & 100\\%\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
hm = lambda h: "" if h == "" else f"{int(round(float(h) * 60)) // 60}:{int(round(float(h) * 60)) % 60:02d}"
MM = {"midday": "midday", "evening": "evening", "shifting": "shifting", "morning": "morning", "": ""}
tm = [m for m in SITE["main"] if not m["regional_statement"] and (m["lunch_mid_clock"] != "" or m["dinner_mid_clock"] != "") and m["clock_ahead_of_sun_min"] != ""]
tm.sort(key=lambda m: CN.get(m["iso3"], m["iso3"]))
rows = "".join(f"{tex(CN.get(m['iso3'], m['iso3']))} & {MM[m['main_meal']]} & {hm(m['lunch_mid_clock'])} & {hm(m['lunch_mid_sun'])} & {hm(m['dinner_mid_clock'])} & {hm(m['dinner_mid_sun'])} & {float(m['clock_ahead_of_sun_min']):.0f}\\\\\n" for m in tm)
TT = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Stated meal times (middle of the window) on the clock and by the sun, and the country's mean lead of clock over sun in minutes.}\\label{tab:times}"
      "\\begin{tabular}{llrrrrr}\\toprule Country & Main meal & Lunch clock & Lunch sun & Dinner clock & Dinner sun & Lead\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_FAM}}", TF).replace("{{TABLE_EV}}", TE).replace("{{TABLE_TIMES}}", TT)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words; dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
