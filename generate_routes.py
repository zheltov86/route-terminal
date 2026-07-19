"""
Генерация 50 маршрутов по Центральной России.
Локальный расчёт — без внешних API, мгновенно.
"""
import json
import time
import random
import math
from geopy.distance import geodesic

print("=" * 60)
print("  Генерация 50 маршрутов по Центральной России")
print("=" * 60)
start = time.time()

ГОРОДА = [
    {"name": "Москва",              "lat": 55.7558, "lon": 37.6173},
    {"name": "Калуга",              "lat": 54.5293, "lon": 36.2754},
    {"name": "Тула",                "lat": 54.1931, "lon": 37.6182},
    {"name": "Рязань",              "lat": 54.6292, "lon": 39.6919},
    {"name": "Владимир",            "lat": 56.1322, "lon": 40.4066},
    {"name": "Ярославль",           "lat": 57.6261, "lon": 39.8845},
    {"name": "Тверь",               "lat": 56.8587, "lon": 35.9176},
    {"name": "Великий Новгород",    "lat": 58.5214, "lon": 31.2755},
    {"name": "Псков",               "lat": 57.8136, "lon": 28.3496},
    {"name": "Брянск",              "lat": 53.2521, "lon": 34.3717},
    {"name": "Орёл",                "lat": 52.9681, "lon": 36.0694},
    {"name": "Курск",               "lat": 51.7304, "lon": 36.1929},
    {"name": "Липецк",              "lat": 52.6031, "lon": 39.5708},
    {"name": "Воронеж",             "lat": 51.6683, "lon": 39.1843},
    {"name": "Нижний Новгород",     "lat": 56.2965, "lon": 43.9361},
    {"name": "Иваново",             "lat": 56.9972, "lon": 40.9920},
    {"name": "Кострома",            "lat": 57.7677, "lon": 40.9268},
    {"name": "Санкт-Петербург",     "lat": 59.9343, "lon": 30.3351},
    {"name": "Серпухов",            "lat": 54.9146, "lon": 37.4067},
    {"name": "Чебоксары",           "lat": 56.1322, "lon": 47.2519},
    {"name": "Муром",               "lat": 55.5726, "lon": 41.7965},
    {"name": "Ногинск",             "lat": 55.8538, "lon": 38.4427},
    {"name": "Подольск",            "lat": 55.4298, "lon": 37.5547},
    {"name": "Химки",               "lat": 55.8903, "lon": 37.3928},
    {"name": "Мытищи",              "lat": 55.9104, "lon": 37.7364},
    {"name": "Одинцово",            "lat": 55.6781, "lon": 37.2636},
]

КОНТРАГЕНТЫ = [
    "ООО «ТехноПром»", "ЗАО «СтройМаш»", "ООО «АльфаСтрой»",
    "ПАО «ПромСвязь»", "ООО «МегаФуд»", "АО «ТрансЛогистик»",
    "ООО «ИнфоСервис»", "ООО «ПромТехника»", "ЗАО «ЭнергоСнаб»",
    "ООО «Восток-Трейд»", "ООО «НовыйГоризонт»", "АО «СеверСталь»",
    "ООО «Агро-Плюс»", "ПАО «Ростелеком»", "ООО «МедТехника»",
    "ООО «ЛогистикПро»", "АО «АвиаТехСервис»", "ООО «СтройДвор»",
    "ООО «ТехноМир»", "ЗАО «МеталлПром»",
]

ТОВАРЫ = ["Бумага А4", "Картридж HP", "Стол офисный", "Стул офисный", "Монитор", "Принтер", "Проектор", "Кабель HDMI", "Флешка 32ГБ", "Степлер"]
УЛИЦЫ = ["Ленина", "Пушкина", "Гагарина", "Мира", "Победы", "Центральная"]

def генератор_маршрута(lat1, lon1, lat2, lon2, num_points=80):
    """Генерирует реалистичный маршрут с петлями и отклонениями"""
    points = []
    dist = geodesic((lat1, lon1), (lat2, lon2)).km

    for i in range(num_points + 1):
        t = i / num_points

        # Базовая точка на прямой
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t

        # Добавляем отклонения (имитация изгибов дороги)
        # Больше отклонений в середине маршрута
        curve = math.sin(t * math.pi) * 0.02
        noise_lat = random.uniform(-0.008, 0.008) * (1 - abs(t - 0.5) * 2)
        noise_lon = random.uniform(-0.008, 0.008) * (1 - abs(t - 0.5) * 2)

        # Небольшой загиб в сторону (как реальная дорога)
        perp_lat = -((lon2 - lon1) / (dist / 111)) * curve
        perp_lon = ((lat2 - lat1) / (dist / 111)) * curve

        lat += noise_lat + perp_lat
        lon += noise_lon + perp_lon

        points.append([round(lat, 6), round(lon, 6)])

    # Добавляем финальную точку точно в назначение
    points[-1] = [lat2, lon2]

    return points

склад = {"lat": 55.7558, "lon": 37.6173}
used_names = set()
контрагенты_список = []

for _ in range(50):
    name = random.choice(КОНТРАГЕНТЫ)
    while name in used_names:
        name = random.choice(КОНТРАГЕНТЫ)
    used_names.add(name)
    город = random.choice(ГОРОДА)
    lat = город["lat"] + random.uniform(-0.03, 0.03)
    lon = город["lon"] + random.uniform(-0.03, 0.03)
    инн = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    контрагенты_список.append({
        "id": str(random.randint(100000, 999999)),
        "name": name,
        "inn": инн,
        "kpp": инн[:4] + str(random.randint(10, 99)) + "01",
        "city": город["name"],
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "phone": f"+7 ({random.randint(300,999)}) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}",
        "status": random.choice(["Активен", "Неактивен"]),
    })

print(f"Контрагенты: {len(контрагенты_список)}")

заказы = []
for i, кт in enumerate(контрагенты_список):
    sys.stdout.write(f"\r  Маршрут {i+1}/50: {кт['city']}...")
    sys.stdout.flush()

    route = генератор_маршрута(склад["lat"], склад["lon"], кт["lat"], кт["lon"])
    dist_km = round(geodesic((склад["lat"], склад["lon"]), (кт["lat"], кт["lon"])).km, 1)
    dur_h = round(dist_km / 80, 1)  # ~80 км/ч

    кол = random.randint(2, 5)
    позиции = []
    общая = 0
    for j in range(1, кол + 1):
        кол_во = round(random.uniform(1, 50), 0)
        цена = round(random.uniform(100, 50000), 2)
        сумма = round(кол_во * цена, 2)
        общая += сумма
        позиции.append({
            "line": j,
            "item": random.choice(ТОВАРЫ),
            "qty": кол_во,
            "unit": random.choice(["шт", "упак", "коробка"]),
            "price": цена,
            "sum": сумма,
            "vat": random.choice(["20%", "10%", "0%"]),
        })

    заказы.append({
        "number": f"ЗК-{random.randint(10000, 99999)}-26",
        "date": f"2026-07-{random.randint(1, 28):02d}",
        "counteragent_id": кт["id"],
        "counteragent_name": кт["name"],
        "counteragent_city": кт["city"],
        "warehouse": {"name": "Главный склад", "city": "Москва", "lat": склад["lat"], "lon": склад["lon"]},
        "delivery_point": {"city": кт["city"], "lat": кт["lat"], "lon": кт["lon"]},
        "route": route,
        "distance_km": dist_km,
        "duration_hours": dur_h,
        "sum": round(общая, 2),
        "vat_sum": round(общая * 0.2, 2),
        "status": random.choice(["Новый", "ВОбработке", "Согласован", "Выполняется", "Завершен"]),
        "items": позиции,
    })

elapsed = time.time() - start
total_dist = sum(з["distance_km"] for з in заказы)
total_points = sum(len(з["route"]) for з in заказы)

result = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "region": "Центральная Россия",
    "routes_count": len(заказы),
    "total_distance_km": round(total_dist, 1),
    "avg_distance_km": round(total_dist / len(заказы), 1),
    "total_route_points": total_points,
    "generation_time_sec": round(elapsed, 2),
    "warehouse": {"name": "Главный склад", "city": "Москва", "lat": 55.7558, "lon": 37.6173},
    "counteragents": контрагенты_список,
    "orders": заказы,
}

with open("routes_cache.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False)

print(f"\n\n{'=' * 60}")
print(f"  Готово за {round(elapsed, 2)} сек!")
print(f"  Маршрутов: {len(заказы)}")
print(f"  Расстояние: {round(total_dist):,} км")
print(f"  Точек polyline: {total_points:,}")
print(f"  Файл: routes_cache.json ({round(os.path.getsize('routes_cache.json')/1024)} КБ)")
print(f"{'=' * 60}")
