"""
Выгрузка XML и JSON в формате 1С:EnterpriseData
Строго по примеру Тест.xml — XML как строка, без lxml namespace issues.
"""
import random
import uuid
import os
from datetime import datetime

OUTPUT_DIR = r"D:\DATA"

# ──────────────────────────────────────────────
# Данные
# ──────────────────────────────────────────────

ТОВАРЫ = [
    {"name": "Сковорода чугунная 26см",       "price": 3490,   "unit": "шт"},
    {"name": "Кастрюля нержавеющая 3л",        "price": 2890,   "unit": "шт"},
    {"name": "Нож кухонный поварской 20см",    "price": 1990,   "unit": "шт"},
    {"name": "Доска разделочная деревянная",   "price": 890,    "unit": "шт"},
    {"name": "Набор кухонных полотенец 3шт",   "price": 1290,   "unit": "комплект"},
    {"name": "Ведро пластиковое 12л",          "price": 490,    "unit": "шт"},
    {"name": "Таз пластиковый 10л",            "price": 390,    "unit": "шт"},
    {"name": "Швабра с отжимом",               "price": 1890,   "unit": "шт"},
    {"name": "Мусорные пакеты 60л 30шт",       "price": 290,    "unit": "упак"},
    {"name": "Губки для посуды 5шт",           "price": 190,    "unit": "упак"},
    {"name": "Средство для мытья посуды 500мл","price": 180,    "unit": "шт"},
    {"name": "Освежитель воздуха спрей",       "price": 290,    "unit": "шт"},
    {"name": "Плед флисовый 150x200",          "price": 2490,   "unit": "шт"},
    {"name": "Подушки наполнитель 50x70 2шт",  "price": 1890,   "unit": "комплект"},
    {"name": "Чайник электрический 1.7л",      "price": 2490,   "unit": "шт"},
    {"name": "Тостер 2-slot",                  "price": 3290,   "unit": "шт"},
    {"name": "Мультиварка 5л",                 "price": 5990,   "unit": "шт"},
    {"name": "Пылесос ручной беспроводной",    "price": 12990,  "unit": "шт"},
    {"name": "Утюг с паром 2400Вт",            "price": 3990,   "unit": "шт"},
    {"name": "Сушилка для белья напольная",    "price": 2990,   "unit": "шт"},
]

КОНТРАГЕНТЫ = [
    {"name": "ООО «ДомашнийУют»",  "full": "ООО «ДомашнийУют»",  "inn": "7701234567", "kpp": "770101001"},
    {"name": "ООО «КухонныйМир»",  "full": "ООО «КухонныйМир»",  "inn": "7702345678", "kpp": "770201001"},
    {"name": "ИП Смирнов А.В.",    "full": "ИП Смирнов Андрей Владимирович", "inn": "7703456789", "kpp": "770301001"},
    {"name": "ООО «УютныйДом»",    "full": "ООО «УютныйДом»",    "inn": "7704567890", "kpp": "770401001"},
    {"name": "ЗАО «ТехноДом»",     "full": "ЗАО «ТехноДом»",     "inn": "7705678901", "kpp": "770501001"},
]

ВАЛЮТА_REF = "7e3e0ef4-8295-11f1-8af8-04ecd881cf53"
ОРГАНИЗАЦИЯ_REF = "553d56f1-8295-11f1-8af8-04ecd881cf53"
ПОЛЬЗОВАТЕЛЬ_REF = "aa00559e-ad84-4494-88fd-f0826edc46f0"

def ref():
    return str(uuid.uuid4())

def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def indent(level):
    return "\t" * level

def gen_order(n):
    к = random.choice(КОНТРАГЕНТЫ)
    дата = datetime(2026, 7, random.randint(1, 18))
    товары = random.sample(ТОВАРЫ, 5)
    строки = []
    итого = 0
    for i, т in enumerate(товары, 1):
        кол = random.randint(1, 10)
        сумма = round(т["price"] * кол, 2)
        ндс = round(сумма * 0.2, 2)
        итого += сумма
        строки.append({"n": i, **т, "qty": кол, "sum": сумма, "nds": ндс})
    return {"ref": ref(), "number": f"ЗК-{n:05d}", "date": дата.strftime("%Y-%m-%dT%H:%M:%S"),
            "kont": к, "sum": round(итого, 2), "items": строки,
            "comment": f"Заказ от {дата.strftime('%d.%m.%Y')} — {к['name']}"}

# ──────────────────────────────────────────────
# XML (ручная генерация, точно как Тест.xml)
# ──────────────────────────────────────────────

def build_xml(orders):
    # Кэш ссылок на контрагентов
    kont_refs = {}
    for к in КОНТРАГЕНТЫ:
        kont_refs[к["name"]] = ref()

    # Ссылки на единицы измерения
    unit_refs = {"шт": ref(), "комплект": ref(), "упак": ref()}

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = []

    # Заголовок (точно как в Тест.xml)
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<Message xmlns:msg="http://www.1c.ru/SSL/Exchange/Message" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">')
    lines.append(f'{indent(1)}<msg:Header>')
    lines.append(f'{indent(2)}<msg:Format>http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8</msg:Format>')
    lines.append(f'{indent(2)}<msg:CreationDate>{now}</msg:CreationDate>')
    lines.append(f'{indent(2)}<msg:AvailableVersion>1.8</msg:AvailableVersion>')
    lines.append(f'{indent(1)}</msg:Header>')

    # Body — default namespace (без префикса, как в Тест.xml)
    lines.append(f'{indent(1)}<Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8">')

    # === Валюта ===
    lines.append(f'{indent(2)}<Справочник.Валюты>')
    lines.append(f'{indent(3)}<КлючевыеСвойства>')
    lines.append(f'{indent(4)}<Ссылка>{ВАЛЮТА_REF}</Ссылка>')
    lines.append(f'{indent(4)}<ДанныеКлассификатора>')
    lines.append(f'{indent(5)}<Код>643</Код>')
    lines.append(f'{indent(5)}<Наименование>руб.</Наименование>')
    lines.append(f'{indent(4)}</ДанныеКлассификатора>')
    lines.append(f'{indent(3)}</КлючевыеСвойства>')
    lines.append(f'{indent(3)}<ПараметрыПрописи>рубль, рубля, рублей, м, копейка, копейки, копеек, ж, 2 знака</ПараметрыПрописи>')
    lines.append(f'{indent(2)}</Справочник.Валюты>')

    # === Организация ===
    lines.append(f'{indent(2)}<Справочник.Организации>')
    lines.append(f'{indent(3)}<КлючевыеСвойства>')
    lines.append(f'{indent(4)}<Ссылка>{ОРГАНИЗАЦИЯ_REF}</Ссылка>')
    lines.append(f'{indent(4)}<Наименование>Управленческая организация</Наименование>')
    lines.append(f'{indent(4)}<ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо>')
    lines.append(f'{indent(3)}</КлючевыеСвойства>')
    lines.append(f'{indent(3)}<Префикс>УУ</Префикс>')
    lines.append(f'{indent(2)}</Справочник.Организации>')

    # === Пользователь ===
    lines.append(f'{indent(2)}<Справочник.Пользователи>')
    lines.append(f'{indent(3)}<КлючевыеСвойства>')
    lines.append(f'{indent(4)}<Ссылка>{ПОЛЬЗОВАТЕЛЬ_REF}</Ссылка>')
    lines.append(f'{indent(4)}<Наименование>&lt;Не указан&gt;</Наименование>')
    lines.append(f'{indent(3)}</КлючевыеСвойства>')
    lines.append(f'{indent(2)}</Справочник.Пользователи>')

    # === Единицы измерения (как в Тест.xml) ===
    for code, name, full in [("796 ", "шт", "Штука"), ("335 ", "комплект", "Комплект"), ("778 ", "упак", "Упаковка")]:
        ukey = "шт" if name == "шт" else ("комплект" if name == "комплект" else "упак")
        lines.append(f'{indent(2)}<Справочник.ЕдиницыИзмерения>')
        lines.append(f'{indent(3)}<КлючевыеСвойства>')
        lines.append(f'{indent(4)}<Ссылка>{unit_refs[ukey]}</Ссылка>')
        lines.append(f'{indent(4)}<ДанныеКлассификатора>')
        lines.append(f'{indent(5)}<Код>{code}</Код>')
        lines.append(f'{indent(5)}<Наименование>{name}</Наименование>')
        lines.append(f'{indent(4)}</ДанныеКлассификатора>')
        lines.append(f'{indent(3)}</КлючевыеСвойства>')
        lines.append(f'{indent(3)}<НаименованиеПолное>{full}</НаименованиеПолное>')
        lines.append(f'{indent(2)}</Справочник.ЕдиницыИзмерения>')

    # === Статья доходов ===
    lines.append(f'{indent(2)}<Справочник.СтатьиДоходов>')
    lines.append(f'{indent(3)}<КлючевыеСвойства>')
    lines.append(f'{indent(4)}<Ссылка>7e3e0ef7-8295-11f1-8af8-04ecd881cf53</Ссылка>')
    lines.append(f'{indent(4)}<КодВПрограмме>000000001</КодВПрограмме>')
    lines.append(f'{indent(4)}<Наименование>Выручка от продаж</Наименование>')
    lines.append(f'{indent(3)}</КлючевыеСвойства>')
    lines.append(f'{indent(2)}</Справочник.СтатьиДоходов>')

    # === Контрагенты ===
    for к in КОНТРАГЕНТЫ:
        lines.append(f'{indent(2)}<Справочник.Контрагенты>')
        lines.append(f'{indent(3)}<КлючевыеСвойства>')
        lines.append(f'{indent(4)}<Ссылка>{kont_refs[к["name"]]}</Ссылка>')
        lines.append(f'{indent(4)}<Наименование>{xml_escape(к["name"])}</Наименование>')
        lines.append(f'{indent(4)}<НаименованиеПолное>{xml_escape(к["full"])}</НаименованиеПолное>')
        lines.append(f'{indent(4)}<ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо>')
        lines.append(f'{indent(3)}</КлючевыеСвойства>')
        lines.append(f'{indent(2)}</Справочник.Контрагенты>')

    # === Заказы клиентов ===
    for order in orders:
        к = order["kont"]
        lines.append(f'{indent(2)}<Документ.ЗаказКлиента>')

        # Ключевые свойства
        lines.append(f'{indent(3)}<КлючевыеСвойства>')
        lines.append(f'{indent(4)}<Ссылка>{order["ref"]}</Ссылка>')
        lines.append(f'{indent(4)}<Номер>{order["number"]}</Номер>')
        lines.append(f'{indent(4)}<Дата>{order["date"]}</Дата>')
        lines.append(f'{indent(4)}<Проведен>true</Проведен>')
        lines.append(f'{indent(3)}</КлючевыеСвойства>')

        # Организация
        lines.append(f'{indent(3)}<Организация>')
        lines.append(f'{indent(4)}<Ссылка>{ОРГАНИЗАЦИЯ_REF}</Ссылка>')
        lines.append(f'{indent(4)}<Наименование>Управленческая организация</Наименование>')
        lines.append(f'{indent(3)}</Организация>')

        # Контрагент
        lines.append(f'{indent(3)}<Контрагент>')
        lines.append(f'{indent(4)}<Ссылка>{kont_refs[к["name"]]}</Ссылка>')
        lines.append(f'{indent(4)}<Наименование>{xml_escape(к["name"])}</Наименование>')
        lines.append(f'{indent(4)}<НаименованиеПолное>{xml_escape(к["full"])}</НаименованиеПолное>')
        lines.append(f'{indent(4)}<ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо>')
        lines.append(f'{indent(3)}</Контрагент>')

        # Валюта
        lines.append(f'{indent(3)}<Валюта>')
        lines.append(f'{indent(4)}<Ссылка>{ВАЛЮТА_REF}</Ссылка>')
        lines.append(f'{indent(4)}<Наименование>руб.</Наименование>')
        lines.append(f'{indent(3)}</Валюта>')

        # Сумма
        lines.append(f'{indent(3)}<Сумма>{order["sum"]}</Сумма>')

        # Комментарий
        lines.append(f'{indent(3)}<Комментарий>{xml_escape(order["comment"])}</Комментарий>')

        # Товары
        lines.append(f'{indent(3)}<Товары>')
        for item in order["items"]:
            ukey = item["unit"]
            lines.append(f'{indent(4)}<Строка>')
            lines.append(f'{indent(5)}<НомерСтрокиДокумента>{item["n"]}</НомерСтрокиДокумента>')
            lines.append(f'{indent(5)}<ДанныеНоменклатуры>')
            lines.append(f'{indent(6)}<Ссылка>{ref()}</Ссылка>')
            lines.append(f'{indent(6)}<Наименование>{xml_escape(item["name"])}</Наименование>')
            lines.append(f'{indent(5)}</ДанныеНоменклатуры>')
            lines.append(f'{indent(5)}<ЕдиницаИзмерения>')
            lines.append(f'{indent(6)}<Ссылка>{unit_refs[ukey]}</Ссылка>')
            lines.append(f'{indent(6)}<Наименование>{item["unit"]}</Наименование>')
            lines.append(f'{indent(5)}</ЕдиницаИзмерения>')
            lines.append(f'{indent(5)}<Количество>{item["qty"]}</Количество>')
            lines.append(f'{indent(5)}<Цена>{item["price"]}</Цена>')
            lines.append(f'{indent(5)}<Сумма>{item["sum"]}</Сумма>')
            lines.append(f'{indent(5)}<СтавкаНДС>НДС20</СтавкаНДС>')
            lines.append(f'{indent(5)}<СуммаНДС>{item["nds"]}</СуммаНДС>')
            lines.append(f'{indent(4)}</Строка>')
        lines.append(f'{indent(3)}</Товары>')

        lines.append(f'{indent(2)}</Документ.ЗаказКлиента>')

    lines.append(f'{indent(1)}</Body>')
    lines.append('</Message>')

    return "\n".join(lines)

def save_xml(orders):
    xml = build_xml(orders)
    path = os.path.join(OUTPUT_DIR, "Выгрузка_Заказы.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"XML: {path} ({os.path.getsize(path) // 1024} КБ)")
    return path

def save_json(orders):
    import json
    data = {
        "format": "EnterpriseData/1.8",
        "generated_at": datetime.now().isoformat(),
        "orders": [{
            "ref": o["ref"], "number": o["number"], "date": o["date"], "posted": True,
            "organization": {"ref": ОРГАНИЗАЦИЯ_REF, "name": "Управленческая организация"},
            "kontagent": {"name": o["kont"]["name"], "inn": o["kont"]["inn"], "kpp": o["kont"]["kpp"]},
            "currency": {"ref": ВАЛЮТА_REF, "code": "643", "name": "руб."},
            "sum": o["sum"], "comment": o["comment"],
            "items": [{"line": it["n"], "name": it["name"], "qty": it["qty"], "unit": it["unit"],
                        "price": it["price"], "sum": it["sum"], "vat": "НДС20", "vat_sum": it["nds"]}
                       for it in o["items"]],
        } for o in orders]
    }
    path = os.path.join(OUTPUT_DIR, "Выгрузка_Заказы.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON: {path} ({os.path.getsize(path) // 1024} КБ)")
    return path

if __name__ == "__main__":
    print("=" * 60)
    print("  Выгрузка 1С:EnterpriseData")
    print("  5 заказов · 5 товаров для дома")
    print("=" * 60)

    orders = [gen_order(i + 1) for i in range(5)]

    for i, o in enumerate(orders, 1):
        print(f"\n  Заказ {o['number']}: {o['kont']['name']} — {o['sum']:,} руб.")
        for it in o["items"]:
            print(f"    {it['n']}. {it['name']} — {it['qty']} × {it['price']} = {it['sum']}")

    save_xml(orders)
    save_json(orders)
    print(f"\n  Готово! Файлы в {OUTPUT_DIR}")
