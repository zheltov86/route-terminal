"""
Генерация 50 маршрутов по дорогам (OSRM) + адреса (Nominatim).
Кэширует результаты для быстрой загрузки.
"""
import json, time, random, os, sys
import requests
from geopy.distance import geodesic

CACHE = "routes_cache.json"
OSRM = "http://router.project-osrm.org/route/v1/driving"
NOMINATIM = "https://nominatim.openstreetmap.org/reverse"

ГОРОДА = [
    {"name": "Москва", "lat": 55.7558, "lon": 37.6173},
    {"name": "Калуга", "lat": 54.5293, "lon": 36.2754},
    {"name": "Тула", "lat": 54.1931, "lon": 37.6182},
    {"name": "Рязань", "lat": 54.6292, "lon": 39.6919},
    {"name": "Владимир", "lat": 56.1322, "lon": 40.4066},
    {"name": "Ярославль", "lat": 57.6261, "lon": 39.8845},
    {"name": "Тверь", "lat": 56.8587, "lon": 35.9176},
    {"name": "СПб", "lat": 59.9343, "lon": 30.3351},
    {"name": "Брянск", "lat": 53.2521, "lon": 34.3717},
    {"name": "Орёл", "lat": 52.9681, "lon": 36.0694},
    {"name": "Курск", "lat": 51.7304, "lon": 36.1929},
    {"name": "Липецк", "lat": 52.6031, "lon": 39.5708},
    {"name": "Воронеж", "lat": 51.6683, "lon": 39.1843},
    {"name": "Нижний Новгород", "lat": 56.2965, "lon": 43.9361},
    {"name": "Иваново", "lat": 56.9972, "lon": 40.9920},
    {"name": "Кострома", "lat": 57.7677, "lon": 40.9268},
    {"name": "Псков", "lat": 57.8136, "lon": 28.3496},
    {"name": "Новгород", "lat": 58.5214, "lon": 31.2755},
    {"name": "Чебоксары", "lat": 56.1322, "lon": 47.2519},
    {"name": "Муром", "lat": 55.5726, "lon": 41.7965},
    {"name": "Серпухов", "lat": 54.9146, "lon": 37.4067},
    {"name": "Подольск", "lat": 55.4298, "lon": 37.5547},
    {"name": "Химки", "lat": 55.8903, "lon": 37.3928},
    {"name": "Мытищи", "lat": 55.9104, "lon": 37.7364},
    {"name": "Одинцово", "lat": 55.6781, "lon": 37.2636},
]

ИМЕНА = [
    "ООО «ТехноПром»", "ЗАО «СтройМаш»", "ООО «АльфаСтрой»",
    "ПАО «ПромСвязь»", "ООО «МегаФуд»", "АО «ТрансЛогистик»",
    "ООО «ИнфоСервис»", "ООО «ПромТехника»", "ЗАО «ЭнергоСнаб»",
    "ООО «Восток-Трейд»", "ООО «НовыйГоризонт»", "АО «СеверСталь»",
    "ООО «Агро-Плюс»", "ПАО «Ростелеком»", "ООО «МедТехника»",
    "ООО «ЛогистикПро»", "АО «АвиаТехСервис»", "ООО «СтройДвор»",
    "ООО «ТехноМир»", "ЗАО «МеталлПром»", "ООО «Форвард»",
    "ООО «Спектр»", "АО «Импульс»", "ЗАО «Восток»", "ООО «Гарант»",
]

ТОВАРЫ = ["Бумага А4", "Картридж HP", "Стол офисный", "Стул офисный", "Монитор", "Принтер", "Проектор", "Кабель HDMI"]

def get_osrm_route(lat1, lon1, lat2, lon2):
    """Маршрут по дорогам через OSRM"""
    try:
        url = f"{OSRM}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            coords = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
            # Упрощаем: каждая 3-я точка
            if len(coords) > 300:
                coords = coords[::3] + [coords[-1]]
            return {
                "coordinates": coords,
                "distance_km": round(route["distance"] / 1000, 1),
                "duration_hours": round(route["duration"] / 3600, 1),
            }
    except:
        pass
    dist = geodesic((lat1, lon1), (lat2, lon2)).km
    return {"coordinates": [[lat1, lon1], [lat2, lon2]], "distance_km": round(dist, 1), "duration_hours": round(dist / 80, 1)}

def get_address(lat, lon):
    """Обратное геокодирование: координаты → адрес"""
    try:
        r = requests.get(NOMINATIM, params={
            "lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "accept-language": "ru"
        }, timeout=5, headers={"User-Agent": "1CDataGenerator/1.0"})
        data = r.json()
        addr = data.get("address", {})
        house = addr.get("house_number", "")
        road = addr.get("road", addr.get("pedestrian", ""))
        city = addr.get("city", addr.get("town", addr.get("village", "")))
        parts = []
        if city: parts.append(f"г. {city}")
        if road: parts.append(f"ул. {road}")
        if house: parts.append(f"д. {house}")
        return " ".join(parts) if parts else data.get("display_name", "")[:60]
    except:
        return ""

# Загрузка кэша
cache = {}
if os.path.exists(CACHE):
    with open(CACHE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    print(f"Загружен кэш: {len(cache.get('orders', []))} маршрутов")

print("=" * 60)
print("  Генерация маршрутов по дорогам (OSRM) + адреса")
print("=" * 60)
start = time.time()

склад = {"lat": 55.7558, "lon": 37.6173}

# Генерируем контрагентов
контр = []
for i in range(25):
    г = ГОРОДА[i % len(ГОРОДА)]
    lat = г["lat"] + random.uniform(-0.02, 0.02)
    lon = г["lon"] + random.uniform(-0.02, 0.02)
    инн = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    адрес = get_address(lat, lon)
    time.sleep(0.1)  # Nominatim rate limit
    контр.append({
        "id": str(100000 + i),
        "name": ИМЕНА[i],
        "inn": инн,
        "kpp": инн[:4] + str(random.randint(10, 99)) + "01",
        "city": г["name"],
        "address": адрес if адрес else f"г. {г['name']}",
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "phone": f"+7 ({random.randint(300,999)}) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}",
        "status": random.choice(["Активен", "Неактивен"]),
    })
    sys.stdout.write(f"\r  Контрагент {i+1}/25: {г['name']} — {адрес[:40]}...")
    sys.stdout.flush()

print(f"\n  Контрагенты: {len(контр)}")

# Генерируем 50 заказов с маршрутами
заказы = []
for i in range(50):
    кт = контр[i % len(контр)]
    sys.stdout.write(f"\r  Маршрут {i+1}/50: Москва → {кт['city']}...")
    sys.stdout.flush()

    route = get_osrm_route(склад["lat"], склад["lon"], кт["lat"], кт["lon"])
    time.sleep(0.05)

    кол = random.randint(2, 5)
    позиции = []
    общая = 0
    for j in range(1, кол + 1):
        кол_во = round(random.uniform(1, 50), 0)
        цена = round(random.uniform(100, 50000), 2)
        сумма = round(кол_во * цена, 2)
        общая += сумма
        позиции.append({
            "line": j, "item": random.choice(ТОВАРЫ), "qty": кол_во,
            "unit": "шт", "price": цена, "sum": сумма,
            "vat": random.choice(["20%", "10%", "0%"]),
        })

    заказы.append({
        "number": f"ЗК-{random.randint(10000, 99999)}-26",
        "date": f"2026-07-{random.randint(1, 28):02d}",
        "counteragent_id": кт["id"],
        "counteragent_name": кт["name"],
        "counteragent_city": кт["city"],
        "counteragent_address": кт["address"],
        "warehouse": {"name": "Главный склад", "city": "Москва", "lat": склад["lat"], "lon": склад["lon"]},
        "delivery_point": {"city": кт["city"], "address": кт["address"], "lat": кт["lat"], "lon": кт["lon"]},
        "route": route["coordinates"],
        "distance_km": route["distance_km"],
        "duration_hours": route["duration_hours"],
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
    "generation_time_sec": round(elapsed, 1),
    "warehouse": {"name": "Главный склад", "city": "Москва", "lat": 55.7558, "lon": 37.6173},
    "counteragents": контр,
    "orders": заказы,
}

with open(CACHE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False)

print(f"\n\n{'=' * 60}")
print(f"  Готово за {round(elapsed, 1)} сек!")
print(f"  Маршрутов: {len(заказы)}")
print(f"  Расстояние: {round(total_dist):,} км")
print(f"  Точек: {total_points:,}")
print(f"  Файл: {CACHE} ({round(os.path.getsize(CACHE)/1024)} КБ)")
print(f"{'=' * 60}")
