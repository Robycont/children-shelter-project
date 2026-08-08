#!/usr/bin/env python3
"""
Орієнтовні ресурсні показники до норм ДСТУ Б Д.

Дані — довідкові/укрупнені для попереднього кошторису притулку.
Для офіційного інвесторського кошторису звіряти з чинним КНУ РЕКН / ДСТУ.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _seed(text: str) -> float:
    """Стабільна псевдовипадковість 0..1 для варіації близьких норм."""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _r(n: float, digits: int = 3) -> float:
    return round(n, digits)


def _mat(kod: str, nazva: str, od: str, vytrata: float, tsina_uah: float | None = None) -> dict:
    item = {
        "kod": kod,
        "nazva": nazva,
        "odynytsya": od,
        "vytrata": _r(vytrata, 4) if abs(vytrata) < 10 else _r(vytrata, 2),
    }
    if tsina_uah is not None:
        item["tsina_za_od_uah"] = _r(tsina_uah, 2)
        item["vartist_uah"] = _r(item["vytrata"] * tsina_uah, 2)
    return item


def _mash(kod: str, nazva: str, mash_god: float, tsina_mash_god: float | None = None) -> dict:
    item = {"kod": kod, "nazva": nazva, "mash_god": _r(mash_god, 4)}
    if tsina_mash_god is not None:
        item["tsina_mash_god_uah"] = _r(tsina_mash_god, 2)
        item["vartist_uah"] = _r(mash_god * tsina_mash_god, 2)
    return item


# Орієнтовні тарифи (грн, 2026, укрупнено)
TARIF_ROBITNYK = 95.0  # грн/люд.-год
TARIF_MASHYNIST = 110.0


def _unit_factor(unit: str) -> float:
    """Привести вимірювач до «базової» одиниці для норми витрат."""
    u = (unit or "").lower().replace(" ", "")
    if u.startswith("1000м3") or u.startswith("1000 м3"):
        return 1000.0
    if u.startswith("100м3") or "100м3" in u:
        return 100.0
    if u.startswith("1000м2"):
        return 1000.0
    if u.startswith("100м2") or "100м2" in u:
        return 100.0
    if u.startswith("100м") and "м2" not in u and "м3" not in u:
        return 100.0
    if u.startswith("100шт"):
        return 100.0
    if "км" in u:
        return 1000.0
    if u in {"т", "шт", "м", "м2", "м3", "компл", "система", "контур", "лінія", "год", "квт"}:
        return 1.0
    if "/" in u:
        # складний вимірювач — беремо перший
        return _unit_factor(u.split("/")[0])
    return 1.0


def _base_profile(kompleks: str, nomer: int, nazva: str, unit: str) -> dict[str, Any]:
    """Підібрати базовий профіль ресурсів за ключовими словами."""
    t = nazva.lower()
    g = f"{kompleks}-{nomer}"
    factor = _unit_factor(unit)
    s = _seed(f"{g}:{nazva}:{unit}")

    # дефолт
    labor = 2.5 + s
    grade = 3.2
    machinist = 0.0
    machines: list[dict] = []
    materials: list[dict] = []
    sklad = ["Підготовка робочого місця", "Виконання основного процесу", "Прибирання"]

    # --- земляні ---
    if any(k in t for k in ("розробк", "екскаватор", "бульдозер", "котлован", "транше", "засипан", "ущільн", "плануван")):
        if "вручну" in t or "ручн" in t:
            labor = 45.0 + 10 * s
            grade = 2.5
            sklad = ["Розпушування ґрунту", "Викидання ґрунту", "Зачищення"]
            materials = [_mat("С311-1", "Перевезення ґрунту (за потреби)", "т", 0.0)]
        elif "бульдозер" in t:
            labor = 0.8 + 0.3 * s
            machinist = 1.2 + 0.2 * s
            grade = 3.0
            machines = [_mash("С201-1", "Бульдозер 79 кВт", machinist, 850)]
            sklad = ["Розробка ґрунту", "Переміщення", "Планування"]
        elif "екскаватор" in t or "навантаж" in t:
            labor = 1.0 + 0.4 * s
            machinist = 1.5 + 0.3 * s
            grade = 3.0
            machines = [
                _mash("С202-1", "Екскаватор одноковшовий 0,4–0,65 м3", machinist, 1200),
                _mash("С311-2", "Автосамоскид 10 т", 1.2 + 0.2 * s, 700),
            ]
            sklad = ["Розробка ґрунту", "Навантаження", "Переміщення в межах вибою"]
        else:
            labor = 8.0 + 3 * s
            machinist = 0.5
            grade = 2.8
            machines = [_mash("С201-2", "Бульдозер / трамбівка", 0.5, 600)]

    # --- бетон / ЗБК ---
    elif any(k in t for k in ("бетон", "залізобетон", "опалуб", "армату", "ростверк", "фундаментн")) and nomer in {5, 6, 7, 46} or any(
        k in t for k in ("бетонуван", "замоноліч", "опалубк", "армуванн")
    ):
        if "опалуб" in t:
            labor = 12.0 + 3 * s
            grade = 3.8
            materials = [
                _mat("С101-1", "Опалубка інвентарна (амортизація)", "м2", 1.05, 45),
                _mat("С102-1", "Цвяхи будівельні", "кг", 0.3, 55),
                _mat("С103-1", "Мастило для опалубки", "кг", 0.2, 40),
            ]
            sklad = ["Установлення опалубки", "Кріплення", "Розбирання", "Очищення щитів"]
        elif "армату" in t:
            labor = 18.0 + 4 * s
            grade = 4.0
            machinist = 0.4
            machines = [_mash("С210-1", "Кран автомобільний 10 т", 0.4, 1400)]
            materials = [
                _mat("С111-1", "Арматура періодичного профілю А400/А500", "т", 1.02, 32000),
                _mat("С112-1", "Дріт в'язальний", "кг", 8.0, 45),
            ]
            sklad = ["Сортування арматури", "Гнуття", "Установлення і в'язання"]
        else:
            labor = 6.5 + 2 * s
            grade = 3.5
            machinist = 0.6
            machines = [
                _mash("С210-1", "Кран / бетононасос", 0.6, 1500),
                _mash("С211-1", "Вібратор глибинний", 0.8, 120),
            ]
            materials = [
                _mat("С120-1", "Бетон товарний В15–В25", "м3", 1.02, 3200),
                _mat("С121-1", "Вода", "м3", 0.2, 40),
            ]
            sklad = ["Подача суміші", "Укладання", "Ущільнення", "Догляд за бетоном"]

    # --- збірні ЗБК (монтаж) ---
    elif kompleks == "Д.2.2" and nomer == 7:
        if "100 шт" in (unit or "") or "фбс" in t or "блоків фундаментних" in t or "подушок" in t:
            labor = 180 + 40 * s
            machinist = 45 + 10 * s
            grade = 3.8
            machines = [_mash("С210-1", "Кран автомобільний 16 т", machinist, 1500)]
            materials = [
                _mat("С122-1", "Блоки/подушки збірні (за специфікацією)", "шт", 100, 1800),
                _mat("С135-1", "Розчин мурувальний", "м3", 4.5, 2200),
            ]
        elif "замоноліч" in t or "стиків" in t and "заливан" not in t:
            labor = 45 + 10 * s
            machinist = 2.0
            grade = 3.6
            machines = [_mash("С211-1", "Вібратор/дрібна механізація", 2.0, 120)]
            materials = [_mat("С120-1", "Бетон дрібнозернистий", "м3", 1.5, 3300)]
        elif unit and "шт" == unit.strip():
            labor = 6.0 + 2 * s
            machinist = 1.2
            grade = 4.0
            machines = [_mash("С210-1", "Кран автомобільний 16 т", 1.2, 1500)]
            materials = [
                _mat("С123-1", "Елемент збірний (за специфікацією)", "шт", 1.0, 9000),
                _mat("С135-1", "Розчин / зварювальні матеріали", "компл", 1.0, 350),
            ]
        else:  # 100 м2 плит/панелей
            labor = 90 + 20 * s
            machinist = 14 + 3 * s
            grade = 4.0
            machines = [_mash("С210-1", "Кран автомобільний 16–25 т", machinist, 1600)]
            materials = [
                _mat("С124-1", "Плити/панелі збірні (за специфікацією)", "м2", 100, 1500),
                _mat("С135-1", "Розчин для швів", "м3", 1.2, 2200),
                _mat("С141-1", "Електроди", "кг", 4.0, 90),
            ]
        sklad = ["Стропування", "Подача краном", "Установлення на розчині", "Вивірка", "Зварювання/анкерування"]

    # --- мурування цегла/блоки ---
    elif any(k in t for k in ("муруван", "цегл", "блок", "бутов", "газобетон", "керамзит", "перегород")) or nomer == 8:
        if "газобетон" in t or "клею" in t:
            labor = 3.8 + s
            grade = 3.6
            materials = [
                _mat("С130-1", "Блоки газобетонні", "м3", 1.02, 2800),
                _mat("С131-1", "Клейова суміш для газобетону", "кг", 25, 18),
                _mat("С132-1", "Арматура для армопоясів / сітка", "кг", 2.5, 35),
            ]
        elif "перегород" in t and ("гіпс" in t or "легкобетон" in t):
            labor = 2.2 + 0.5 * s
            grade = 3.4
            materials = [
                _mat("С133-1", "Плити гіпсові / пазогребеневі", "м2", 1.05 if factor == 1 else 1.05, 220),
                _mat("С131-2", "Клей гіпсовий", "кг", 5.0, 16),
            ]
            # для 100 м2
            if factor >= 100:
                materials = [
                    _mat("С133-1", "Плити гіпсові / пазогребеневі", "м2", 105, 220),
                    _mat("С131-2", "Клей гіпсовий", "кг", 500, 16),
                ]
                labor = 180 + 40 * s
        elif "бутов" in t:
            labor = 5.5 + 1.2 * s
            grade = 3.3
            materials = [
                _mat("С134-1", "Камінь бутовий", "м3", 1.05, 900),
                _mat("С135-1", "Розчин мурувальний М50–М75", "м3", 0.38, 2200),
            ]
        elif "риштуван" in t:
            labor = 8.0 + 2 * s
            grade = 3.2
            materials = [
                _mat("С136-1", "Риштування інвентарні (амортизація)", "м2", 1.0 if factor == 1 else 100, 25),
            ]
            if factor >= 100:
                labor = 25 + 5 * s
        else:
            # цегляне мурування на 1 м3
            labor = 4.8 + 0.8 * s
            grade = 3.5
            materials = [
                _mat("С137-1", "Цегла керамічна рядова 250×120×65", "шт", 400 + 10 * s, 12),
                _mat("С135-1", "Розчин мурувальний М50–М75", "м3", 0.24, 2200),
                _mat("С138-1", "Вода", "м3", 0.15, 40),
            ]
            if "силікат" in t:
                materials[0] = _mat("С137-2", "Цегла силікатна", "шт", 400, 10)
            if factor >= 100:  # 100 м2 перегородок
                labor = 55 + 10 * s
                materials = [
                    _mat("С137-1", "Цегла керамічна", "шт", 5100, 12),
                    _mat("С135-1", "Розчин мурувальний", "м3", 2.4, 2200),
                ]
        machinist = 0.15
        machines = [_mash("С212-1", "Підйомник / кран (подача матеріалів)", 0.15, 900)]
        sklad = ["Подача матеріалів", "Мурування", "Перевірка вертикальності", "Розшивання / зачищення"]

    # --- метал ---
    elif any(k in t for k in ("метал", "колон", "ферм", "профнастил", "зварюв", "балок", "ригел")) and nomer in {9, 39, 46}:
        labor = 14.0 + 3 * s
        grade = 4.2
        machinist = 1.0
        machines = [
            _mash("С210-2", "Кран стріловий 16–25 т", 1.0, 1800),
            _mash("С213-1", "Апарат зварювальний", 2.0, 80),
        ]
        materials = [
            _mat("С140-1", "Конструкції сталеві", "т", 1.03, 45000),
            _mat("С141-1", "Електроди / зварювальні матеріали", "кг", 6.0, 90),
            _mat("С142-1", "Болти високоміцні / метизи", "кг", 8.0, 70),
        ]
        sklad = ["Стропування", "Установлення", "Вивірка", "Закріплення / зварювання"]

    # --- дерево ---
    elif any(k in t for k in ("дерев", "крокв", "мауерлат", "лавч", "гіпсокартон", "віконн", "дверн", "обшив", "підшив")) or nomer == 10:
        if "вікон" in t or "двер" in t:
            labor = 2.5 + 0.6 * s
            grade = 3.8
            materials = [
                _mat("С150-1", "Блок віконний/дверний", "м2", 1.0 if factor == 1 else 100, 2500),
                _mat("С151-1", "Піна монтажна / герметик", "л", 0.8 if factor == 1 else 80, 120),
                _mat("С152-1", "Кріплення (анкери, шурупи)", "компл", 1.0 if factor == 1 else 100, 45),
            ]
            if factor >= 100:
                labor = 220 + 40 * s
            sklad = ["Приміртування", "Установлення", "Закріплення", "Задування швів"]
        elif "гіпсокартон" in t or "каркасн" in t:
            labor = 1.8 + 0.4 * s
            grade = 3.5
            materials = [
                _mat("С153-1", "Профіль CD/UD", "м", 3.2 if factor == 1 else 320, 25),
                _mat("С154-1", "Гіпсокартон 12,5 мм", "м2", 1.15 if factor == 1 else 115, 180),
                _mat("С155-1", "Шурупи, стрічка, шпаклівка", "компл", 1.0 if factor == 1 else 100, 90),
            ]
            if factor >= 100:
                labor = 160 + 30 * s
        else:
            labor = 8.0 + 2 * s
            grade = 3.6
            materials = [
                _mat("С156-1", "Пиломатеріали хвойні", "м3", 1.1, 12000),
                _mat("С157-1", "Цвяхи, кріплення", "кг", 5.0, 55),
                _mat("С158-1", "Антисептик", "л", 1.5, 80),
            ]
        sklad = ["Розмітка", "Заготівля", "Монтаж", "Кріплення"]

    # --- підлоги ---
    elif any(k in t for k in ("підлог", "стяжк", "лінолеум", "ламінат", "паркет", "плитк")) and ("стін" not in t or "підлог" in t) or nomer == 11:
        if "стяжк" in t or "підстилаюч" in t or "бетонн" in t and "підлог" in t:
            labor = 1.2 + 0.3 * s
            grade = 3.3
            materials = [
                _mat("С160-1", "Суміш для стяжки / бетон", "м3", 0.04 if factor == 1 else 4.0, 2800),
                _mat("С161-1", "Ґрунтовка", "л", 0.2 if factor == 1 else 20, 90),
            ]
            if factor >= 100:
                labor = 90 + 20 * s
                materials = [
                    _mat("С160-1", "Суміш для стяжки", "м3", 4.0, 2800),
                    _mat("С161-1", "Ґрунтовка", "л", 20, 90),
                ]
        elif "лінолеум" in t or "пвх" in t:
            labor = 0.7 + 0.2 * s
            grade = 3.4
            materials = [
                _mat("С162-1", "Лінолеум / ПВХ-покриття", "м2", 1.05 if factor == 1 else 105, 450),
                _mat("С163-1", "Клей для лінолеуму", "кг", 0.4 if factor == 1 else 40, 85),
                _mat("С164-1", "Плінтус ПВХ", "м", 0.4 if factor == 1 else 40, 55),
            ]
            if factor >= 100:
                labor = 55 + 10 * s
        elif "ламінат" in t or "паркет" in t or "дощат" in t:
            labor = 1.0 + 0.25 * s
            grade = 3.7
            materials = [
                _mat("С165-1", "Ламінат / дошка / паркет", "м2", 1.08 if factor == 1 else 108, 650),
                _mat("С166-1", "Підкладка", "м2", 1.05 if factor == 1 else 105, 45),
                _mat("С164-2", "Плінтус", "м", 0.4 if factor == 1 else 40, 70),
            ]
            if factor >= 100:
                labor = 75 + 15 * s
        else:  # плитка
            labor = 1.6 + 0.3 * s
            grade = 3.8
            materials = [
                _mat("С167-1", "Плитка керамічна / керамограніт", "м2", 1.05 if factor == 1 else 105, 420),
                _mat("С168-1", "Клей плитковий", "кг", 5.0 if factor == 1 else 500, 14),
                _mat("С169-1", "Затирка", "кг", 0.5 if factor == 1 else 50, 45),
            ]
            if factor >= 100:
                labor = 130 + 25 * s
        sklad = ["Підготовка основи", "Укладання покриття", "Обробка примикань"]

    # --- покрівля ---
    elif any(k in t for k in ("покрівл", "руберойд", "металочерепиц", "профнастил", "ринв", "водостік", "пароізол", "наплав")) or nomer == 12:
        if "металочерепиц" in t or "профнастил" in t or "фальц" in t:
            labor = 1.4 + 0.3 * s
            grade = 3.7
            materials = [
                _mat("С170-1", "Металочерепиця / профнастил", "м2", 1.1 if factor == 1 else 110, 320),
                _mat("С171-1", "Саморізи покрівельні", "шт", 8 if factor == 1 else 800, 2.5),
                _mat("С172-1", "Плівки / ущільнювачі", "м2", 1.1 if factor == 1 else 110, 35),
            ]
            if factor >= 100:
                labor = 110 + 20 * s
        elif "ринв" in t or "водостік" in t or "планок" in t:
            labor = 1.0 + 0.2 * s
            grade = 3.5
            materials = [
                _mat("С173-1", "Елементи водостоку / планки", "м", 1.05 if factor == 1 else 105, 180),
                _mat("С171-2", "Кріплення", "компл", 1.0 if factor == 1 else 100, 40),
            ]
            if factor >= 100:
                labor = 70 + 15 * s
        else:
            labor = 1.1 + 0.25 * s
            grade = 3.6
            materials = [
                _mat("С174-1", "Матеріал рулонний наплавлюваний", "м2", 1.15 if factor == 1 else 115, 180),
                _mat("С175-1", "Праймер бітумний", "л", 0.3 if factor == 1 else 30, 70),
            ]
            if factor >= 100:
                labor = 85 + 15 * s
            machinist = 0.2
            machines = [_mash("С214-1", "Пальник газовий покрівельний", 0.8, 50)]
        sklad = ["Підготовка основи", "Укладання покриття", "Влаштування примикань"]

    # --- оздоблення ---
    elif any(k in t for k in ("штукатур", "фарбув", "облицюв", "шпалер", "осклін", "шпаклів", "ґрунтув", "стель")) or nomer == 15:
        if "облицюв" in t or "плитк" in t:
            labor = 2.0 + 0.4 * s
            grade = 3.9
            materials = [
                _mat("С180-1", "Плитка облицювальна", "м2", 1.05 if factor == 1 else 105, 380),
                _mat("С168-1", "Клей плитковий", "кг", 5.5 if factor == 1 else 550, 14),
                _mat("С169-1", "Затирка", "кг", 0.6 if factor == 1 else 60, 45),
            ]
            if factor >= 100:
                labor = 160 + 30 * s
        elif "фарбув" in t or "шпаклів" in t or "ґрунтув" in t:
            labor = 0.9 + 0.2 * s
            grade = 3.4
            materials = [
                _mat("С181-1", "Ґрунтовка", "л", 0.15 if factor == 1 else 15, 85),
                _mat("С182-1", "Шпаклівка", "кг", 1.2 if factor == 1 else 120, 22),
                _mat("С183-1", "Фарба водоемульсійна", "л", 0.25 if factor == 1 else 25, 140),
            ]
            if factor >= 100:
                labor = 70 + 15 * s
        elif "шпалер" in t:
            labor = 0.8 + 0.2 * s
            grade = 3.5
            materials = [
                _mat("С184-1", "Шпалери", "м2", 1.1 if factor == 1 else 110, 180),
                _mat("С185-1", "Клей шпалерний", "кг", 0.2 if factor == 1 else 20, 60),
            ]
            if factor >= 100:
                labor = 60 + 12 * s
        elif "стель" in t or "підвісн" in t or "натяжн" in t:
            labor = 1.5 + 0.3 * s
            grade = 3.7
            materials = [
                _mat("С186-1", "Каркас / комплектуючі стелі", "м2", 1.05 if factor == 1 else 105, 250),
                _mat("С187-1", "Плити / полотно стелі", "м2", 1.05 if factor == 1 else 105, 200),
            ]
            if factor >= 100:
                labor = 120 + 25 * s
        else:  # штукатурка
            labor = 1.8 + 0.4 * s
            grade = 3.6
            materials = [
                _mat("С188-1", "Суміш штукатурна", "кг", 12 if factor == 1 else 1200, 8),
                _mat("С181-2", "Ґрунтовка", "л", 0.2 if factor == 1 else 20, 85),
                _mat("С189-1", "Сітка штукатурна (за потреби)", "м2", 0.3 if factor == 1 else 30, 25),
            ]
            if factor >= 100:
                labor = 150 + 30 * s
        sklad = ["Підготовка поверхні", "Основний опоряджувальний процес", "Зачищення / фініш"]

    # --- трубопроводи / сантехніка ---
    elif any(k in t for k in ("труб", "водопров", "каналіз", "опален", "радіатор", "умивальн", "унітаз", "змішувач", "газопров")) or re.search(r"(?:^|\s)ванн", t) or nomer in {16, 17, 18, 19, 22, 23, 24}:
        if any(k in t for k in ("умивальн", "унітаз", "мийк", "змішувач", "піддон", "пісуар", "біде", "радіатор", "конвектор", "рушникосушар")) or re.search(r"(?:^|\s)(ванн|трап|котл|насос|лічильник)", t):
            labor = 3.5 + s
            grade = 4.0
            materials = [
                _mat("С190-1", "Прилад санітарний / опалювальний", "шт", 1.0, 3500),
                _mat("С191-1", "Підводка / кріплення / арматура", "компл", 1.0, 650),
                _mat("С192-1", "Герметик / ущільнювачі", "компл", 1.0, 80),
            ]
            sklad = ["Розмітка", "Установлення приладу", "Підключення", "Перевірка"]
        elif any(k in t for k in ("колодяз", "септик", "лос", "дощоприймач", "гідрант")):
            labor = 16.0 + 4 * s
            grade = 3.6
            machinist = 1.2
            machines = [_mash("С210-1", "Кран автомобільний 10 т", 1.2, 1400)]
            materials = [
                _mat("С196-1", "Кільця/елементи колодязя збірні", "компл", 1.0, 6500),
                _mat("С197-1", "Люк чавунний / решітка", "шт", 1.0, 2800),
                _mat("С135-1", "Розчин для закладення стиків", "м3", 0.08, 2200),
            ]
            sklad = ["Підготовка основи", "Монтаж елементів краном", "Закладення стиків", "Установлення люка"]
        else:
            labor = 2.0 + 0.5 * s
            grade = 3.8
            materials = [
                _mat("С193-1", "Труби (сталь/ППР/ПВХ/ПЕ)", "м", 1.05 if factor == 1 else 105, 120),
                _mat("С194-1", "Фітинги та арматура", "компл", 1.0 if factor == 1 else 100, 350),
                _mat("С195-1", "Кріплення / ізоляція", "компл", 1.0 if factor == 1 else 100, 90),
            ]
            if factor >= 100:
                labor = 160 + 40 * s
            sklad = ["Розмітка траси", "Прокладання трубопроводів", "Монтаж арматури", "Випробування"]

    # --- вентиляція ---
    elif any(k in t for k in ("повітровод", "вентиля", "кондиці", "спліт", "дифузор", "решіт")) or nomer == 20:
        if "спліт" in t or "кондиці" in t or "вентилятор" in t or "установ" in t and "приплив" in t:
            labor = 8.0 + 2 * s
            grade = 4.1
            materials = [
                _mat("С200-1", "Обладнання вентиляції/кондиціювання", "шт", 1.0, 18000),
                _mat("С201-m", "Кронштейни, фреон-траса, дренаж", "компл", 1.0, 2500),
            ]
        else:
            labor = 3.0 + 0.6 * s
            grade = 3.9
            materials = [
                _mat("С202-m", "Повітроводи оцинковані", "м2", 1.05 if factor == 1 else 105, 280),
                _mat("С203-m", "Фланці, ущільнення, кріплення", "компл", 1.0 if factor == 1 else 100, 120),
            ]
            if factor >= 100:
                labor = 220 + 40 * s
        sklad = ["Заготівля", "Монтаж", "Герметизація", "Перевірка"]

    # --- електрика ---
    elif any(k in t for k in ("кабел", "провод", "світильник", "розетк", "вимикач", "щит", "заземлен", "електро", "лічильник електро")) or nomer in {21, 33} or (kompleks == "Д.2.3" and nomer in {8, 39}):
        if any(k in t for k in ("світильник", "розетк", "вимикач", "щит", "лічильник", "коробк")):
            labor = 1.2 + 0.3 * s
            grade = 3.8
            materials = [
                _mat("С210-m", "Виріб електроустановочний / щит / світильник", "шт", 1.0 if factor == 1 else 100, 350),
                _mat("С211-m", "Клемники, кріплення", "компл", 1.0 if factor == 1 else 100, 40),
            ]
            if factor >= 100:
                labor = 90 + 20 * s
        elif "заземлен" in t:
            labor = 12.0 + 3 * s
            grade = 4.0
            materials = [
                _mat("С212-m", "Сталь кругла / кутик для заземлення", "кг", 45, 35),
                _mat("С213-m", "Провідник заземлення", "м", 25, 40),
            ]
        else:
            labor = 1.5 + 0.4 * s
            grade = 3.7
            materials = [
                _mat("С214-m", "Кабель / провід силовий", "м", 1.05 if factor == 1 else 105, 55),
                _mat("С215-m", "Труба/короб/гофра", "м", 1.05 if factor == 1 else 105, 18),
                _mat("С216-m", "Кріплення", "компл", 1.0 if factor == 1 else 100, 25),
            ]
            if factor >= 100:
                labor = 110 + 25 * s
        sklad = ["Розмітка трас", "Прокладання / установлення", "Підключення", "Перевірка ізоляції"]

    # --- теплоізоляція ---
    elif any(k in t for k in ("утепл", "теплоізол", "ізоляц", "ссті", "гідроізол")) or nomer in {13, 26}:
        labor = 1.3 + 0.3 * s
        grade = 3.5
        materials = [
            _mat("С220-1", "Утеплювач плитний", "м2", 1.05 if factor == 1 else 105, 220),
            _mat("С221-1", "Клей / дюбелі / сітка / декоративний шар", "компл", 1.0 if factor == 1 else 100, 180),
        ]
        if factor >= 100:
            labor = 100 + 20 * s
        if "гідроізол" in t or "ізоляц" in t and "тепло" not in t:
            materials = [
                _mat("С222-1", "Мастика / рулонна гідроізоляція", "м2", 1.15 if factor == 1 else 115, 160),
                _mat("С223-1", "Праймер", "л", 0.3 if factor == 1 else 30, 70),
            ]
        sklad = ["Підготовка поверхні", "Монтаж ізоляції", "Захисний шар / фініш"]

    # --- дороги / благоустрій / озеленення ---
    elif any(k in t for k in ("асфальт", "щебен", "бордюр", "тротуар", "газон", "посадк", "дерев", "квітник", "озелен")) or nomer in {27, 47}:
        if "посадк" in t or "дерев" in t or "кущ" in t:
            labor = 1.5 + 0.4 * s
            grade = 2.8
            materials = [
                _mat("С230-1", "Садивний матеріал", "шт", 1.0, 450),
                _mat("С231-1", "Ґрунт рослинний / добрива", "м3", 0.2, 600),
            ]
        elif "газон" in t or "квітник" in t or "озелен" in t:
            labor = 0.6 + 0.15 * s
            grade = 2.7
            materials = [
                _mat("С232-1", "Насіння / рулонний газон / розсада", "м2", 1.1 if factor == 1 else 110, 45),
                _mat("С231-2", "Ґрунт рослинний", "м3", 0.05 if factor == 1 else 5.0, 600),
            ]
            if factor >= 100:
                labor = 45 + 10 * s
        else:
            labor = 0.8 + 0.2 * s
            grade = 3.2
            machinist = 0.4
            machines = [
                _mash("С220-m", "Коток / віброплита", 0.4, 500),
                _mash("С221-m", "Автосамоскид", 0.3, 700),
            ]
            materials = [
                _mat("С233-1", "Щебінь / відсів / асфальтобетон / плитка", "м3", 0.2 if factor == 1 else (0.15 if factor >= 1000 else 15), 1800),
            ]
            if factor >= 100:
                labor = 55 + 15 * s
        sklad = ["Підготовка основи", "Улаштування покриття / посадка", "Ущільнення / полив"]

    # --- монтаж обладнання ---
    elif kompleks == "Д.2.3" or any(k in t for k in ("монтаж", "підключен", "налагодж")):
        labor = 10.0 + 5 * s
        grade = 4.3
        machinist = 1.5
        machines = [
            _mash("С230-m", "Кран / такелаж", 1.5, 1600),
            _mash("С213-1", "Зварювальне / електромонтажне обладнання", 2.0, 80),
        ]
        materials = [
            _mat("С240-1", "Матеріали монтажні (анкери, прокладки, метизи)", "компл", 1.0, 1200),
            _mat("С241-1", "Електроди / кабель обв'язки", "компл", 1.0, 800),
        ]
        sklad = ["Приймання обладнання", "Установлення на фундамент", "Вивірка", "Обв'язка", "Індивідуальні випробування"]

    # --- ремонт ---
    elif kompleks == "Д.2.4" or any(k in t for k in ("розбиран", "демонтаж", "ремонт", "замін", "відновлен", "відбиван")):
        if "розбиран" in t or "демонтаж" in t or "відбиван" in t:
            labor = 4.0 + 1.5 * s
            grade = 2.8
            machinist = 0.3
            machines = [_mash("С240-m", "Перфоратор / відбійний молоток", 1.0, 90)]
            materials = [_mat("С311-3", "Вивезення будівельного сміття", "т", 0.8 + 0.4 * s, 450)]
            sklad = ["Відключення комунікацій", "Розбирання", "Сортування", "Винесення сміття"]
        else:
            labor = 5.0 + 2 * s
            grade = 3.5
            materials = [
                _mat("С250-1", "Матеріали ремонтні", "компл", 1.0, 1500),
                _mat("С251-1", "Суміші / розчини / фарби", "компл", 1.0, 800),
            ]
            sklad = ["Підготовка", "Ремонтні роботи", "Прибирання"]

    # --- реконструкція / палі / спец ---
    elif nomer in {5, 46} or any(k in t for k in ("пал", "пробиван", "посилен")):
        labor = 8.0 + 3 * s
        grade = 3.8
        machinist = 2.0
        machines = [_mash("С250-m", "Копер / бурова установка / кран", 2.0, 2200)]
        materials = [
            _mat("С260-1", "Палі / бетон / метал посилення", "компл", 1.0, 15000),
        ]
        sklad = ["Підготовка", "Основний процес", "Контроль якості"]

    # масштабування labor якщо одиниця вже «на вимірювач» і профіль був на 1 м2/м
    # (для більшості профілів уже враховано factor>=100)

    return {
        "labor": labor,
        "grade": grade,
        "machinist": machinist,
        "machines": machines,
        "materials": materials,
        "sklad": sklad,
    }


def _calibrate(kompleks: str, nomer: int, nazva: str, unit: str, profile: dict) -> dict:
    """Відкалібрувати показники до реалістичних діапазонів за вимірювачем."""
    t = nazva.lower()
    u = (unit or "").lower().replace(" ", "")
    factor = _unit_factor(unit)
    s = _seed(f"cal:{kompleks}{nomer}:{nazva}")

    def clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    labor = profile["labor"]
    machinist = profile["machinist"]
    machines = profile["machines"]
    materials = list(profile["materials"])

    is_beton = any(k in t for k in ("бетон", "залізобетон", "фундамент", "ростверк", "перекритт", "колон", "сход", "монолітн")) and "розбиран" not in t and "демонтаж" not in t

    if u.startswith("1000м3"):
        labor = clamp(labor, 10 + 6 * s, 60)
        if machines:
            machinist = clamp(machinist, 18 + 6 * s, 45)
    elif u.startswith("100м3") or u == "100м3":
        if is_beton and kompleks == "Д.2.2" and nomer in {5, 6, 7, 37, 46}:
            labor = clamp(labor * (100 if labor < 30 else 1), 350 + 100 * s, 900)
            machinist = clamp(machinist * (100 if machinist < 3 else 1), 25 + 10 * s, 70)
        else:
            labor = clamp(labor * (10 if labor < 15 else 1), 90 + 40 * s, 300)
    elif u.startswith("1000м2"):
        labor = clamp(labor, 15 + 8 * s, 90)
        if machines:
            machinist = clamp(machinist, 6 + 3 * s, 25)
    elif u.startswith("100м2"):
        labor = clamp(labor * (10 if labor < 8 else 1), 35 + 15 * s, 320)
    elif u.startswith("100шт"):
        labor = clamp(labor * (10 if labor < 10 else 1), 40 + 20 * s, 380)
    elif u.startswith("100м") and "м2" not in u and "м3" not in u:
        labor = clamp(labor * (10 if labor < 6 else 1), 20 + 10 * s, 260)
    elif u == "т":
        labor = clamp(labor, 12 + 6 * s, 45)

    # масштабування машин під новий машиніст-час
    if machines and machinist > 0:
        old_mh = sum(m.get("mash_god", 0) for m in machines) or 1
        k = machinist / old_mh
        if abs(k - 1) > 0.05:
            for m in machines:
                m["mash_god"] = _r(m["mash_god"] * k, 3)
                if m.get("tsina_mash_god_uah") is not None:
                    m["vartist_uah"] = _r(m["mash_god"] * m["tsina_mash_god_uah"], 2)

    # матеріали в м3 на вимірювач 100 м3 (бетон 1.02 -> 102)
    if (u.startswith("100м3") or u == "100м3") and is_beton:
        for m in materials:
            if m.get("odynytsya") == "м3" and (m.get("vytrata") or 0) <= 2.5:
                m["vytrata"] = _r(m["vytrata"] * 100, 2)
                if m.get("tsina_za_od_uah") is not None:
                    m["vartist_uah"] = _r(m["vytrata"] * m["tsina_za_od_uah"], 2)

    profile["labor"] = labor
    profile["machinist"] = machinist
    profile["machines"] = machines
    profile["materials"] = materials
    return profile


def build_resources(kompleks: str, nomer: int, nazva: str, unit: str, shifr: str = "") -> tuple[dict, list[str]]:
    """Повернути (resursy, sklad_robit) для норми."""
    profile = _base_profile(kompleks, nomer, nazva, unit)
    profile = _calibrate(kompleks, nomer, nazva, unit, profile)
    labor = _r(profile["labor"], 3)
    grade = _r(profile["grade"], 1)
    machinist = _r(profile["machinist"], 3)
    machines = profile["machines"]
    materials = list(profile["materials"])

    # Для механізованих робіт без матеріалів — пальне/мастила
    if not materials and machines:
        fuel = sum(m.get("mash_god", 0) for m in machines) * 8.5
        materials.append(_mat("С300-1", "Пальне дизельне (орієнтовно)", "л", max(fuel, 1.0), 55))
        materials.append(_mat("С300-2", "Мастильні матеріали", "кг", max(fuel * 0.05, 0.1), 120))
    elif not materials:
        materials.append(_mat("С301-1", "Допоміжні матеріали", "компл", 1.0, 150))

    # вартість труда
    vartist_trud = _r(labor * TARIF_ROBITNYK + machinist * TARIF_MASHYNIST, 2)
    vartist_mash = _r(sum(m.get("vartist_uah", 0) or 0 for m in machines), 2)
    vartist_mat = _r(sum(m.get("vartist_uah", 0) or 0 for m in materials), 2)
    priami = _r(vartist_trud + vartist_mash + vartist_mat, 2)

    resursy = {
        "trud_robitnykiv": {
            "lyud_god": labor,
            "seredniy_rozryad": grade,
            "tarif_uah_za_god": TARIF_ROBITNYK,
            "vartist_uah": _r(labor * TARIF_ROBITNYK, 2),
        },
        "trud_mashynistiv": {
            "lyud_god": machinist,
            "tarif_uah_za_god": TARIF_MASHYNIST,
            "vartist_uah": _r(machinist * TARIF_MASHYNIST, 2),
        },
        "mashyny": machines,
        "materialy": materials,
        "pidsumky": {
            "vartist_trudu_uah": vartist_trud,
            "vartist_mashyn_uah": vartist_mash,
            "vartist_materialiv_uah": vartist_mat,
            "priami_vytraty_uah": priami,
            "odynytsya": unit,
            "dzherelo": "орієнтовні укрупнені показники для попереднього кошторису",
            "prymitka": "Для офіційного кошторису застосувати чинні КНУ РЕКН / ДСТУ Б Д та поточні ціни регіону",
        },
        # зворотна сумісність зі старою схемою
        "trud_lyud_god": labor,
        "mashynisty_lyud_god": machinist,
    }
    return resursy, profile["sklad"]


def fill_norm(norm: dict, kompleks: str, nomer: int) -> dict:
    resursy, sklad = build_resources(
        kompleks,
        nomer,
        norm.get("nazva", ""),
        norm.get("odynytsya", ""),
        norm.get("shifr", ""),
    )
    norm["resursy"] = resursy
    if not norm.get("sklad_robit"):
        norm["sklad_robit"] = sklad
    if not norm.get("prymitka"):
        norm["prymitka"] = "Ресурси орієнтовні; звірити з офіційним РЕКН перед затвердженням кошторису"
    return norm


def fill_zbirnyk(z: dict) -> dict:
    kompleks = z["kompleks"]
    nomer = z["nomer"]
    for g in z.get("grupy", []):
        if not g.get("sklad_robit"):
            # склад групи з першої норми після заповнення
            pass
        for n in g.get("normy", []):
            fill_norm(n, kompleks, nomer)
        if not g.get("sklad_robit") and g.get("normy"):
            g["sklad_robit"] = list(g["normy"][0].get("sklad_robit") or [])
    # оновити примітки збірника
    notes = z.get("prymitky") or []
    marker = "Ресурсні показники — орієнтовні укрупнені"
    if not any(marker in x for x in notes):
        notes = [
            "Каталог робіт сформовано за структурою РЕКН ДСТУ Б Д.",
            f"{marker} (труд, машини, матеріали, прямі витрати в грн) для попереднього кошторису.",
            "Перед затвердженням інвесторського кошторису звірити з чинним КНУ РЕКН / ДСТУ та регіональними цінами.",
            "Шифр норми: збірник-група-норма (наприклад 8-5-1).",
        ]
        z["prymitky"] = notes
    return z
