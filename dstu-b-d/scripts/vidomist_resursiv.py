#!/usr/bin/env python3
"""Зведена відомість ресурсів до локального кошторису притулку."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"


def build_vidomist(estimate: dict, norm_index: dict[str, dict]) -> dict:
    """Агрегувати труд/машини/матеріали за позиціями кошторису."""
    mat: dict[tuple, dict] = {}
    mash: dict[tuple, dict] = {}
    trud_rob = 0.0
    trud_mash = 0.0
    vartist_trud = 0.0

    for pos in estimate["pozytsiyi"]:
        n = norm_index.get(pos["shifr"])
        if not n:
            continue
        qty = pos["kilkist"]
        r = n.get("resursy") or {}

        tr = r.get("trud_robitnykiv") or {}
        trud_rob += (tr.get("lyud_god") or 0) * qty
        vartist_trud += (tr.get("vartist_uah") or 0) * qty
        tm = r.get("trud_mashynistiv") or {}
        trud_mash += (tm.get("lyud_god") or 0) * qty
        vartist_trud += (tm.get("vartist_uah") or 0) * qty

        for m in r.get("mashyny") or []:
            key = (m.get("kod"), m.get("nazva"))
            row = mash.setdefault(key, {
                "kod": m.get("kod"),
                "nazva": m.get("nazva"),
                "odynytsya": "маш.-год",
                "kilkist": 0.0,
                "tsina_uah": m.get("tsina_mash_god_uah"),
                "vartist_uah": 0.0,
            })
            row["kilkist"] += (m.get("mash_god") or 0) * qty
            row["vartist_uah"] += (m.get("vartist_uah") or 0) * qty

        for m in r.get("materialy") or []:
            key = (m.get("kod"), m.get("nazva"), m.get("odynytsya"))
            row = mat.setdefault(key, {
                "kod": m.get("kod"),
                "nazva": m.get("nazva"),
                "odynytsya": m.get("odynytsya"),
                "kilkist": 0.0,
                "tsina_uah": m.get("tsina_za_od_uah"),
                "vartist_uah": 0.0,
            })
            row["kilkist"] += (m.get("vytrata") or 0) * qty
            row["vartist_uah"] += (m.get("vartist_uah") or 0) * qty

    materialy = sorted(mat.values(), key=lambda x: -x["vartist_uah"])
    mashyny = sorted(mash.values(), key=lambda x: -x["vartist_uah"])
    for row in materialy + mashyny:
        row["kilkist"] = round(row["kilkist"], 2)
        row["vartist_uah"] = round(row["vartist_uah"], 2)

    return {
        "obyekt": estimate.get("obyekt"),
        "trud": {
            "robitnyky_lyud_god": round(trud_rob, 1),
            "mashynisty_lyud_god": round(trud_mash, 1),
            "vartist_trudu_uah": round(vartist_trud, 2),
        },
        "mashyny": mashyny,
        "materialy": materialy,
        "pidsumky": {
            "vartist_mashyn_uah": round(sum(m["vartist_uah"] for m in mashyny), 2),
            "vartist_materialiv_uah": round(sum(m["vartist_uah"] for m in materialy), 2),
            "pozytsiy_materialiv": len(materialy),
            "pozytsiy_mashyn": len(mashyny),
        },
        "prymitka": "Кількості — добуток норм витрат на шаблонні обсяги кошторису; уточнити за робочим проектом.",
    }


def write_vidomist_files(vidomist: dict) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    (EXPORTS / "vidomist-resursiv-prytulok.json").write_text(
        json.dumps(vidomist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    fields = ["typ", "kod", "nazva", "odynytsya", "kilkist", "tsina_uah", "vartist_uah"]
    with (EXPORTS / "vidomist-resursiv-prytulok.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow({
            "typ": "труд",
            "kod": "Т1",
            "nazva": "Труд робітників-будівельників",
            "odynytsya": "люд.-год",
            "kilkist": vidomist["trud"]["robitnyky_lyud_god"],
            "tsina_uah": "",
            "vartist_uah": "",
        })
        w.writerow({
            "typ": "труд",
            "kod": "Т2",
            "nazva": "Труд машиністів",
            "odynytsya": "люд.-год",
            "kilkist": vidomist["trud"]["mashynisty_lyud_god"],
            "tsina_uah": "",
            "vartist_uah": vidomist["trud"]["vartist_trudu_uah"],
        })
        for m in vidomist["mashyny"]:
            w.writerow({"typ": "машина", **{k: m.get(k) for k in ("kod", "nazva", "odynytsya", "kilkist", "tsina_uah", "vartist_uah")}})
        for m in vidomist["materialy"]:
            w.writerow({"typ": "матеріал", **{k: m.get(k) for k in ("kod", "nazva", "odynytsya", "kilkist", "tsina_uah", "vartist_uah")}})
