"""
logic.py — Изолированный модуль алгоритмов расчёта.
Все данные генерируются здесь. app.py только обращается за данными.
"""
import random
import math
from datetime import datetime

# ─── Справочники ───

ГОРОДА = [
    {"name": "Москва", "lat": 55.7558, "lon": 37.6173},
    {"name": "Санкт-Петербург", "lat": 59.9343, "lon": 30.3351},
    {"name": "Калуга", "lat": 54.5293, "lon": 36.2754},
    {"name": "Тула", "lat": 54.1931, "lon": 37.6182},
    {"name": "Рязань", "lat": 54.6292, "lon": 39.6919},
    {"name": "Владимир", "lat": 56.1322, "lon": 40.4066},
    {"name": "Ярославль", "lat": 57.6261, "lon": 39.8845},
    {"name": "Кострома", "lat": 57.7677, "lon": 40.9268},
    {"name": "Тверь", "lat": 56.8587, "lon": 35.9176},
    {"name": "Великий Новгород", "lat": 58.5214, "lon": 31.2755},
    {"name": "Псков", "lat": 57.8136, "lon": 28.3496},
    {"name": "Брянск", "lat": 53.2521, "lon": 34.3717},
    {"name": "Орёл", "lat": 52.9681, "lon": 36.0694},
    {"name": "Курск", "lat": 51.7304, "lon": 36.1929},
    {"name": "Липецк", "lat": 52.6031, "lon": 39.5708},
    {"name": "Воронеж", "lat": 51.6683, "lon": 39.1843},
    {"name": "Нижний Новгород", "lat": 56.2965, "lon": 43.9361},
    {"name": "Смоленск", "lat": 54.7826, "lon": 32.0453},
    {"name": "Белгород", "lat": 50.5968, "lon": 36.5872},
    {"name": "Саратов", "lat": 51.5336, "lon": 46.0342},
    {"name": "Сочи", "lat": 43.6028, "lon": 39.7342},
    {"name": "Краснодар", "lat": 45.0355, "lon": 38.9753},
    {"name": "Ростов-на-Дону", "lat": 47.2357, "lon": 39.7015},
    {"name": "Волгоград", "lat": 48.7080, "lon": 44.5133},
    {"name": "Казань", "lat": 55.7887, "lon": 49.1221},
    {"name": "Уфа", "lat": 54.7388, "lon": 55.9721},
    {"name": "Самара", "lat": 53.1959, "lon": 50.1002},
    {"name": "Екатеринбург", "lat": 56.8389, "lon": 60.6057},
    {"name": "Челябинск", "lat": 55.1644, "lon": 61.4368},
    {"name": "Пермь", "lat": 58.0105, "lon": 56.2502},
]

СКЛАД = {"name": "Главный склад", "city": "Москва", "lat": 55.7558, "lon": 37.6173}

КОНТРАГЕНТЫ = [
    "ООО «ТехноПром»", "ЗАО «СтройМаш»", "ООО «АльфаСтрой»", "ПАО «ПромСвязь»",
    "ООО «МегаФуд»", "АО «ТрансЛогистик»", "ООО «ИнфоСервис»", "ООО «ПромТехника»",
    "ЗАО «ЭнергоСнаб»", "ООО «Восток-Трейд»", "ООО «НовыйГоризонт»", "АО «СеверСталь»",
    "ООО «Агро-Плюс»", "ПАО «Ростелеком»", "ООО «МедТехника»", "ООО «ЛогистикПро»",
    "АО «АвиаТехСервис»", "ООО «СтройДвор»", "ООО «ТехноМир»", "ЗАО «МеталлПром»",
]

ТОВАРЫ = [
    {"name": "Бумага А4", "price": 390, "unit": "упак"},
    {"name": "Картридж HP", "price": 2890, "unit": "шт"},
    {"name": "Стол офисный", "price": 12990, "unit": "шт"},
    {"name": "Стул офисный", "price": 8990, "unit": "шт"},
    {"name": "Монитор 24\"", "price": 18990, "unit": "шт"},
    {"name": "Принтер лазерный", "price": 24990, "unit": "шт"},
    {"name": "Кабель HDMI", "price": 590, "unit": "шт"},
    {"name": "Флешка 32ГБ", "price": 890, "unit": "шт"},
    {"name": "Проектор", "price": 34990, "unit": "шт"},
    {"name": "Доска магнитная", "price": 5990, "unit": "шт"},
    {"name": "Пылесос", "price": 12990, "unit": "шт"},
    {"name": "Утюг", "price": 3990, "unit": "шт"},
    {"name": "Чайник", "price": 2490, "unit": "шт"},
    {"name": "Мультиварка", "price": 5990, "unit": "шт"},
    {"name": "Кофемашина", "price": 15990, "unit": "шт"},
]

СТАТУСЫ = ["New", "Processing", "Confirmed", "InTransit", "Delivered"]
ГРУЗЫ = ["Строительные материалы", "Электроника", "Канцелярия", "Мебель", "Бытовая техника", "Продукты", "Текстиль"]

# ─── Алгоритмы расчёта ───

def расстояние(lat1, lon1, lat2, lon2):
    """Расчёт расстояния между двумя точками (формула гаверсинусов), км."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 1)


def стоимость_перевозки(distance_km, weight_t):
    """Алгоритм расчёта стоимости перевозки по тарифу фуры."""
    if distance_km < 100: rate = 55
    elif distance_km < 300: rate = 45
    elif distance_km < 500: rate = 42
    elif distance_km < 1000: rate = 38
    else: rate = 35
    base = round(distance_km * rate)
    if weight_t > 20:
        base = round(base * (1 + (weight_t - 20) * 0.02))
    return round(base / 500) * 500


def время_в_пути(distance_km):
    """Расчёт времени в пути (средняя скорость 80 км/ч), часов."""
    return round(distance_km / 80, 1)


# ─── Генераторы ───

def генерация_точки(город):
    """Случайная точка рядом с городом (радиус ~3 км)."""
    lat = город["lat"] + random.uniform(-0.03, 0.03)
    lon = город["lon"] + random.uniform(-0.03, 0.03)
    return round(lat, 6), round(lon, 6)


def генерация_заказа():
    """Генерация одного заказа: пункт А (склад) → пункт Б (город назначения)."""
    город = random.choice(ГОРОДА)
    lat, lon = генерация_точки(город)
    дистанция = расстояние(СКЛАД["lat"], СКЛАД["lon"], lat, lon)
    вес = round(random.uniform(10, 22), 1)
    стоимость = стоимость_перевозки(дистанция, вес)
    время = время_в_пути(дистанция)

    items = random.sample(ТОВАРЫ, random.randint(2, 5))
    order_items = []
    total = 0
    for i, t in enumerate(items, 1):
        qty = random.randint(1, 20)
        s = round(t["price"] * qty, 2)
        total += s
        order_items.append({"line": i, "item": t["name"], "qty": qty, "unit": t["unit"], "price": t["price"], "sum": s})

    is_sbor = random.random() < 0.15
    cargo_type = "сборный" if is_sbor else "фура"
    cargo = " + ".join(random.sample(ГРУЗЫ, random.randint(2, 3))) if is_sbor else random.choice(ГРУЗЫ)
    weight = round(random.uniform(3, 12), 1) if is_sbor else вес

    return {
        "number": "ZK-" + str(random.randint(10000, 99999)) + "-26",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "counteragent": random.choice(КОНТРАГЕНТЫ),
        "from_city": СКЛАД["city"],
        "from_lat": СКЛАД["lat"],
        "from_lon": СКЛАД["lon"],
        "city": город["name"],
        "lat": lat,
        "lon": lon,
        "cargo": cargo,
        "cargo_type": cargo_type,
        "weight": weight,
        "distance_km": дистанция,
        "duration_hours": время,
        "transport_cost": стоимость,
        "sum": round(total, 2),
        "status": random.choice(СТАТУСЫ),
        "items": order_items,
        "has_route": not is_sbor,  # Сборные заказы — без маршрута, просто точка
    }


def генерация_заказов(count=1):
    """Генерация нескольких заказов."""
    return [генерация_заказа() for _ in range(count)]


def получить_города():
    """Список всех городов для справочника."""
    return ГОРОДА


def получить_склад():
    """Данные склада."""
    return СКЛАД
