"""
Генерация маршрутов по Центральной России.
OSRM (роутинг по дорогам) + OpenStreetMap.
"""
import random
import math
import requests
from geopy.distance import geodesic

# ──────────────────────────────────────────────
# Центральная Россия — города и координаты
# ──────────────────────────────────────────────

ГОРОДА_ЦЕНТР = [
    {"name": "Москва",              "lat": 55.7558, "lon": 37.6173, "region": "Москва"},
    {"name": "Санкт-Петербург",     "lat": 59.9343, "lon": 30.3351, "region": "Ленинградская обл."},
    {"name": "Калуга",              "lat": 54.5293, "lon": 36.2754, "region": "Калужская обл."},
    {"name": "Тула",                "lat": 54.1931, "lon": 37.6182, "region": "Тульская обл."},
    {"name": "Рязань",              "lat": 54.6292, "lon": 39.6919, "region": "Рязанская обл."},
    {"name": "Владимир",            "lat": 56.1322, "lon": 40.4066, "region": "Владимирская обл."},
    {"name": "Иваново",             "lat": 56.9972, "lon": 40.9920, "region": "Ивановская обл."},
    {"name": "Ярославль",           "lat": 57.6261, "lon": 39.8845, "region": "Ярославская обл."},
    {"name": "Кострома",            "lat": 57.7677, "lon": 40.9268, "region": "Костромская обл."},
    {"name": "Тверь",               "lat": 56.8587, "lon": 35.9176, "region": "Тверская обл."},
    {"name": "Великий Новгород",    "lat": 58.5214, "lon": 31.2755, "region": "Новгородская обл."},
    {"name": "Псков",               "lat": 57.8136, "lon": 28.3496, "region": "Псковская обл."},
    {"name": "Брянск",              "lat": 53.2521, "lon": 34.3717, "region": "Брянская обл."},
    {"name": "Орёл",                "lat": 52.9681, "lon": 36.0694, "region": "Орловская обл."},
    {"name": "Курск",               "lat": 51.7304, "lon": 36.1929, "region": "Курская обл."},
    {"name": "Липецк",              "lat": 52.6031, "lon": 39.5708, "region": "Липецкая обл."},
    {"name": "Тамбов",              "lat": 52.7214, "lon": 41.4172, "region": "Тамбовская обл."},
    {"name": "Воронеж",             "lat": 51.6683, "lon": 39.1843, "region": "Воронежская обл."},
    {"name": "Нижний Новгород",     "lat": 56.2965, "lon": 43.9361, "region": "Нижегородская обл."},
    {"name": "Чебоксары",           "lat": 56.1322, "lon": 47.2519, "region": "Чувашская Республика"},
    {"name": "Муром",               "lat": 55.5726, "lon": 41.7965, "region": "Владимирская обл."},
    {"name": "Серпухов",            "lat": 54.9146, "lon": 37.4067, "region": "Московская обл."},
    {"name": "Ногинск",             "lat": 55.8538, "lon": 38.4427, "region": "Московская обл."},
    {"name": "Павловский Посад",    "lat": 55.7836, "lon": 38.6523, "region": "Московская обл."},
    {"name": "Электросталь",        "lat": 55.7914, "lon": 38.4469, "region": "Московская обл."},
    {"name": "Одинцово",            "lat": 55.6781, "lon": 37.2636, "region": "Московская обл."},
    {"name": "Химки",               "lat": 55.8903, "lon": 37.3928, "region": "Московская обл."},
    {"name": "Мытищи",              "lat": 55.9104, "lon": 37.7364, "region": "Московская обл."},
    {"name": "Люберцы",             "lat": 55.6772, "lon": 37.8947, "region": "Московская обл."},
    {"name": "Подольск",            "lat": 55.4298, "lon": 37.5547, "region": "Московская обл."},
    {"name": "Смоленск",            "lat": 54.7826, "lon": 32.0453, "region": "Смоленская обл."},
    {"name": "Белгород",            "lat": 50.5968, "lon": 36.5872, "region": "Белгородская обл."},
    {"name": "Старый Оскол",       "lat": 51.2966, "lon": 37.8357, "region": "Белгородская обл."},
    {"name": "Энгельс",             "lat": 51.4839, "lon": 46.1128, "region": "Саратовская обл."},
    {"name": "Балашиха",            "lat": 55.7496, "lon": 37.9275, "region": "Московская обл."},
    {"name": "Королёв",             "lat": 55.9166, "lon": 37.8567, "region": "Московская обл."},
    {"name": "Жуковский",           "lat": 55.5897, "lon": 38.1226, "region": "Московская обл."},
    {"name": "Домодедово",          "lat": 55.4372, "lon": 37.7603, "region": "Московская обл."},
    {"name": "Наро-Фоминск",        "lat": 55.3936, "lon": 36.7425, "region": "Московская обл."},
    {"name": "Коломна",             "lat": 55.0783, "lon": 38.7787, "region": "Московская обл."},
    {"name": "Орехово-Зуево",       "lat": 55.8058, "lon": 38.9614, "region": "Московская обл."},
    {"name": "Шатура",              "lat": 55.5731, "lon": 39.5447, "region": "Московская обл."},
    {"name": "Дмитров",             "lat": 56.3465, "lon": 37.5256, "region": "Московская обл."},
    {"name": "Клин",                "lat": 56.3331, "lon": 36.7328, "region": "Московская обл."},
    {"name": "Сергиев Посад",       "lat": 56.3098, "lon": 38.1332, "region": "Московская обл."},
    {"name": "Пушкино",             "lat": 56.0107, "lon": 37.8471, "region": "Московская обл."},
    {"name": "Щёлково",             "lat": 55.9162, "lon": 37.9958, "region": "Московская обл."},
    {"name": "Фрязино",             "lat": 55.9611, "lon": 38.0483, "region": "Московская обл."},
    # ══ СЕВЕР РОССИИ ══
    {"name": "Мурманск",            "lat": 68.9585, "lon": 33.0827, "region": "Мурманская обл."},
    {"name": "Архангельск",         "lat": 64.5399, "lon": 40.5152, "region": "Архангельская обл."},
    {"name": "Сыктывкар",           "lat": 61.6688, "lon": 50.8364, "region": "Коми"},
    {"name": "Воркута",             "lat": 67.4975, "lon": 64.0529, "region": "Коми"},
    {"name": "Вологда",             "lat": 59.2205, "lon": 39.8915, "region": "Вологодская обл."},
    {"name": "Череповец",           "lat": 59.1270, "lon": 37.9093, "region": "Вологодская обл."},
    {"name": "Петрозаводск",        "lat": 61.7976, "lon": 34.3470, "region": "Республика Карелия"},
    {"name": "Калининград",         "lat": 54.7065, "lon": 20.5109, "region": "Калининградская обл."},
    {"name": "Северодвинск",        "lat": 64.5635, "lon": 39.8302, "region": "Архангельская обл."},
    {"name": "Котлас",              "lat": 61.2500, "lon": 46.6500, "region": "Архангельская обл."},
    {"name": "Микунь",              "lat": 62.3500, "lon": 50.0833, "region": "Коми"},
    # ══ ЮГ РОССИИ ══
    {"name": "Сочи",                "lat": 43.6028, "lon": 39.7342, "region": "Краснодарский край"},
    {"name": "Краснодар",           "lat": 45.0355, "lon": 38.9753, "region": "Краснодарский край"},
    {"name": "Ростов-на-Дону",     "lat": 47.2357, "lon": 39.7015, "region": "Ростовская обл."},
    {"name": "Краснодар",           "lat": 45.0355, "lon": 38.9753, "region": "Краснодарский край"},
    {"name": "Ставрополь",          "lat": 45.0428, "lon": 41.9734, "region": "Ставропольский край"},
    {"name": "Волгоград",           "lat": 48.7080, "lon": 44.5133, "region": "Волгоградская обл."},
    {"name": "Астрахань",           "lat": 46.3498, "lon": 48.0408, "region": "Астраханская обл."},
    {"name": "Элиста",              "lat": 46.3083, "lon": 44.2558, "region": "Республика Калмыкия"},
    {"name": "Майкоп",              "lat": 44.6064, "lon": 40.0970, "region": "Республика Адыгея"},
    {"name": "Новочеркасск",        "lat": 47.4194, "lon": 40.0853, "region": "Ростовская обл."},
    {"name": "Шахты",               "lat": 47.7083, "lon": 40.2167, "region": "Ростовская обл."},
    {"name": "Таганрог",            "lat": 47.2362, "lon": 38.9244, "region": "Ростовская обл."},
    {"name": "Новопавловск",        "lat": 43.9567, "lon": 43.7356, "region": "Ставропольский край"},
    {"name": "Ессентуки",           "lat": 44.0392, "lon": 42.8630, "region": "Ставропольский край"},
    {"name": "Кисловодск",          "lat": 43.9050, "lon": 42.7211, "region": "Ставропольский край"},
    {"name": "Минеральные Воды",    "lat": 44.2111, "lon": 43.1350, "region": "Ставропольский край"},
]

УЛИЦЫ = ["Ленина", "Пушкина", "Гагарина", "Мира", "Советская", "Кирова", "Чехова", "Победы", "Мира", "Центральная"]

КОНТРАГЕНТЫ_НАЗВАНИЯ = [
    "ООО «ТехноПром»", "ЗАО «СтройМаш»", "ООО «АльфаСтрой»",
    "ПАО «ПромСвязь»", "ООО «МегаФуд»", "АО «ТрансЛогистик»",
    "ООО «ИнфоСервис»", "ООО «ПромТехника»", "ЗАО «ЭнергоСнаб»",
    "ООО «Восток-Трейд»", "ООО «НовыйГоризонт»", "АО «СеверСталь»",
    "ООО «Агро-Плюс»", "ПАО «Ростелеком»", "ООО «МедТехника»",
    "ООО «ЛогистикПро»", "АО «АвиаТехСервис»", "ООО «СтройДвор»",
    "ООО «ТехноМир»", "ЗАО «МеталлПром»",
]

ТОВАРЫ = [
    "Бумага А4", "Картридж HP", "Стол офисный", "Стул офисный",
    "Монитор 24\"", "Клавиатура", "Принтер", "Сканер",
    "Маркер", "Ручка", "Тетрадь", "Степлер",
    "Проектор", "Кабель HDMI", "Флешка 32ГБ", "Доска магнитная",
]

ЕДИНИЦЫ = ["шт", "упак", "коробка", "комплект"]
СТАТУСЫ_З = ["Новый", "ВОбработке", "Согласован", "Выполняется", "Завершен"]

# ──────────────────────────────────────────────
# OSRM — роутинг по дорогам
# ──────────────────────────────────────────────

OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

def get_route_road(lat1, lon1, lat2, lon2):
    """Получить маршрут по дорогам через OSRM. Возвращает координаты polyline."""
    try:
        url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            coords = route["geometry"]["coordinates"]  # [[lon, lat], ...]
            # Конвертируем в [[lat, lon], ...]
            coords_latlon = [[c[1], c[0]] for c in coords]
            return {
                "coordinates": coords_latlon,
                "distance_km": round(route["distance"] / 1000, 1),
                "duration_hours": round(route["duration"] / 3600, 1),
            }
    except Exception as e:
        pass
    # Fallback: прямая линия
    dist = geodesic((lat1, lon1), (lat2, lon2)).km
    return {
        "coordinates": [[lat1, lon1], [lat2, lon2]],
        "distance_km": round(dist, 1),
        "duration_hours": round(dist / 80, 1),  # ~80 км/ч
    }

def get_route_with_stops(起点_lat, 起点_lon, stops):
    """Маршрут с остановками. stops = [(lat, lon), ...]"""
    all_coords = []
    total_distance = 0
    total_duration = 0

    current_lat, current_lon = 起点_lat, 起点_lon

    for stop_lat, stop_lon in stops:
        route = get_route_road(current_lat, current_lon, stop_lat, stop_lon)
        if all_coords:
            all_coords.extend(route["coordinates"][1:])  # пропускаем первую точку (дубль)
        else:
            all_coords.extend(route["coordinates"])
        total_distance += route["distance_km"]
        total_duration += route["duration_hours"]
        current_lat, current_lon = stop_lat, stop_lon

    return {
        "coordinates": all_coords,
        "distance_km": round(total_distance, 1),
        "duration_hours": round(total_duration, 1),
    }

# ──────────────────────────────────────────────
# Генераторы
# ──────────────────────────────────────────────

def инн():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def кпп(значение):
    return значение[:4] + str(random.randint(10, 99)) + '01'

def телефон():
    return f"+7 ({random.randint(300,999)}) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}"

def адрес(город):
    return f"г. {город['name']}, ул. {random.choice(УЛИЦЫ)}, д. {random.randint(1,100)}"

def координаты_рядом(город, radius_km=3):
    lat = город["lat"] + random.uniform(-radius_km/111, radius_km/111)
    lon = город["lon"] + random.uniform(-radius_km/111, radius_km/111) / math.cos(math.radians(город["lat"]))
    return round(lat, 6), round(lon, 6)

def контрагенты(count=5):
    результат = []
    used = set()
    for _ in range(count):
        name = random.choice(КОНТРАГЕНТЫ_НАЗВАНИЯ)
        while name in used:
            name = random.choice(КОНТРАГЕНТЫ_НАЗВАНИЯ)
        used.add(name)
        город = random.choice(ГОРОДА_ЦЕНТР)
        lat, lon = координаты_рядом(город)
        инн_знач = инн()
        результат.append({
            "id": str(random.randint(100000, 999999)),
            "name": name,
            "inn": инн_знач,
            "kpp": кпп(инн_знач),
            "city": город["name"],
            "region": город["region"],
            "address": адрес(город),
            "phone": телефон(),
            "lat": lat,
            "lon": lon,
            "status": random.choice(["Активен", "Неактивен"]),
        })
    return результат

def маршрут_заказа(склад_lat, склад_lon, кт):
    """Маршрут доставки от склада до контрагента по дорогам"""
    route = get_route_road(склад_lat, склад_lon, кт["lat"], кт["lon"])
    return {
        "from": {"name": "Главный склад (Москва)", "lat": склад_lat, "lon": склад_lon},
        "to": {"name": кт["name"], "city": кт["city"], "lat": кт["lat"], "lon": кт["lon"]},
        "route": route["coordinates"],
        "distance_km": route["distance_km"],
        "duration_hours": route["duration_hours"],
    }

def заказы(count=10, контрагенты_список=None):
    if not контрагенты_список:
        контрагенты_список = контрагенты(5)

    склад = {"lat": 55.7558, "lon": 37.6173}  # Москва
    результат = []

    for _ in range(count):
        кт = random.choice(контрагенты_список)
        route = маршрут_заказа(склад["lat"], склад["lon"], кт)

        кол = random.randint(2, 6)
        позиции = []
        общая = 0
        for i in range(1, кол + 1):
            кол_во = round(random.uniform(1, 50), 0)
            цена = round(random.uniform(100, 50000), 2)
            сумма = round(кол_во * цена, 2)
            общая += сумма
            позиции.append({
                "line": i,
                "item": random.choice(ТОВАРЫ),
                "qty": кол_во,
                "unit": random.choice(ЕДИНИЦЫ),
                "price": цена,
                "sum": сумма,
                "vat": random.choice(["20%", "10%", "0%"]),
            })

        результат.append({
            "number": f"ЗК-{random.randint(10000, 99999)}-26",
            "date": f"2026-07-{random.randint(1, 28):02d}",
            "counteragent_id": кт["id"],
            "counteragent_name": кт["name"],
            "counteragent_city": кт["city"],
            "counteragent_region": кт["region"],
            "warehouse": {"name": "Главный склад", "city": "Москва", "lat": склад["lat"], "lon": склад["lon"]},
            "delivery_point": {"city": кт["city"], "lat": кт["lat"], "lon": кт["lon"]},
            "route": route["route"],
            "distance_km": route["distance_km"],
            "duration_hours": route["duration_hours"],
            "sum": round(общая, 2),
            "vat_sum": round(общая * 0.2, 2),
            "status": random.choice(СТАТУСЫ_З),
            "items": позиции,
        })

    return результат

def json_full(count_orders=5, count_counteragents=5):
    ктс = контрагенты(count_counteragents)
    заказы_список = заказы(count_orders, ктс)
    return {
        "service": "1C Data Generator",
        "version": "1.1.0",
        "region": "Центральная Россия",
        "warehouse": {"name": "Главный склад", "city": "Москва", "lat": 55.7558, "lon": 37.6173},
        "counteragents": ктс,
        "orders": заказы_список,
    }
