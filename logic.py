"""
logic.py — Изолированный модуль алгоритмов расчёта.
Все данные генерируются здесь. app.py только обращается за данными.
Маршруты: A → B → C ... (любые города связаны).
Расстояния через OSRM (OpenStreetMap Routing).
"""
import random
import math
import requests
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
    """Расчёт расстояния (формула гаверсинусов), км."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 1)


def osrm_route(lat1, lon1, lat2, lon2):
    """Получить маршрут через OSRM: расстояние, время, координаты polyline."""
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=10)
        d = r.json()
        if d.get("code") == "Ok" and d.get("routes"):
            route = d["routes"][0]
            coords = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
            return {
                "distance_km": round(route["distance"] / 1000, 1),
                "duration_hours": round(route["duration"] / 3600, 1),
                "coords": coords,
            }
    except Exception:
        pass
    # Fallback: прямая линия
    dist = расстояние(lat1, lon1, lat2, lon2)
    return {
        "distance_km": dist,
        "duration_hours": round(dist / 80, 1),
        "coords": [[lat1, lon1], [lat2, lon2]],
    }


def стоимость_перевозки(distance_km, weight_t):
    """Тариф перевозки."""
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
    """Время в пути (80 км/ч), часов."""
    return round(distance_km / 80, 1)


# ─── Маршруты ───

def построить_маршрут(точки):
    """Построить маршрут через список точек A → B → C ...
    Возвращает общее расстояние, время, координаты polyline."""
    if len(точки) < 2:
        return {"distance_km": 0, "duration_hours": 0, "coords": []}

    all_coords = []
    total_dist = 0
    total_time = 0

    for i in range(len(точки) - 1):
        a, b = точки[i], точки[i + 1]
        seg = osrm_route(a["lat"], a["lon"], b["lat"], b["lon"])
        if all_coords and seg["coords"]:
            seg["coords"] = seg["coords"][1:]  # убрать дубль точки
        all_coords.extend(seg["coords"])
        total_dist += seg["distance_km"]
        total_time += seg["duration_hours"]

    return {
        "distance_km": round(total_dist, 1),
        "duration_hours": round(total_time, 1),
        "coords": all_coords,
    }


# ─── Генераторы ───

def генерация_точки(город):
    """Случайная точка рядом с городом (~3 км)."""
    lat = город["lat"] + random.uniform(-0.03, 0.03)
    lon = город["lon"] + random.uniform(-0.03, 0.03)
    return round(lat, 6), round(lon, 6)


def генерация_заказа():
    """Генерация заказа: A → B (→ C ...) через разные города.
    Любые города могут быть связаны, не только из склада."""
    num_stops = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
    used = set()
    stops = []

    for _ in range(num_stops):
        while True:
            город = random.choice(ГОРОДА)
            if город["name"] not in used:
                used.add(город["name"])
                lat, lon = генерация_точки(город)
                stops.append({"name": город["name"], "lat": lat, "lon": lon})
                break

    # Маршрут: Склад → Город1 → Город2 → ...
    route_points = [{"name": СКЛАД["city"], "lat": СКЛАД["lat"], "lon": СКЛАД["lon"]}] + stops
    route = построить_маршрут(route_points)

    final = stops[-1]
    вес = round(random.uniform(10, 22), 1)
    стоимость = стоимость_перевозки(route["distance_km"], вес)

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

    # Формируем строку "Откуда → Куда"
    from_city = СКЛАД["city"]
    to_city = final["name"]
    cities_route = " → ".join([СКЛАД["city"]] + [s["name"] for s in stops])

    return {
        "number": "ZK-" + str(random.randint(10000, 99999)) + "-26",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "counteragent": random.choice(КОНТРАГЕНТЫ),
        "from_city": from_city,
        "from_lat": СКЛАД["lat"],
        "from_lon": СКЛАД["lon"],
        "to_city": to_city,
        "to_lat": final["lat"],
        "to_lon": final["lon"],
        "cities_route": cities_route,
        "stops": stops,
        "cargo": cargo,
        "cargo_type": cargo_type,
        "weight": weight,
        "distance_km": route["distance_km"],
        "duration_hours": route["duration_hours"],
        "transport_cost": стоимость,
        "sum": round(total, 2),
        "status": random.choice(СТАТУСЫ),
        "items": order_items,
        "coords": route["coords"],
        "has_route": not is_sbor,
    }


def генерация_заказов(count=1):
    """Генерация нескольких заказов."""
    return [генерация_заказа() for _ in range(count)]


def получить_города():
    """Список городов."""
    return ГОРОДА


def получить_склад():
    """Данные склада."""
    return СКЛАД


# ══════════════════════════════════════════════
# АЛГОРИТМЫ ОПТИМИЗАЦИИ
# ══════════════════════════════════════════════

def clark_wright(клиенты, K=22):
    """Алгоритм Кларка-Райта (Savings Algorithm).
    Оптимальное объединение клиентов в маршруты с ограничением грузоподъёма K (тонн).

    Алгоритм:
    1. Строим матрицу savings: s(i,j) = d(0,i) + d(0,j) - d(i,j)
       где 0 — depot, i,j — клиенты.
    2. Сортируем пары по убыванию savings.
    3. Объединяем клиентов в маршруты, если:
       - оба клиента ещё не в маршруте
       - суммарный вес не превышает K
       - объединение не нарушает порядок
    """
    depot = {"lat": СКЛАД["lat"], "lon": СКЛАД["lon"]}
    n = len(клиенты)

    # Матрица расстояний depot → клиент
    d0 = [расстояние(depot["lat"], depot["lon"], к["lat"], к["lon"]) for к in клиенты]

    # Savings: s(i,j) = d0[i] + d0[j] - d(i,j)
    savings = []
    for i in range(n):
        for j in range(i + 1, n):
            d_ij = расстояние(клиенты[i]["lat"], клиенты[i]["lon"], клиенты[j]["lat"], клиенты[j]["lon"])
            s = d0[i] + d0[j] - d_ij
            savings.append((s, i, j, d_ij))

    savings.sort(key=lambda x: -x[0])  # по убыванию

    # Инициализация: каждый клиент — отдельный маршрут
    routes = [{"clients": [i], "weight": клиенты[i]["weight"], "dist": d0[i] * 2} for i in range(n)]
    client_route = {i: i for i in range(n)}  # клиент → индекс маршрута

    # Объединение
    for s, i, j, d_ij in savings:
        ri = client_route.get(i)
        rj = client_route.get(j)
        if ri is None or rj is None or ri == rj:
            continue
        route_i = routes[ri]
        route_j = routes[rj]
        new_weight = route_i["weight"] + route_j["weight"]
        if new_weight > K:
            continue
        # Объединяем: route_i + route_j
        route_i["clients"].extend(route_j["clients"])
        route_i["weight"] = new_weight
        route_i["dist"] = route_i["dist"] + route_j["dist"] - d0[i] - d0[j] + d_ij
        for c in route_j["clients"]:
            client_route[c] = ri
        route_j["clients"] = []
        route_j["weight"] = 0
        route_j["dist"] = 0

    # Формируем результат
    result = []
    for route in routes:
        if not route["clients"]:
            continue
        points = [{"name": "Depot", "lat": depot["lat"], "lon": depot["lon"]}]
        total_dist = 0
        prev_lat, prev_lon = depot["lat"], depot["lon"]
        for ci in route["clients"]:
            к = клиенты[ci]
            seg = расстояние(prev_lat, prev_lon, к["lat"], к["lon"])
            total_dist += seg
            points.append({"name": к.get("name", f"Client {ci}"), "lat": к["lat"], "lon": к["lon"], "weight": к["weight"]})
            prev_lat, prev_lon = к["lat"], к["lon"]
        total_dist += расстояние(prev_lat, prev_lon, depot["lat"], depot["lon"])
        result.append({
            "points": points,
            "weight": route["weight"],
            "distance_km": round(total_dist, 1),
            "duration_hours": round(total_dist / 80, 1),
            "transport_cost": стоимость_перевозки(total_dist, route["weight"]),
        })

    return result


def min_cost_flow(источники, приемники, K=150):
    """Поток минимальной стоимости (Min-Cost Flow).
    Оптимальное распределение ресурсов от источников к приемникам.

    Алгоритм (жадный):
    1. Строим матрицу стоимостей: cost(i,j) = расстояние(i,j)
    2. Для каждого приемника ищем ближайший источник
    3. Заполняем приемник до K (или остатка ресурса)
    4. Минимизируем суммарную стоимость
    """
    result = []
    total_cost = 0
    total_delivered = 0

    # Копируем остатки ресурсов
    остатки = [{"lat": и["lat"], "lon": и["lon"], "name": и.get("name", ""), "rest": и["weight"]} for и in источники]

    for п in приемники:
        remaining = K
        allocations = []
        п_lat, п_lon = п["lat"], п["lon"]

        # Сортируем источники по расстоянию до приемника
        sorted_sources = sorted(range(len(остатки)), key=lambda i: расстояние(остатки[i]["lat"], остатки[i]["lon"], п_lat, п_lon))

        for si in sorted_sources:
            if remaining <= 0 or остатки[si]["rest"] <= 0:
                continue
            amount = min(remaining, остатки[si]["rest"])
            dist = расстояние(остатки[si]["lat"], остатки[si]["lon"], п_lat, п_lon)
            cost = round(dist * amount)
            allocations.append({
                "source": остатки[si]["name"],
                "amount": amount,
                "distance_km": dist,
                "cost": cost,
            })
            остатки[si]["rest"] -= amount
            remaining -= amount
            total_cost += cost
            total_delivered += amount

        result.append({
            "receiver": п.get("name", ""),
            "lat": п_lat,
            "lon": п_lon,
            "capacity": K,
            "filled": K - remaining,
            "allocations": allocations,
        })

    return {"distributions": result, "total_cost": total_cost, "total_delivered": total_delivered}


def генерация_заказов_clark_wright(count=10, K=22):
    """Генерация оптимальных заказов через Clark-Wright."""
    # Генерируем клиентов (точки назначения)
    клиенты = []
    used = set()
    for _ in range(count):
        while True:
            город = random.choice(ГОРОДА)
            if город["name"] not in used:
                used.add(город["name"])
                lat, lon = генерация_точки(город)
                вес = round(random.uniform(5, 15), 1)
                клиенты.append({"name": город["name"], "lat": lat, "lon": lon, "weight": вес})
                break

    routes = clark_wright(клиенты, K)

    # Формируем заказы из маршрутов
    заказы = []
    for route in routes:
        items = random.sample(ТОВАРЫ, random.randint(2, 4))
        order_items = []
        total = 0
        for i, t in enumerate(items, 1):
            qty = random.randint(1, 10)
            s = round(t["price"] * qty, 2)
            total += s
            order_items.append({"line": i, "item": t["name"], "qty": qty, "unit": t["unit"], "price": t["price"], "sum": s})

        stops = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"]} for p in route["points"][1:]]
        cities_route = " → ".join(["Москва"] + [p["name"] for p in route["points"][1:]])

        заказы.append({
            "number": "ZK-" + str(random.randint(10000, 99999)) + "-26",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "counteragent": random.choice(КОНТРАГЕНТЫ),
            "from_city": СКЛАД["city"],
            "from_lat": СКЛАД["lat"],
            "from_lon": СКЛАД["lon"],
            "to_city": stops[-1]["name"] if stops else СКЛАД["city"],
            "to_lat": stops[-1]["lat"] if stops else СКЛАД["lat"],
            "to_lon": stops[-1]["lon"] if stops else СКЛАД["lon"],
            "cities_route": cities_route,
            "stops": stops,
            "cargo": random.choice(ГРУЗЫ),
            "cargo_type": "фура",
            "weight": route["weight"],
            "distance_km": route["distance_km"],
            "duration_hours": route["duration_hours"],
            "transport_cost": route["transport_cost"],
            "sum": round(total, 2),
            "status": random.choice(СТАТУСЫ),
            "items": order_items,
            "coords": [],  # polyline будет построен на клиенте
            "has_route": True,
        })

    return заказы
