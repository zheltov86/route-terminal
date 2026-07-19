from flask import Flask, jsonify, Response, request
import json, os, random
from datetime import datetime
from logic import генерация_заказа, генерация_заказов, генерация_заказов_clark_wright, min_cost_flow, оптимизация_бюджета, ГОРОДА, СКЛАД

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "orders.json")

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.route("/")
def index(): return Response(HTML, mimetype="text/html")

@app.route("/api/random-order")
def api_random_order():
    return jsonify(генерация_заказа())

@app.route("/api/optimal-orders")
def api_optimal_orders():
    count = int(request.args.get("count", 10))
    K = int(request.args.get("K", 22))
    return jsonify(генерация_заказов_clark_wright(count, K))

@app.route("/api/distribute")
def api_distribute():
    sources = [{"name": ГОРОДА[i]["name"], "lat": ГОРОДА[i]["lat"], "lon": ГОРОДА[i]["lon"], "weight": random.randint(20, 100)} for i in range(min(5, len(ГОРОДА)))]
    receivers = [{"name": ГОРОДА[i]["name"], "lat": ГОРОДА[i]["lat"], "lon": ГОРОДА[i]["lon"]} for i in range(5, min(15, len(ГОРОДА)))]
    K = int(request.args.get("K", 150))
    return jsonify(min_cost_flow(sources, receivers, K))

@app.route("/api/budget-optimize")
def api_budget_optimize():
    B = int(request.args.get("B", 1000000))
    n = int(request.args.get("n", 20))
    return jsonify(оптимизация_бюджета(B, n))

@app.route("/api/orders")
def api_orders():
    return jsonify(load_orders())

@app.route("/api/export/xml")
def api_export_xml():
    """Выгрузка заказов в EnterpriseData 1.8 XML (для XDTO-парсинга в 1C).
    Формат строго как Тест.xml / Выгрузка_Заказы.xml."""
    from flask import Response as Resp
    import uuid

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    org_ref = "553d56f1-8295-11f1-8af8-04ecd881cf53"
    cur_ref = "7e3e0ef4-8295-11f1-8af8-04ecd881cf53"

    def indent(l): return "\t" * l
    def ref(): return str(uuid.uuid4())
    def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append('<Message xmlns:msg="http://www.1c.ru/SSL/Exchange/Message" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">')
    L.append(f'{indent(1)}<msg:Header>')
    L.append(f'{indent(2)}<msg:Format>http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8</msg:Format>')
    L.append(f'{indent(2)}<msg:CreationDate>{now}</msg:CreationDate>')
    L.append(f'{indent(2)}<msg:AvailableVersion>1.8</msg:AvailableVersion>')
    L.append(f'{indent(1)}</msg:Header>')
    L.append(f'{indent(1)}<Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8">')

    # Валюта
    L.append(f'{indent(2)}<Справочник.Валюты>')
    L.append(f'{indent(3)}<КлючевыеСвойства>')
    L.append(f'{indent(4)}<Ссылка>{cur_ref}</Ссылка>')
    L.append(f'{indent(4)}<ДанныеКлассификатора><Код>643</Код><Наименование>руб.</Наименование></ДанныеКлассификатора>')
    L.append(f'{indent(3)}</КлючевыеСвойства>')
    L.append(f'{indent(3)}<ПараметрыПрописи>рубль, рубля, рублей, м, копейка, копейки, копеек, ж, 2 знака</ПараметрыПрописи>')
    L.append(f'{indent(2)}</Справочник.Валюты>')

    # Организация
    L.append(f'{indent(2)}<Справочник.Организации>')
    L.append(f'{indent(3)}<КлючевыеСвойства>')
    L.append(f'{indent(4)}<Ссылка>{org_ref}</Ссылка>')
    L.append(f'{indent(4)}<Наименование>Управленческая организация</Наименование>')
    L.append(f'{indent(4)}<ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо>')
    L.append(f'{indent(3)}</КлючевыеСвойства>')
    L.append(f'{indent(3)}<Префикс>УУ</Префикс>')
    L.append(f'{indent(2)}</Справочник.Организации>')

    # Заказы клиентов
    for order in load_orders():
        order_ref = ref()
        kont_ref = ref()
        num = order.get("number", "")
        date = order.get("date", "")
        amount = order.get("amount", order.get("sum", 0))
        comment = order.get("comment", f"Заказ {num}")

        L.append(f'{indent(2)}<Документ.ЗаказКлиента>')
        L.append(f'{indent(3)}<КлючевыеСвойства>')
        L.append(f'{indent(4)}<Ссылка>{order_ref}</Ссылка>')
        L.append(f'{indent(4)}<Номер>{esc(num)}</Номер>')
        L.append(f'{indent(4)}<Дата>{date}T00:00:00</Дата>')
        L.append(f'{indent(4)}<Проведен>true</Проведен>')
        L.append(f'{indent(3)}</КлючевыеСвойства>')
        L.append(f'{indent(3)}<Организация><Ссылка>{org_ref}</Ссылка><Наименование>Управленческая организация</Наименование></Организация>')
        L.append(f'{indent(3)}<Контрагент><Ссылка>{kont_ref}</Ссылка><Наименование>{esc(order.get("counteragent","Клиент"))}</Наименование><НаименованиеПолное>{esc(order.get("counteragent","Клиент"))}</НаименованиеПолное><ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо></Контрагент>')
        L.append(f'{indent(3)}<Валюта><Ссылка>{cur_ref}</Ссылка><Наименование>руб.</Наименование></Валюта>')
        L.append(f'{indent(3)}<Сумма>{amount}</Сумма>')
        L.append(f'{indent(3)}<Комментарий>{esc(comment)}</Комментарий>')
        L.append(f'{indent(3)}<Товары>')

        for item in order.get("items", []):
            item_ref = ref()
            unit_ref = ref()
            qty = item.get("quantity", item.get("qty", 0))
            price = item.get("price", 0)
            sum_val = item.get("sum", 0)
            vat_rate = item.get("vat_rate", "НДС20")
            vat_sum = round(sum_val * 0.2, 2) if vat_rate == "НДС20" else 0
            nomenclature = item.get("nomenclature_name", item.get("item", ""))
            unit_name = item.get("unit_name", item.get("unit", "шт"))

            L.append(f'{indent(4)}<Строка>')
            L.append(f'{indent(5)}<НомерСтрокиДокумента>{item.get("line", "")}</НомерСтрокиДокумента>')
            L.append(f'{indent(5)}<ДанныеНоменклатуры><Ссылка>{item_ref}</Ссылка><Наименование>{esc(nomenclature)}</Наименование></ДанныеНоменклатуры>')
            L.append(f'{indent(5)}<ЕдиницаИзмерения><Ссылка>{unit_ref}</Ссылка><Наименование>{esc(unit_name)}</Наименование></ЕдиницаИзмерения>')
            L.append(f'{indent(5)}<Количество>{qty}</Количество>')
            L.append(f'{indent(5)}<Цена>{price}</Цена>')
            L.append(f'{indent(5)}<Сумма>{sum_val}</Сумма>')
            L.append(f'{indent(5)}<СтавкаНДС>{vat_rate}</СтавкаНДС>')
            L.append(f'{indent(5)}<СуммаНДС>{vat_sum}</СуммаНДС>')
            L.append(f'{indent(4)}</Строка>')

        L.append(f'{indent(3)}</Товары>')
        L.append(f'{indent(2)}</Документ.ЗаказКлиента>')

    L.append(f'{indent(1)}</Body>')
    L.append('</Message>')

    return Resp("\n".join(L), mimetype="text/xml; charset=utf-8")

HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Route Terminal</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden}
body{font-family:'Inter',system-ui,sans-serif;background:#0a0b0f;color:#e8eaf0}

.hdr{height:34px;background:#0f1017;border-bottom:1px solid #1e2035;display:flex;align-items:center;padding:0 12px;gap:10px;flex-shrink:0}
.logo{display:flex;align-items:center;gap:6px}
.logo i{width:22px;height:22px;background:linear-gradient(135deg,#6366f1,#22d3ee);border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;color:#fff;font-style:normal}
.logo b{font-size:12px}.logo small{font-size:8px;color:#565a72;text-transform:uppercase}
.toolbar{display:flex;align-items:center;gap:4px;margin-left:16px}
.btn{background:#1a1b28;border:1px solid #1e2035;color:#8b8fa8;padding:3px 10px;border-radius:4px;font-size:9px;font-weight:600;cursor:pointer;font-family:inherit}
.btn:hover{border-color:#6366f1;color:#818cf8}
.btn.pri{background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;border-color:transparent}
.btn.dng{border-color:#dc2626;color:#f87171}
.btn.on{background:#059669;color:#fff;border-color:#34d399}
.sep{width:1px;height:14px;background:#1e2035}

.filters{height:24px;background:#0d0e14;border-bottom:1px solid #1e2035;display:flex;align-items:center;gap:4px;padding:0 12px;font-size:8px;color:#565a72;flex-shrink:0;overflow-x:auto}
.filters span{color:#565a72;text-transform:uppercase;letter-spacing:.05em;font-weight:600;white-space:nowrap}
.fb{background:#13141e;border:1px solid #1e2035;color:#8b8fa8;padding:1px 5px;border-radius:3px;font-size:8px;font-weight:500;cursor:pointer;white-space:nowrap}
.fb:hover{border-color:#6366f1;color:#818cf8}
.fb.on{background:rgba(99,102,241,.15);color:#818cf8;border-color:rgba(99,102,241,.3)}
.fb .d{display:inline-block;width:5px;height:5px;border-radius:50%;margin-right:2px;vertical-align:middle}

/* LAYOUT: left column (map+table) | right panel */
.page{display:flex;height:calc(100vh - 58px)}
.left{flex:1;display:flex;flex-direction:column;min-width:0}
#map{flex:1;min-height:0}
.tbl{height:160px;border-top:1px solid #1e2035;flex-shrink:0;overflow-y:auto;overflow-x:hidden;background:#0a0b0f}
.tbl::-webkit-scrollbar{width:4px}
.tbl::-webkit-scrollbar-track{background:#0f1017}
.tbl::-webkit-scrollbar-thumb{background:#2a2d45;border-radius:2px}

.rpanel{width:350px;background:#0d0e14;border-left:1px solid #1e2035;display:flex;flex-direction:column;flex-shrink:0;overflow:hidden}
.stats-box{padding:10px;border-bottom:1px solid #1e2035;flex-shrink:0}
.stats-box h4{font-size:8px;color:#565a72;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.sg{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px}
.sg .s{background:#13141e;border:1px solid #1e2035;border-radius:5px;padding:8px 4px;text-align:center}
.sg .s .v{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:800;color:#818cf8}
.sg .s .l{font-size:7px;color:#565a72;text-transform:uppercase;margin-top:2px}
.sg .s.up .v{color:#34d399}

.info-box{flex:1;overflow-y:auto;padding:10px}
.info-box::-webkit-scrollbar{width:3px}
.info-box::-webkit-scrollbar-thumb{background:#2a2d45;border-radius:2px}
.info-empty{color:#565a72;font-size:9px;text-align:center;padding-top:20px}
.info-hdr{font-size:12px;font-weight:700;color:#818cf8;margin-bottom:6px;padding-bottom:5px;border-bottom:1px solid #1e2035}
.ir{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(30,32,53,.3);font-size:9px}
.ir .lb{color:#565a72}
.ir .vl{color:#e8eaf0;font-weight:500;font-family:'JetBrains Mono',monospace;font-size:9px;text-align:right;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ir .vl.pink{color:#f472b6}
.ir .vl.cyan{color:#22d3ee}
.route-box{margin-top:6px;padding:5px;background:#13141e;border:1px solid #1e2035;border-radius:4px;font-size:8px;color:#565a72;line-height:1.6}
.route-box b{color:#22d3ee}

table{width:100%;border-collapse:collapse;font-size:9px}
thead{position:sticky;top:0;z-index:2}
th{background:#13141e;padding:3px 5px;text-align:left;font-size:7px;color:#565a72;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #1e2035;white-space:nowrap;cursor:pointer;user-select:none}
th:hover{color:#818cf8}
td{padding:3px 5px;border-bottom:1px solid rgba(30,32,53,.3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100px}
tr{transition:background .1s;cursor:pointer}
tr:hover td{background:rgba(99,102,241,.06)}
tr.hl td{background:rgba(99,102,241,.15)!important}
tr.active td{background:rgba(52,211,153,.1)!important}
.badge{display:inline-block;padding:0 3px;border-radius:2px;font-size:7px;font-weight:600}
.b-New{background:rgba(129,140,248,.1);color:#818cf8;border:1px solid rgba(129,140,248,.15)}
.b-Processing{background:rgba(251,191,36,.1);color:#fbbf24;border:1px solid rgba(251,191,36,.15)}
.b-Confirmed{background:rgba(34,211,238,.1);color:#22d3ee;border:1px solid rgba(34,211,238,.15)}
.b-InTransit{background:rgba(251,146,60,.1);color:#fb923c;border:1px solid rgba(251,146,60,.15)}
.b-Delivered{background:rgba(52,211,153,.1);color:#34d399;border:1px solid rgba(52,211,153,.15)}
.money{font-family:'JetBrains Mono',monospace;color:#f472b6;font-weight:500;font-size:8px}
.km{font-family:'JetBrains Mono',monospace;color:#22d3ee;font-weight:500;font-size:8px}

.leaflet-popup-content-wrapper{background:#13141e!important;border:1px solid #1e2035!important;border-radius:8px!important;color:#e8eaf0!important;box-shadow:0 8px 32px rgba(0,0,0,.6)!important;min-width:220px}
.leaflet-popup-tip{background:#13141e!important}
.leaflet-popup-content{font-family:'Inter',sans-serif;font-size:10px;line-height:1.5;margin:8px 10px}
.lp-t{font-weight:700;color:#818cf8;margin-bottom:4px;font-size:12px}
.lp-r{display:flex;justify-content:space-between;padding:2px 0;font-size:9px}
.lp-r .a{color:#565a72}.lp-r .b{color:#e8eaf0;font-weight:500;font-family:'JetBrains Mono',monospace}
.lp-r .b.pk{color:#f472b6}.lp-r .b.cy{color:#22d3ee}
.lp-c{margin-top:4px;padding:3px 5px;background:#1a1b28;border-radius:4px;font-size:8px;color:#565a72}
@keyframes fadeIn{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:translateY(0)}}
.row-new{animation:fadeIn .3s ease-out}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo"><i>RT</i><div><b>Route Terminal</b><br><small>Logistics Dashboard</small></div></div>
  <div class="toolbar">
    <button class="btn pri" id="bAdd">+ Order</button>
    <button class="btn" id="bAdd5">+5</button>
    <button class="btn" id="bAuto">Auto 10s</button>
    <div class="sep"></div>
    <button class="btn" id="bOptimal" style="border-color:#22d3ee;color:#22d3ee">Clark-Wright</button>
    <button class="btn" id="bDistrib" style="border-color:#a78bfa;color:#a78bfa">Min-Cost</button>
    <button class="btn" id="bBudget" style="border-color:#34d399;color:#34d399">Budget Opt</button>
    <div class="sep"></div>
    <button class="btn dng" id="bClear">Clear</button>
    <div class="sep"></div>
    <div style="position:relative;display:flex;align-items:center">
      <button class="btn" id="bApi" style="border-color:#fbbf24;color:#fbbf24">API</button>
      <div id="apiMenu" style="display:none;position:absolute;right:0;top:100%;margin-top:4px;background:#13141e;border:1px solid #1e2035;border-radius:6px;padding:6px 0;min-width:220px;z-index:100;box-shadow:0 8px 24px rgba(0,0,0,.6)">
        <a href="http://localhost:5001/" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">1C API - Home</a>
        <a href="http://localhost:5001/health" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">GET /health</a>
        <a href="http://localhost:5001/api/orders" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">GET /api/orders</a>
        <a href="http://localhost:5001/api/refs" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">GET /api/refs</a>
        <div style="height:1px;background:#1e2035;margin:4px 8px"></div>
        <a href="http://localhost:5000/api/random-order" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">GET /api/random-order</a>
        <a href="http://localhost:5000/api/orders" target="_blank" style="display:block;padding:6px 12px;font-size:10px;color:#8b8fa8;text-decoration:none">GET /api/orders (Route)</a>
      </div>
    </div>
  </div>
</div>
<div class="filters" id="fBar">
  <button class="fb on" data-f="all">All</button>
  <div class="sep"></div>
  <span>Status:</span>
  <button class="fb" data-f="st" data-v="New"><span class="d" style="background:#818cf8"></span>New</button>
  <button class="fb" data-f="st" data-v="Processing"><span class="d" style="background:#fbbf24"></span>Proc</button>
  <button class="fb" data-f="st" data-v="Confirmed"><span class="d" style="background:#22d3ee"></span>Conf</button>
  <button class="fb" data-f="st" data-v="InTransit"><span class="d" style="background:#fb923c"></span>Transit</button>
  <button class="fb" data-f="st" data-v="Delivered"><span class="d" style="background:#34d399"></span>Done</button>
  <div class="sep"></div>
  <span>Cargo:</span>
  <button class="fb" data-f="cg" data-v="fura">Fura</button>
  <button class="fb" data-f="cg" data-v="sborniy">Sbor</button>
</div>

<div class="page">
  <!-- LEFT: map + table (same width) -->
  <div class="left">
    <div id="map"></div>
    <div class="tbl"><table><thead><tr>
      <th class="sh" data-c="0">No</th><th class="sh" data-c="1">From</th><th class="sh" data-c="2">To</th>
      <th class="sh" data-c="3">Load</th><th class="sh" data-c="4">Unload</th><th class="sh" data-c="5">km</th>
      <th class="sh" data-c="6">Price</th><th class="sh" data-c="7">Status</th>
    </tr></thead><tbody id="tB"></tbody></table></div>
  </div>
  <!-- RIGHT: stats + info -->
  <div class="rpanel">
    <div class="stats-box">
      <h4>Statistics</h4>
      <div class="sg">
        <div class="s"><div class="v" id="sT">0</div><div class="l">Orders</div></div>
        <div class="s up"><div class="v" id="sD">0</div><div class="l">Done</div></div>
        <div class="s"><div class="v" id="sK">0</div><div class="l">km</div></div>
        <div class="s"><div class="v" id="sW">0</div><div class="l">Tons</div></div>
        <div class="s"><div class="v" id="sS">0</div><div class="l">Sum</div></div>
        <div class="s"><div class="v" id="sF">0/0</div><div class="l">Fura/Sbor</div></div>
      </div>
    </div>
    <div class="info-box" id="iBox"><div class="info-empty">Hover on route or click row</div></div>
    <div class="algo-box" id="algoBox" style="display:none;border-top:1px solid #1e2035;padding:8px;font-size:8px">
      <div style="color:#565a72;text-transform:uppercase;letter-spacing:.06em;font-weight:600;margin-bottom:4px">Algorithm Results</div>
      <div id="algoContent"></div>
    </div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var WH=[55.7558,37.6173];
var CC=['#f472b6','#fb923c','#34d399','#22d3ee','#a78bfa','#fbbf24','#f87171','#818cf8','#c084fc','#2dd4bf','#e879f9','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
var orders=[],autoI=null,cIdx=0,activeF='all',activeV=null,selectedNum=null;

var map=L.map('map',{zoomControl:false,attributionControl:false}).setView([57,42],5);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:19}).addTo(map);
var routeLayer=L.layerGroup().addTo(map);
var markerLayer=L.layerGroup().addTo(map);

function addWh(){
  L.marker(WH,{icon:L.divIcon({html:'<div style="width:18px;height:18px;background:linear-gradient(135deg,#34d399,#059669);border-radius:50%;border:3px solid #fff;box-shadow:0 0 14px rgba(52,211,153,.6);display:flex;align-items:center;justify-content:center"><div style="width:5px;height:5px;background:#fff;border-radius:50%"></div></div>',className:'',iconSize:[18,18],iconAnchor:[9,9]})}).bindPopup('<b>Warehouse Moscow</b>').addTo(map);
}
addWh();

function updateStats(){
  var n=orders.length,dl=0,km=0,tn=0,sm=0,fu=0,sb=0;
  orders.forEach(function(o){if(o.status==='Delivered')dl++;km+=o.distance_km||0;tn+=o.weight;sm+=o.sum;if(o.cargo_type==='фура')fu++;else sb++;});
  document.getElementById('sT').textContent=n;
  document.getElementById('sD').textContent=dl;
  document.getElementById('sK').textContent=Math.round(km).toLocaleString();
  document.getElementById('sW').textContent=tn.toFixed(1);
  document.getElementById('sS').textContent=Math.round(sm).toLocaleString();
  document.getElementById('sF').textContent=fu+'/'+sb;
}

function matchF(o){
  if(activeF==='all')return true;
  if(activeF==='st')return o.status===activeV;
  if(activeF==='cg')return o.cargo_type===activeV;
  return true;
}

function drawRoute(o){
  var color=CC[cIdx%CC.length];cIdx++;
  o._color=color;
  var ct=o.cargo_type==='сборный'?'Sbor':'Fura';
  var st=o.status||'New';
  var num=o.number;

  // Маршрут: фура — линия по координатам из OSRM
  if(o.has_route!==false && o.coords && o.coords.length>=2){
    var ln=L.polyline(o.coords,{color:color,weight:2.5,opacity:0.9}).addTo(routeLayer);
    ln._n=o.number;
    ln.on('mouseover',function(){
      ln.setStyle({weight:4,opacity:1});ln.bringToFront();
      highlightRow(num,true);
      if(selectedNum===null)showInfo(findO(num));
    });
    ln.on('mouseout',function(){
      ln.setStyle({weight:2.5,opacity:0.9});
      highlightRow(num,false);
      if(selectedNum===null){var el=document.getElementById('iBox');if(el)el.innerHTML='<div class="info-empty">Hover on route or click row</div>';}
    });
  }

  // Маркеры: начальная точка + промежуточные + конечная
  if(o.stops && o.stops.length>0){
    for(var i=0;i<o.stops.length;i++){
      var s=o.stops[i];
      var last=i===o.stops.length-1;
      var mc=last?color:'#ffffff';
      var ms=last?10:7;
      var mk=L.marker([s.lat,s.lon],{icon:L.divIcon({html:'<div style="width:'+ms+'px;height:'+ms+'px;background:'+mc+';border-radius:50%;border:2px solid rgba(255,255,255,'+(last?1:0.5)+');box-shadow:0 0 6px '+mc+'80"></div>',className:'',iconSize:[ms,ms],iconAnchor:[Math.ceil(ms/2),Math.ceil(ms/2)]})}).addTo(markerLayer);
      mk._n=o.number;
      mk.bindPopup(
        '<div class="lp-t">'+o.number+(o.has_route===false?' <span style="color:#fb923c;font-size:9px">[sbor]</span>':'')+'</div>'
        +'<div class="lp-r"><span class="a">Agent</span><span class="b">'+o.counteragent+'</span></div>'
        +'<div class="lp-r"><span class="a">Route</span><span class="b">'+o.cities_route+'</span></div>'
        +'<div class="lp-r"><span class="a">Stop</span><span class="b">'+s.name+'</span></div>'
        +'<div class="lp-r"><span class="a">Cargo</span><span class="b">'+o.cargo+' ('+ct+')</span></div>'
        +'<div class="lp-r"><span class="a">Weight</span><span class="b">'+o.weight+' t</span></div>'
        +'<div class="lp-r"><span class="a">Distance</span><span class="b cy">'+o.distance_km+' km</span></div>'
        +'<div class="lp-r"><span class="a">Duration</span><span class="b cy">'+o.duration_hours+' h</span></div>'
        +'<div class="lp-r"><span class="a">Transport</span><span class="b pk">'+o.transport_cost.toLocaleString()+' rub</span></div>'
        +'<div class="lp-r"><span class="a">Sum</span><span class="b pk">'+o.sum.toLocaleString()+' rub</span></div>'
        +'<div class="lp-r"><span class="a">Status</span><span class="b"><span class="badge b-'+st+'">'+st+'</span></span></div>',
        {maxWidth:280}
      );
    }
  }
}

function showInfo(o){
  var st=o.status||'New';
  var ct=o.cargo_type==='сборный'?'Sbor':'Fura';
  var el=document.getElementById('iBox');
  if(!el)return;
  el.innerHTML='<div class="info-hdr">'+o.number+'</div>'
    +'<div class="ir"><span class="lb">Agent</span><span class="vl">'+o.counteragent+'</span></div>'
    +'<div class="ir"><span class="lb">From</span><span class="vl">'+o.from_city+'</span></div>'
    +'<div class="ir"><span class="lb">To</span><span class="vl">'+o.to_city+'</span></div>'
    +'<div class="ir"><span class="lb">Load Date</span><span class="vl cyan">'+(o.date||'...')+'</span></div>'
    +'<div class="ir"><span class="lb">Unload Date</span><span class="vl cyan">'+(o.unload_date||'...')+'</span></div>'
    +'<div class="ir"><span class="lb">Distance</span><span class="vl cyan">'+o.distance_km+' km</span></div>'
    +'<div class="ir"><span class="lb">Duration</span><span class="vl cyan">'+o.duration_hours+' h</span></div>'
    +'<div class="ir"><span class="lb">Transport</span><span class="vl pink">'+o.transport_cost.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Price</span><span class="vl pink">'+o.sum.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Revenue</span><span class="vl" style="color:#34d399">'+(o.revenue||0).toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Status</span><span class="vl"><span class="badge b-'+st+'">'+st+'</span></span></div>'
    +'<div class="route-box"><b>Route:</b> '+o.cities_route+'</div>';
}

function findO(num){for(var i=0;i<orders.length;i++){if(orders[i].number===num)return orders[i];}return null;}

function highlightRow(num,on){
  var rows=document.getElementById('tB').rows;
  for(var i=0;i<rows.length;i++){
    if(rows[i].getAttribute('data-num')===num){
      if(on){rows[i].classList.add('hl');rows[i].scrollIntoView({block:'nearest',behavior:'smooth'});}
      else{rows[i].classList.remove('hl');}
      break;
    }
  }
}

function addRow(o,prep){
  var st=o.status||'New';
  var tr=document.createElement('tr');
  if(prep)tr.className='row-new';
  tr.setAttribute('data-num',o.number);
  var routeTag=o.has_route===false?' <span style="color:#fb923c;font-size:6px">[sbor]</span>':'';
  var h='<td style="font-family:JetBrains Mono,monospace;color:#818cf8;font-weight:600;font-size:8px">'+o.number+'</td>';
  h+='<td style="font-size:8px">'+o.from_city+'</td>';
  h+='<td style="font-size:8px">'+o.to_city+routeTag+'</td>';
  h+='<td style="font-size:8px;color:#22d3ee">'+(o.date||'...')+'</td>';
  h+='<td style="font-size:8px;color:#fb923c">'+(o.unload_date||o.date||'...')+'</td>';
  h+='<td class="km">'+o.distance_km+' km</td>';
  h+='<td class="money">'+o.sum.toLocaleString()+'</td>';
  h+='<td><span class="badge b-'+st+'">'+st+'</span></td>';
  tr.innerHTML=h;
  var num=o.number;
  var order=o;
  tr.onmouseenter=function(){
    highlightRow(num,true);
    if(selectedNum===null)showInfo(order);
  };
  tr.onmouseleave=function(){
    highlightRow(num,false);
    if(selectedNum===null){var el=document.getElementById('iBox');if(el)el.innerHTML='<div class="info-empty">Hover on route or click row</div>';}
  };
  tr.onclick=function(){
    document.querySelectorAll('#tB tr.active').forEach(function(r){r.classList.remove('active')});
    tr.classList.add('active');
    selectedNum=num;
    routeLayer.eachLayer(function(l){if(l._n===num){l.setStyle({weight:4,opacity:1});l.bringToFront();}});
    markerLayer.eachLayer(function(l){if(l._n===num){l.bringToFront();try{l.openPopup();}catch(e){}}});
    showInfo(order);
  };
  var tb=document.getElementById('tB');
  if(prep)tb.insertBefore(tr,tb.firstChild);else tb.appendChild(tr);
}

function refreshAll(){
  routeLayer.clearLayers();markerLayer.clearLayers();cIdx=0;
  orders.forEach(function(o){if(matchF(o))drawRoute(o);});
  addWh();
  document.getElementById('tB').innerHTML='';
  orders.forEach(function(o){if(matchF(o))addRow(o,false);});
}

function addOneOrder(){
  return fetch('/api/random-order').then(function(r){return r.json()}).then(function(o){
    orders.unshift(o);
    addRow(o,true);
    drawRoute(o);
    updateStats();
  }).catch(function(e){console.error('addOneOrder error:',e);});
}

document.getElementById('bAdd').onclick=function(){addOneOrder();};
document.getElementById('bAdd5').onclick=function(){
  var i=0;function nx(){if(i>=5)return;i++;addOneOrder().then(function(){setTimeout(nx,600)});}nx();
};
document.getElementById('bAuto').onclick=function(){
  var b=document.getElementById('bAuto');
  if(autoI){clearInterval(autoI);autoI=null;b.textContent='Auto 10s';b.classList.remove('on');}
  else{addOneOrder();autoI=setInterval(addOneOrder,10000);b.textContent='Stop';b.classList.add('on');}
};

document.getElementById('bOptimal').onclick=function(){
  fetch('/api/optimal-orders?count=8&K=22').then(function(r){return r.json()}).then(function(arr){
    arr.forEach(function(o){orders.unshift(o);addRow(o,true);drawRoute(o);});
    updateStats();
  });
};

document.getElementById('bDistrib').onclick=function(){
  fetch('/api/distribute?K=150').then(function(r){return r.json()}).then(function(d){
    alert('Min-Cost Flow: delivered '+d.total_delivered+' units, cost: '+d.total_cost.toLocaleString()+' rub');
  });
};

document.getElementById('bBudget').onclick=function(){
  fetch('/api/budget-optimize?B=1000000&n=20').then(function(r){return r.json()}).then(function(d){
    // Добавляем заказы
    d.orders.forEach(function(o){orders.unshift(o);addRow(o,true);drawRoute(o);});
    updateStats();
    // Показываем результаты алгоритма
    showAlgoResults(d.summary);
  });
};

function showAlgoResults(s){
  var box=document.getElementById('algoBox');
  var el=document.getElementById('algoContent');
  if(!box||!el)return;
  box.style.display='block';
  el.innerHTML='<div class="ir"><span class="lb">Budget</span><span class="vl pink">'+s.budget.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Points Selected</span><span class="vl cyan">'+s.points_selected+'</span></div>'
    +'<div class="ir"><span class="lb">Revenue</span><span class="vl" style="color:#34d399">'+s.total_revenue.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Opening Cost</span><span class="vl pink">'+s.total_opening_cost.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Delivery Cost</span><span class="vl pink">'+s.total_delivery_cost.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Total Cost</span><span class="vl pink">'+s.total_cost.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Profit</span><span class="vl" style="color:#34d399;font-weight:700">'+s.profit.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Profit Margin</span><span class="vl cyan">'+s.profit_margin+'%</span></div>'
    +'<div class="ir"><span class="lb">Budget Left</span><span class="vl cyan">'+s.budget_remaining.toLocaleString()+' rub</span></div>';
}
document.getElementById('bClear').onclick=function(){
  orders=[];cIdx=0;activeF='all';activeV=null;selectedNum=null;
  routeLayer.clearLayers();markerLayer.clearLayers();
  document.getElementById('tB').innerHTML='';updateStats();
  map.setView([57,42],5);
  document.querySelectorAll('.fb').forEach(function(b){b.classList.remove('on')});
  document.querySelector('.fb[data-f="all"]').classList.add('on');
  addWh();
};

document.getElementById('bApi').onclick=function(e){
  e.stopPropagation();
  var m=document.getElementById('apiMenu');
  m.style.display=m.style.display==='none'?'block':'none';
};
document.addEventListener('click',function(){document.getElementById('apiMenu').style.display='none';});

document.getElementById('fBar').onclick=function(e){
  var b=e.target.closest('.fb');if(!b)return;
  document.querySelectorAll('.fb').forEach(function(x){x.classList.remove('on')});
  b.classList.add('on');
  activeF=b.getAttribute('data-f');activeV=b.getAttribute('data-v');
  refreshAll();
};

document.querySelectorAll('.sh').forEach(function(th){
  th.onclick=function(){
    var c=parseInt(th.getAttribute('data-c'));
    var tb=document.getElementById('tB'),rows=Array.prototype.slice.call(tb.rows);
    var dir=th.getAttribute('data-dir')==='1'?-1:1;
    th.setAttribute('data-dir',dir===1?'0':'1');
    rows.sort(function(a,b){
      var va=a.cells[c].textContent.trim(),vb=b.cells[c].textContent.trim();
      var na=parseFloat(va.replace(/[^0-9.-]/g,'')),nb=parseFloat(vb.replace(/[^0-9.-]/g,''));
      if(!isNaN(na)&&!isNaN(nb))return(na-nb)*dir;
      return va.localeCompare(vb)*dir;
    });
    rows.forEach(function(r){tb.appendChild(r)});
  };
});

setTimeout(function(){map.invalidateSize();addOneOrder();},200);
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("="*60)
    print("  Route Terminal")
    print("  http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)
