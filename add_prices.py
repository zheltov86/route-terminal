"""
Добавление цен на перевозки (фуры 22 т) и расписания доставок.
"""
import json, random
from datetime import datetime, timedelta

with open("routes_cache.json", "r", encoding="utf-8") as f:
    cache = json.load(f)

print(f"Загружено: {len(cache['orders'])} заказов")

def calc_freight_price(distance_km, weight_tons=22):
    """Расчёт стоимости перевозки фурой 22 тонны (2026)"""
    if distance_km < 100:
        rate = 55
    elif distance_km < 300:
        rate = 45
    elif distance_km < 500:
        rate = 42
    elif distance_km < 1000:
        rate = 38
    else:
        rate = 35
    base = distance_km * rate
    weight_surcharge = base * 0.02 * max(0, weight_tons - 20)
    total = round(base + weight_surcharge, 0)
    total = round(total / 500) * 500
    return int(total)

base_time = datetime(2026, 7, 19, 6, 0)

for order in cache["orders"]:
    dist = order.get("distance_km", 0)
    order["freight_price"] = calc_freight_price(dist)
    order["freight_rate"] = "руб/км"

    speed = random.randint(60, 80)
    travel_hours = round(dist / speed, 1)
    order["travel_hours"] = travel_hours

    offset_hours = random.randint(0, 72)
    departure = base_time + timedelta(hours=offset_hours, minutes=random.randint(0, 59))
    order["departure"] = departure.strftime("%Y-%m-%dT%H:%M:%S")
    order["departure_display"] = departure.strftime("%d.%m.%Y %H:%M")

    arrival = departure + timedelta(hours=travel_hours)
    order["arrival"] = arrival.strftime("%Y-%m-%dT%H:%M:%S")
    order["arrival_display"] = arrival.strftime("%d.%m.%Y %H:%M")

    now = datetime(2026, 7, 18, 23, 0)
    if departure > now + timedelta(days=2):
        order["delivery_status"] = "Ожидает отправки"
    elif departure > now:
        order["delivery_status"] = "На погрузке"
    elif arrival > now:
        order["delivery_status"] = "В пути"
    else:
        order["delivery_status"] = "Доставлен"

with open("routes_cache.json", "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False)

total_freight = sum(o["freight_price"] for o in cache["orders"])
print(f"Цены рассчитаны для {len(cache['orders'])} маршрутов")
print(f"Общая стоимость перевозок: {total_freight:,} руб.")
print(f"Средняя: {total_freight // len(cache['orders']):,} руб.")
print()
for o in cache["orders"][:5]:
    print(f"  {o['number']}: {o['counteragent_city']} — {o['distance_km']} км — {o['freight_price']:,} руб. — {o['departure_display']}")
print("  ...")
