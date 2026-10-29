"""Breakfast styles and the main meal of the day, coded by hand from English Wikipedia text.

Breakfast: one style per country from the article 'Breakfast by country' (each country's own section; the short food
lists are my summaries of the foods that section names). Main meal and meal times: what the cuisine articles and the
articles 'Lunch' and 'Dinner' state in words; a country is coded only when a sentence says which meal is the main or
largest one, or gives clock times. Clock times are turned into sun time with the clock-vs-sun project's
population-weighted offset between clock and sun for each country (annual mean, daylight saving included).
Also counts Wikidata dishes whose 'course' (P8431) is breakfast or main course.
Outputs: data/breakfast.csv, data/main_meal.csv, work/meals.json
"""
import csv, collections
from common import *

geo = jload(f"{DATA}/countries_geo.json")
BW = "https://en.wikipedia.org/wiki/Breakfast_by_country"

STYLES = {
    "sweet": "Coffee or tea with bread and something sweet",
    "bread": "Bread with cheese, cold meats and spreads",
    "cooked": "Cereal and toast, or a cooked fry-up",
    "beans": "Eggs, beans, tortillas and plantain",
    "rice": "Rice, soup and savoury sides",
    "porridge": "Porridge, congee, buns and fritters",
    "southasia": "Flatbreads, rice cakes and curries",
    "mezze": "Flatbread with beans, cheese, eggs and olives",
}
# iso3, style, section of 'Breakfast by country', foods named there (my short list)
B = [
    ("DZA", "sweet", "Algeria", "milky coffee, croissants and pastries, date-filled bread"),
    ("EGY", "mezze", "Egypt", "ful medames, taameya (falafel), flatbread, cheeses, eggs"),
    ("MWI", "porridge", "Malawi", "porridge, cornbread, fritters, boiled sweet potato, sweet tea"),
    ("MAR", "mezze", "Morocco", "bread, harcha, msemen with olive oil, mint tea"),
    ("NGA", "porridge", "Nigeria", "ogi or koko porridge with akara or moi moi bean cakes"),
    ("SEN", "sweet", "Senegal", "café Touba, baguette with spreads, small beignets, fruit"),
    ("SOM", "mezze", "Somalia", "canjeero flatbread with stew, honey or ghee, spiced tea"),
    ("TUN", "mezze", "Tunisia", "lablabi chickpea soup, or baguette with butter and jam"),
    ("UGA", "porridge", "Uganda", "maize or millet porridge, katogo (green bananas in sauce)"),
    ("BGD", "southasia", "Bangladesh", "roti or paratha with vegetable curry, dal or eggs, tea"),
    ("CHN", "porridge", "China", "congee, youtiao, steamed buns, noodles, soy milk"),
    ("IND", "southasia", "India", "idli, dosa and sambar in the south; paratha and curry in the north"),
    ("IDN", "rice", "Indonesia", "bubur ayam (chicken congee), nasi uduk, nasi goreng"),
    ("IRN", "mezze", "Iran", "flatbreads with white cheese, butter, jam or honey, tea; haleem"),
    ("ISR", "mezze", "Israel", "eggs, cheeses, chopped salad, bread, hummus, shakshouka"),
    ("JPN", "rice", "Japan", "steamed rice, miso soup, pickles, grilled fish, egg"),
    ("KOR", "rice", "Korea", "rice, soup or stew, kimchi and other banchan"),
    ("LBN", "mezze", "Levant", "manakish flatbread"),
    ("SYR", "mezze", "Levant", "manakish flatbread"),
    ("JOR", "mezze", "Levant", "manakish flatbread"),
    ("PSE", "mezze", "Levant", "manakish flatbread"),
    ("MYS", "rice", "Malaysia and Singapore", "nasi lemak, roti canai, kaya toast, teh tarik"),
    ("SGP", "rice", "Malaysia and Singapore", "nasi lemak, roti prata, kaya toast with soft eggs, kopi"),
    ("MMR", "rice", "Myanmar", "mohinga fish noodle soup, fried rice with peas, sticky rice"),
    ("PAK", "southasia", "Pakistan", "paratha and omelette, nihari, halwa puri, milky tea"),
    ("PHL", "rice", "Philippines", "garlic fried rice and egg (silog) with tapa or tocino; pandesal"),
    ("TWN", "porridge", "Taiwan", "shaobing and youtiao with soy milk, scallion pancake, congee"),
    ("ALB", "bread", "Albania", "scone or bread, eggs, cheese, jam, milk or tea"),
    ("HRV", "bread", "Croatia", "pastries, cold cuts, cheese, yogurt, eggs"),
    ("DNK", "bread", "Denmark", "rye bread with cheese, soft-boiled egg, cereal or yogurt"),
    ("FIN", "bread", "Finland", "open sandwiches with cheese or cold cuts, porridge, yogurt"),
    ("FRA", "sweet", "France", "tartines with butter and jam, croissants, café au lait"),
    ("DEU", "bread", "Germany and Austria", "bread rolls, butter, jam, ham, cheese, boiled eggs"),
    ("AUT", "bread", "Germany and Austria", "bread rolls, butter, jam, ham, cheese, boiled eggs"),
    ("GRC", "sweet", "Greece", "bread with butter and honey, coffee; tyropita or bougatsa"),
    ("HUN", "bread", "Hungary", "open sandwiches with cold cuts, sausage, cheese spreads, peppers"),
    ("ISL", "bread", "Iceland", "bread and coffee, skyr with cereal, oatmeal porridge"),
    ("ITA", "sweet", "Italy", "caffè latte or cappuccino with a cornetto, biscotti or rusks"),
    ("LVA", "bread", "Latvia", "open sandwiches, curd, oat porridge, coffee"),
    ("MLT", "sweet", "Malta", "cereal, bread with jam, pastizzi, coffee or tea"),
    ("NLD", "bread", "Netherlands and Belgium", "sliced bread with cheese, cold meats or hagelslag"),
    ("BEL", "bread", "Netherlands and Belgium", "sliced bread with cheese, cold meats or chocolate"),
    ("NOR", "bread", "Norway", "open sandwiches with brunost, cold cuts, mackerel in tomato"),
    ("POL", "bread", "Poland", "bread with cold cuts, twaróg cheese, eggs, pickles"),
    ("ROU", "bread", "Romania", "bread with butter and honey or jam, or cured meats and cheese"),
    ("RUS", "porridge", "Russia", "kasha (buckwheat, oat or semolina porridge), blini, syrniki"),
    ("SRB", "bread", "Serbia", "eggs, open sandwiches, kajmak, burek or gibanica"),
    ("ESP", "sweet", "Spain", "coffee with biscuits, magdalenas or toast; churros at weekends; pan con tomate on the coasts"),
    ("SWE", "bread", "Sweden", "open sandwiches on crispbread, cheese, smörgåskaviar, filmjölk"),
    ("CHE", "bread", "Switzerland", "zopf bread on Sundays, muesli"),
    ("TUR", "mezze", "Turkey", "bread, white cheese, olives, tomatoes, eggs, menemen, tea"),
    ("GBR", "cooked", "United Kingdom and Ireland", "cereal or toast in the week; a full breakfast at weekends"),
    ("IRL", "cooked", "United Kingdom and Ireland", "cereal or toast in the week; a full breakfast at weekends"),
    ("CAN", "cooked", "Canada", "eggs, bacon or peameal bacon, pancakes with maple syrup, toast"),
    ("CRI", "beans", "Costa Rica", "gallo pinto (rice and beans) with eggs, cheese and plantain"),
    ("CUB", "sweet", "Cuba", "café con leche with buttered Cuban bread"),
    ("DOM", "beans", "Dominican Republic", "mangú (mashed plantain), eggs, cheese"),
    ("SLV", "beans", "El Salvador", "eggs, refried beans, fried plantain, cheese, tortillas"),
    ("GTM", "beans", "Guatemala", "eggs, black beans, fried plantain, cream and cheese"),
    ("HND", "beans", "Honduras", "beans, eggs, plantain, tortillas; baleadas"),
    ("JAM", "beans", "Jamaica", "ackee and saltfish, callaloo, boiled green bananas, fried dumplings"),
    ("MEX", "beans", "Mexico", "huevos rancheros, chilaquiles, tamales, quesadillas"),
    ("NIC", "beans", "Nicaragua", "gallo pinto, eggs, cheese, corn tortillas, sweet plantain"),
    ("PAN", "beans", "Panama", "corn tortillas, white cheese, eggs, beef or liver, plantain"),
    ("PRI", "cooked", "Puerto Rico", "pancakes, eggs, revoltillo, pan de agua with coffee"),
    ("USA", "cooked", "United States", "cereal or oatmeal in the week; eggs, bacon, pancakes at weekends"),
    ("AUS", "cooked", "Australia", "cereal with milk, toast with Vegemite; a cooked breakfast at weekends"),
    ("FJI", "sweet", "Fiji", "sweet tea with fried dough, pancakes or bread; roti and curry"),
    ("NZL", "cooked", "New Zealand", "cereal, porridge in winter, toast; a 'big breakfast' in cafés"),
    ("ARG", "sweet", "Argentina", "toast with dulce de leche or jam, medialunas, milky coffee"),
    ("BRA", "bread", "Brazil", "bread, butter, cheese, ham, fruit, pão de queijo, coffee"),
    ("URY", "sweet", "Uruguay", "mate with torta frita or bizcochos"),
    ("CHL", "sweet", "Chile", "toast with jam or butter, pan con palta, tea or coffee"),
]
assert len({b[0] for b in B}) == len(B)

# main meal: iso3, main ('midday', 'evening', 'shifting', 'morning'), lunch window, dinner window, source, note
WP = "https://en.wikipedia.org/wiki/"
M = [
    ("ALB", "midday", None, None, "Albanian cuisine", "Lunch is traditionally the biggest meal; supper is smaller."),
    ("ARG", "midday", (12, 14), None, "Lunch", "Lunch is usually the main meal, between noon and 2 pm."),
    ("AUT", "shifting", None, None, "Austrian cuisine", "The midday meal was the main meal; it is now often eaten in the evening."),
    ("BOL", "midday", (12, 14), (20, 21), "Bolivian cuisine", "Long lunches, shops close 12 to 2 pm; dinner is lighter, at 8 pm or later."),
    ("BIH", "midday", (14, 14), None, "Lunch", "Lunch is the day's main meal, normally around 2 pm."),
    ("BRA", "midday", (11.5, 14), None, "Lunch", "Lunch is the main meal, between 11.30 am and 2 pm."),
    ("BGR", None, (12, 14), None, "Lunch", "Lunch is normally between noon and 2 pm."),
    ("CAN", "evening", (12, 12), (17, 19), "Canadian cuisine", "Lunch around noon; dinner between 5 and 7 pm and heartier."),
    ("TCD", "evening", None, None, "Chadian cuisine", "The day's main meal is typically eaten in the evening."),
    ("CHN", None, (12, 14), (18, 21), "Chinese cuisine", "Breakfast 6 to 9 am, lunch 12 to 2 pm, dinner 6 to 9 pm."),
    ("DNK", "evening", None, None, "Danish cuisine", "The evening meal is still sometimes called middag, as hot meals were once eaten at midday."),
    ("ECU", "midday", None, None, "Latin American cuisine", "Dinner is usually lighter, sometimes just coffee and bread."),
    ("EGY", "midday", None, None, "Egyptian cuisine", "The main meal is usually lunch; evenings bring lighter meals."),
    ("FIN", "evening", (12, 12), None, "Finnish cuisine", "Dinner is the most substantial meal; lunch around noon is warm."),
    ("FRA", None, (12, 14), (19.5, 22), "French cuisine", "Lunch from noon; restaurants open for dinner at 7.30 pm."),
    ("DEU", "shifting", None, None, "German cuisine", "Lunch was traditionally the main meal; in Berlin it is now often the evening meal."),
    ("GRC", "midday", None, None, "Yemeni cuisine", "Named alongside Spain and Portugal as places where lunch is the main meal."),
    ("HUN", "midday", (12, 14), (18, 21), "Hungarian cuisine", "Lunch is traditionally the main meal; breakfast 6 to 9, lunch 12 to 2, dinner 6 to 9."),
    ("IND", "evening", None, None, "Indian cuisine", "Dinner is considered the main meal of the day."),
    ("IDN", "midday", None, None, "Indonesian cuisine", "Lunch is often the main meal, cooked in the late morning."),
    ("ITA", "evening", (12.5, 14), None, "Lunch", "Lunch is a full meal but lighter than supper; 12.30 in the north, 2 pm in the centre and south."),
    ("LVA", "midday", (12, 15), None, "Latvian cuisine", "Lunch, from noon to 3 pm, tends to be the main meal."),
    ("LTU", "morning", None, None, "Lithuanian cuisine", "Breakfast was the most filling meal, and evening meals are still light."),
    ("MLI", "midday", None, None, "Malian cuisine", "Lunch is the most substantial meal."),
    ("MEX", "midday", (14, 16), None, "Lunch", "Lunch is usually the main meal, between 2 and 4 pm."),
    ("MCO", "midday", None, None, "Monégasque cuisine", "Traditionally lunch is the main meal."),
    ("NZL", "evening", None, None, "New Zealand cuisine", "83% of households ate their main meal in the evening in 1982."),
    ("NOR", None, None, (16, 19), "Norwegian cuisine", "Dinner usually starts around 4 to 7 pm."),
    ("OMN", "midday", None, None, "Omani cuisine", "The main meal is usually at midday; dinner is lighter."),
    ("PSE", "midday", None, (20, 22), "Palestinian cuisine", "Lunch is the heaviest meal; dinner from 8 to 10 pm."),
    ("PHL", "evening", None, (18, 20), "Filipino cuisine", "Dinner is still the main meal, usually 6 to 8 pm."),
    ("POL", "midday", (13, 17), None, "Lunch", "The main meal, obiad, is eaten between 1 and 5 pm."),
    ("PRT", "midday", (12, 14), (20, 20), "Portuguese cuisine", "Lunch between noon and 2 pm is the main meal; dinner around 8 pm."),
    ("ROU", "midday", None, None, "Lunch", "Lunch is the main hot meal of the day."),
    ("RUS", "midday", None, None, "Lunch", "Lunch, in the afternoon, is typically the biggest meal."),
    ("RWA", "midday", None, None, "Rwandan cuisine", "Lunch is generally the main meal."),
    ("SRB", "midday", None, None, "Serbian cuisine", "Lunch, in the early afternoon, is the most important meal; dinner is light."),
    ("SVK", "shifting", (12, 12), None, "Slovak cuisine", "Lunch around noon was the main meal; many now eat it in the evening."),
    ("SOM", None, None, (21, 21), "Somali cuisine", "Dinner is served as late as 9 pm."),
    ("ESP", "midday", (13, 15), (20.5, 22), "Lunch", "Lunch, 1 to 3 pm, is effectively dinner; supper begins 8.30 to 10 pm."),
    ("SWE", "evening", (11.5, 12), (18, 19), "Swedish cuisine", "A light lunch before noon and a heavy dinner around 6 or 7 pm."),
    ("GBR", "evening", None, (19.8, 19.8), "Dinner", "Average evening meal time 7.47 pm (a survey cited by Wikipedia); Sunday lunch is the big meal of the week."),
    ("USA", "evening", (11, 13), (17.1, 20.3), "Dinner", "Dinner peaks at 6.19 pm; most households eat between 5.07 and 8.19 pm."),
    ("VEN", "midday", None, None, "Venezuelan cuisine", "A large dinner around noon and a very light supper."),
    ("YEM", "midday", None, None, "Yemeni cuisine", "Lunch is the main meal of the day, not dinner."),
    ("AUS", None, (12, 14), None, "Lunch", "Lunch between noon and 2 pm."),
]
# the 'Lunch' article: in most Arab countries lunch, 1 to 4 pm, is the main meal (coded as a regional statement)
ARAB = ["SAU", "ARE", "KWT", "QAT", "BHR", "JOR", "LBN", "SYR", "IRQ"]
for a in ARAB:
    M.append((a, "midday", (13, 16), None, "Lunch", "Regional statement: in most Arab countries lunch, 1 to 4 pm, is the main meal."))
assert len({m[0] for m in M}) == len(M)

# clock versus sun (from the clock-vs-sun project's countries table)
cvs = {r["adm0"]: r for r in csv.DictReader(open("/home/claude/hist/clock-vs-sun/data/countries.csv", encoding="utf-8"))}


def solar(h, iso):
    e = float(cvs[iso]["e_ann"]) if iso in cvs and cvs[iso]["e_ann"] else None
    return None if (h is None or e is None) else round(h - e / 60, 2)


def hm(h):
    if h is None: return ""
    m = int(round(h * 60)); return f"{m // 60}:{m % 60:02d}"


brk = [{"iso3": i, "country": geo[i]["name"] if i in geo else i, "style": s, "style_label": STYLES[s], "foods": f,
        "source_section": sec, "source": BW + "#" + sec.replace(" ", "_")} for i, s, sec, f in B]
with open(f"{DATA}/breakfast.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(brk[0].keys())); w.writeheader(); w.writerows(dash(brk))

mm = []
for i, main, lw, dw, src, note in M:
    lmid = sum(lw) / 2 if lw else None
    dmid = sum(dw) / 2 if dw else None
    e = float(cvs[i]["e_ann"]) if i in cvs and cvs[i]["e_ann"] else None
    mm.append({"iso3": i, "country": geo[i]["name"] if i in geo else i, "main_meal": main or "", "lunch_from": hm(lw[0]) if lw else "",
               "lunch_to": hm(lw[1]) if lw else "", "dinner_from": hm(dw[0]) if dw else "", "dinner_to": hm(dw[1]) if dw else "",
               "lunch_mid_clock": round(lmid, 2) if lmid else "", "dinner_mid_clock": round(dmid, 2) if dmid else "",
               "clock_ahead_of_sun_min": round(e, 1) if e is not None else "",
               "lunch_mid_sun": solar(lmid, i) if lmid else "", "dinner_mid_sun": solar(dmid, i) if dmid else "",
               "regional_statement": int(i in ARAB), "note": note, "source": WP + src.replace(" ", "_")})
with open(f"{DATA}/main_meal.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(mm[0].keys())); w.writeheader(); w.writerows(dash(mm))

# Wikidata course statements
dishes = jload(f"{WORK}/dishes.json")
course = collections.defaultdict(lambda: collections.Counter())
for d in dishes:
    for c in d["countries"].split("|"):
        for k in d["course"].split("|"):
            if k == "Q80973": course[c]["breakfast"] += 1
            if k == "Q772630": course[c]["main"] += 1
            if k == "Q12896105": course[c]["lunch"] += 1
            if k == "Q657221": course[c]["dinner"] += 1
jsave({"breakfast": brk, "main": mm, "course": {k: dict(v) for k, v in course.items()}}, f"{WORK}/meals.json")
print(len(brk), "breakfast countries", collections.Counter(b["style"] for b in brk))
print(len(mm), "main-meal rows", collections.Counter(m["main_meal"] for m in mm))
print("course totals", sum(v["breakfast"] for v in course.values()), "breakfast;", sum(v["main"] for v in course.values()), "main;",
      sum(v["lunch"] for v in course.values()), "lunch;", sum(v["dinner"] for v in course.values()), "dinner")
for m in mm:
    if m["lunch_mid_sun"] or m["dinner_mid_sun"]:
        print(m["iso3"], m["lunch_mid_clock"], "->", m["lunch_mid_sun"], "|", m["dinner_mid_clock"], "->", m["dinner_mid_sun"], m["clock_ahead_of_sun_min"])
