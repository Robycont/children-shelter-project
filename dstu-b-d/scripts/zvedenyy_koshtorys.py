#!/usr/bin/env python3
"""Зведений кошторисний розрахунок (ЗКР) вартості будівництва притулку по главах."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"

# Розподіл шифрів локального кошторису по главах ЗКР
# Глава 1 — підготовка території; 2 — основні об'єкти; 6 — зовнішні мережі;
# 7 — благоустрій та озеленення.
CHAPTER_BY_ZBIRNYK = {
    # глава 1: підготовка території (зрізання шару, планування)
    ("Д.2.2", 1): 2,   # земляні для будівлі — гл.2 (котловани); планування — теж об'єктне
    ("Д.2.2", 5): 2,
    ("Д.2.2", 6): 2,
    ("Д.2.2", 7): 2,
    ("Д.2.2", 8): 2,
    ("Д.2.2", 9): 2,
    ("Д.2.2", 10): 2,
    ("Д.2.2", 11): 2,
    ("Д.2.2", 12): 2,
    ("Д.2.2", 15): 2,
    ("Д.2.2", 16): 2,
    ("Д.2.2", 17): 2,
    ("Д.2.2", 18): 2,
    ("Д.2.2", 20): 2,
    ("Д.2.2", 21): 2,
    ("Д.2.2", 26): 2,
    ("Д.2.2", 46): 2,
    ("Д.2.2", 22): 6,
    ("Д.2.2", 23): 6,
    ("Д.2.2", 24): 6,
    ("Д.2.2", 27): 7,
    ("Д.2.2", 47): 7,
    ("Д.2.3", 7): 2,
    ("Д.2.3", 8): 2,
    ("Д.2.3", 10): 2,
    ("Д.2.3", 11): 2,
    ("Д.2.3", 38): 2,
    ("Д.2.3", 39): 2,
}

CHAPTER_NAMES = {
    1: "Підготовка території будівництва",
    2: "Основні об'єкти будівництва",
    3: "Об'єкти підсобного та обслуговуючого призначення",
    4: "Об'єкти енергетичного господарства",
    5: "Об'єкти транспортного господарства і зв'язку",
    6: "Зовнішні мережі та споруди водопостачання, каналізації, тепло- і газопостачання",
    7: "Благоустрій та озеленення території",
    8: "Тимчасові будівлі і споруди",
    9: "Інші роботи і витрати",
    10: "Утримання служби замовника і авторський нагляд",
    12: "Проектні та вишукувальні роботи",
}


def _shifr_to_key(shifr: str, norm_index: dict[str, dict]) -> tuple[str, int] | None:
    n = norm_index.get(shifr)
    if not n:
        return None
    return (n.get("kompleks"), n.get("zbirnyk"))


def build_zkr(estimate: dict, norm_index: dict[str, dict]) -> dict:
    """Побудувати ЗКР на основі локального кошторису."""
    by_chapter: dict[int, float] = {}
    for pos in estimate["pozytsiyi"]:
        key = _shifr_to_key(pos["shifr"], norm_index)
        chapter = CHAPTER_BY_ZBIRNYK.get(key, 2)
        by_chapter[chapter] = by_chapter.get(chapter, 0) + (pos["suma_uah"] or 0)

    # прямі витрати по главах 1–7
    ch17 = {ch: round(v, 2) for ch, v in sorted(by_chapter.items())}
    bmr_pryami = round(sum(ch17.values()), 2)

    # накладні складові (як у локальному кошторисі)
    zv = round(bmr_pryami * 0.20, 2)          # загальновиробничі
    admin = round(bmr_pryami * 0.03, 2)        # адміністративні
    prybutok = round(bmr_pryami * 0.05, 2)     # кошторисний прибуток
    bmr = round(bmr_pryami + zv + admin + prybutok, 2)

    # глави 8–12 (відсотки орієнтовні, від БМР)
    ch8 = round(bmr * 0.015, 2)    # тимчасові будівлі і споруди
    ch9 = round(bmr * 0.02, 2)     # інші роботи (зимові/літні подорожчання тощо)
    ch10 = round(bmr * 0.025, 2)   # служба замовника + технагляд + авторський нагляд
    ch12 = round(bmr * 0.05, 2)    # проектно-вишукувальні + експертиза

    razom_1_12 = round(bmr + ch8 + ch9 + ch10 + ch12, 2)
    rezerv = round(razom_1_12 * 0.10, 2)  # кошторисний резерв (новобуд ~10%)
    razom_z_rezervom = round(razom_1_12 + rezerv, 2)
    pdv = round(razom_z_rezervom * 0.20, 2)
    vsogo = round(razom_z_rezervom + pdv, 2)

    glavy = []
    for ch in sorted(CHAPTER_NAMES):
        if ch <= 7:
            suma = ch17.get(ch, 0.0)
            if suma == 0 and ch in (1, 3, 4, 5):
                continue
            glavy.append({
                "glava": ch,
                "nazva": CHAPTER_NAMES[ch],
                "bmr_pryami_uah": suma,
                "prymitka": "прямі витрати за локальним кошторисом",
            })
        elif ch == 8:
            glavy.append({"glava": 8, "nazva": CHAPTER_NAMES[8], "suma_uah": ch8, "prymitka": "1,5% від БМР"})
        elif ch == 9:
            glavy.append({"glava": 9, "nazva": CHAPTER_NAMES[9], "suma_uah": ch9, "prymitka": "2% від БМР"})
        elif ch == 10:
            glavy.append({"glava": 10, "nazva": CHAPTER_NAMES[10], "suma_uah": ch10, "prymitka": "2,5% від БМР"})
        elif ch == 12:
            glavy.append({"glava": 12, "nazva": CHAPTER_NAMES[12], "suma_uah": ch12, "prymitka": "5% від БМР"})

    return {
        "obyekt": "Дитячий притулок — зведений кошторисний розрахунок (орієнтовний)",
        "glavy": glavy,
        "pidsumky": {
            "bmr_pryami_uah": bmr_pryami,
            "zagalnovyrobnychi_uah": zv,
            "administratyvni_uah": admin,
            "koshtorysnyy_prybutok_uah": prybutok,
            "bmr_vsogo_uah": bmr,
            "glavy_8_12_uah": round(ch8 + ch9 + ch10 + ch12, 2),
            "razom_glavy_1_12_uah": razom_1_12,
            "koshtorysnyy_rezerv_10pct_uah": rezerv,
            "razom_z_rezervom_uah": razom_z_rezervom,
            "pdv_20pct_uah": pdv,
            "vsogo_koshtorysna_vartist_uah": vsogo,
        },
        "prymitky": [
            "Відсотки глав 8–12 і резерву — орієнтовні; уточнити за чинними настановами з визначення вартості будівництва.",
            "Обсяги глав 1–7 — з локального кошторису із шаблонними обсягами; замінити на дані проекту.",
            "Устаткування (меблі, інвентар, технологічне) додати окремими рядками глави 2 за специфікаціями.",
        ],
    }


def write_zkr_files(zkr: dict) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    (EXPORTS / "zvedenyy-koshtorys-prytulok.json").write_text(
        json.dumps(zkr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Зведений кошторисний розрахунок — дитячий притулок (орієнтовний)",
        "",
        "| Глава | Найменування | Сума, грн | Примітка |",
        "|-------|--------------|-----------|----------|",
    ]
    for g in zkr["glavy"]:
        suma = g.get("bmr_pryami_uah", g.get("suma_uah", 0))
        lines.append(f"| {g['glava']} | {g['nazva']} | {suma:,.2f} | {g.get('prymitka','')} |".replace(",", " "))
    p = zkr["pidsumky"]
    lines += [
        "",
        "## Підсумки",
        "",
        f"- Прямі витрати (глави 1–7): **{p['bmr_pryami_uah']:,.2f} грн**".replace(",", " "),
        f"- Загальновиробничі (20%): {p['zagalnovyrobnychi_uah']:,.2f} грн".replace(",", " "),
        f"- Адміністративні (3%): {p['administratyvni_uah']:,.2f} грн".replace(",", " "),
        f"- Кошторисний прибуток (5%): {p['koshtorysnyy_prybutok_uah']:,.2f} грн".replace(",", " "),
        f"- **БМР разом: {p['bmr_vsogo_uah']:,.2f} грн**".replace(",", " "),
        f"- Глави 8–12: {p['glavy_8_12_uah']:,.2f} грн".replace(",", " "),
        f"- Разом глави 1–12: {p['razom_glavy_1_12_uah']:,.2f} грн".replace(",", " "),
        f"- Кошторисний резерв (10%): {p['koshtorysnyy_rezerv_10pct_uah']:,.2f} грн".replace(",", " "),
        f"- Разом з резервом: {p['razom_z_rezervom_uah']:,.2f} грн".replace(",", " "),
        f"- ПДВ (20%): {p['pdv_20pct_uah']:,.2f} грн".replace(",", " "),
        f"- **ВСЬОГО кошторисна вартість: {p['vsogo_koshtorysna_vartist_uah']:,.2f} грн**".replace(",", " "),
        "",
        "## Примітки",
        "",
    ] + [f"- {x}" for x in zkr["prymitky"]]
    (EXPORTS / "zvedenyy-koshtorys-prytulok.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
