"""1C Routes v1.4 — Грузы + расширенная шапка + ограничение таблицы"""
import random,json as json_mod,os,uuid
from datetime import datetime
from flask import Flask,Response,request,jsonify
from geo_service import контрагенты,заказы,get_route_road,ГОРОДА_ЦЕНТР
app=Flask(__name__)

def xml_escape(s):return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def load_cache():
    if os.path.exists("routes_cache.json"):
        with open("routes_cache.json","r",encoding="utf-8") as f:return json_mod.load(f)
    return {"counteragents":[],"orders":[]}

ORG={"ref":"a1b2c3d4-e5f6-7890-abcd-ef1234567890","name":"ООО «ЦентрСнабжение»","name_short":"ООО ЦентрСнабжение",
    "name_full":"Общество с ограниченной ответственностью «ЦентрСнабжение»","inn":"7708123456","kpp":"770801001",
    "juridical":"ЮридическоеЛицо","ogrn":"1237700123456","okved":"46.46","address":"г. Москва, ул. Снабженческая, д. 12"}

PRODUCTS=[{"name":"Сковорода чугунная 26см","desc":"Чугунная","price":3490,"unit":"шт","unit_ref":"u001","weight":1.8},
    {"name":"Кастрюля нержавеющая 3л","desc":"Сталь 18/10","price":2890,"unit":"шт","unit_ref":"u001","weight":1.2},
    {"name":"Нож кухонный 20см","desc":"Поварской","price":1990,"unit":"шт","unit_ref":"u001","weight":0.3},
    {"name":"Доска разделочная","desc":"Берёза","price":890,"unit":"шт","unit_ref":"u001","weight":0.5},
    {"name":"Полотенца 3шт","desc":"Комплект","price":1290,"unit":"комплект","unit_ref":"u002","weight":0.8},
    {"name":"Ведро 12л","desc":"Пластик","price":490,"unit":"шт","unit_ref":"u001","weight":0.4},
    {"name":"Швабра с отжимом","desc":"Вращ. механизм","price":1890,"unit":"шт","unit_ref":"u001","weight":0.9},
    {"name":"Пакеты 60л","desc":"30 шт","price":290,"unit":"упак","unit_ref":"u003","weight":0.2},
    {"name":"Средство посуды 500мл","desc":"Концентрат","price":180,"unit":"шт","unit_ref":"u001","weight":0.6},
    {"name":"Плед 150x200","desc":"Флис","price":2490,"unit":"шт","unit_ref":"u001","weight":1.5},
    {"name":"Чайник 1.7л","desc":"2200 Вт","price":2490,"unit":"шт","unit_ref":"u001","weight":0.8},
    {"name":"Тостер 2-slot","desc":"Регулировка","price":3290,"unit":"шт","unit_ref":"u001","weight":1.1},
    {"name":"Мультиварка 5л","desc":"30 программ","price":5990,"unit":"шт","unit_ref":"u001","weight":4.5},
    {"name":"Пылесос беспроводной","desc":"40 мин","price":12990,"unit":"шт","unit_ref":"u001","weight":2.3},
    {"name":"Утюг 2400Вт","desc":"Паровой","price":3990,"unit":"шт","unit_ref":"u001","weight":1.2},
    {"name":"Сушилка напольная","desc":"20 кг","price":2990,"unit":"шт","unit_ref":"u001","weight":3.0},
    {"name":"Телевизор 50\"","desc":"LED 4K","price":34990,"unit":"шт","unit_ref":"u001","weight":12.0},
    {"name":"Холодильник 250л","desc":"No Frost","price":42990,"unit":"шт","unit_ref":"u001","weight":65.0},
    {"name":"Стиральная машина","desc":"7 кг","price":29990,"unit":"шт","unit_ref":"u001","weight":55.0},
    {"name":"Посудомоечная машина","desc":"60 см","price":24990,"unit":"шт","unit_ref":"u001","weight":40.0},
    {"name":"Кондиционер","desc":"2.5 кВт","price":18990,"unit":"шт","unit_ref":"u001","weight":8.0},
    {"name":"Обогреватель","desc":"2 кВт","price":3490,"unit":"шт","unit_ref":"u001","weight":3.5},
    {"name":"Робот-пылесос","desc":"Навигация","price":19990,"unit":"шт","unit_ref":"u001","weight":3.2},
    {"name":"Блендер","desc":"1200 Вт","price":4990,"unit":"шт","unit_ref":"u001","weight":1.5},
    {"name":"Кофемашина","desc":"15 бар","price":15990,"unit":"шт","unit_ref":"u001","weight":5.0},
]

# ── Грузы (алгоритм: ~85% фура, ~15% сборный) ──
ГРУЗЫ_ФУРА=["Строительные материалы","Мебель","Электроника","Бытовая техника","Продукты питания","Канцелярия","Текстиль","Металлопрокат","Пластик","Химикаты"]
ГРУЗЫ_СБОРНЫЙ=["Мелкий товар для дома","Канцелярия мелким оптом","Запчасти и комплектующие","Упаковочные материалы","Хозтовары","Сантехника","Освещение","Инструменты"]

def gen_cargo():
    is_sbor = random.random() < 0.15
    if is_sbor:
        грузы = random.sample(ГРУЗЫ_СБОРНЫЙ, random.randint(2,4))
        return {"cargo": " + ".join(грузы), "cargo_type": "сборный", "weight": round(random.uniform(3, 12), 1)}
    else:
        return {"cargo": random.choice(ГРУЗЫ_ФУРА), "cargo_type": "фура", "weight": round(random.uniform(10, 22), 1)}

# ══════════════════════════════════════════════
# HTML — расширенная шапка + грузы + меню
# ══════════════════════════════════════════════
@app.route("/")
def index():
    return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>1C Routes</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui;background:#06070b;color:#e8eaf0;line-height:1.4}
.page{max-width:1400px;margin:0 auto;padding:.6rem 1.5rem}
.hdr{display:grid;grid-template-columns:repeat(6,1fr);gap:.4rem;margin-bottom:.5rem}
.stat{background:linear-gradient(145deg,#11121b,#14151f);border:1px solid #1e2035;border-radius:10px;padding:.55rem .4rem;text-align:center;transition:border-color .2s}
.stat:hover{border-color:rgba(99,102,241,.25)}
.stat .n{font-size:1.1rem;font-weight:800;color:#818cf8;letter-spacing:-.02em}
.stat .l{font-size:.5rem;color:#7c8298;text-transform:uppercase;letter-spacing:.04em;margin-top:.08rem}
.bar{display:flex;gap:.35rem;align-items:center;flex-wrap:wrap;padding:.35rem 0;border-bottom:1px solid #1e2035;margin-bottom:.4rem}
.ctrl{display:flex;gap:.2rem;align-items:center;flex-wrap:wrap}
.ctrl label{font-size:.63rem;color:#7c8298;display:flex;align-items:center;gap:.15rem;cursor:pointer;padding:.18rem .3rem;border-radius:4px;transition:.12s}
.ctrl label:hover{background:rgba(99,102,241,.05)}
.ctrl input[type=checkbox]{accent-color:#6366f1;width:11px;height:11px}
.ctrl select{background:#11121b;color:#e8eaf0;border:1px solid #1e2035;border-radius:4px;padding:.18rem .25rem;font-size:.63rem}
.gen{background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;border:none;padding:.28rem .6rem;border-radius:5px;cursor:pointer;font-size:.66rem;font-weight:600;transition:.12s}
.gen:hover{opacity:.85;transform:scale(1.02)}
.gen.sec{background:#1a1b28;border:1px solid #1e2035;color:#818cf8}
.gen.active{background:#34d399!important;color:#fff!important;border-color:#34d399!important}
.sep{width:1px;height:18px;background:#1e2035;flex-shrink:0}
.mw{position:relative}
.mb{background:#11121b;border:1px solid #1e2035;border-radius:6px;padding:.22rem .45rem;cursor:pointer;color:#7c8298;font-size:.68rem;transition:.12s;display:flex;align-items:center;gap:.2rem}
.mb:hover{border-color:#6366f1;color:#818cf8}
.md{position:absolute;top:calc(100% + 4px);right:0;min-width:200px;background:#11121b;border:1px solid #1e2035;border-radius:8px;box-shadow:0 12px 32px rgba(0,0,0,.6);padding:.25rem 0;opacity:0;visibility:hidden;transform:translateY(-4px);transition:.15s;z-index:100}
.md.show{opacity:1;visibility:visible;transform:translateY(0)}
.md a{display:flex;align-items:center;gap:.35rem;padding:.3rem .65rem;font-size:.66rem;color:#7c8298;text-decoration:none;transition:.1s}
.md a:hover{color:#818cf8;background:rgba(99,102,241,.05)}
.md .s{height:1px;background:linear-gradient(90deg,transparent,var(--bdr),transparent);margin:.15rem .5rem}
#map{height:calc(100vh - 200px);min-height:350px;border-radius:10px;border:1px solid #1e2035}
table{width:100%;border-collapse:collapse;background:#11121b;border:1px solid #1e2035;border-radius:8px;overflow:hidden;font-size:.66rem}
th{background:#13141e;padding:.32rem .38rem;text-align:left;font-size:.56rem;color:#7c8298;text-transform:uppercase;border-bottom:1px solid #1e2035;cursor:pointer;user-select:none;white-space:nowrap}
th:hover{color:#818cf8}
td{padding:.28rem .38rem;border-bottom:1px solid #1e2035}
tr:hover td{background:rgba(99,102,241,.025)}
.cb{display:flex;align-items:center;gap:.35rem;padding:.28rem .55rem;background:#11121b;border:1px solid #1e2035;border-radius:6px;cursor:pointer;color:#818cf8;font-size:.7rem;font-weight:600;width:100%;text-align:left;margin-top:.35rem;transition:.12s}
.cb:hover{border-color:#6366f1}
.cc{overflow:hidden;max-height:0;transition:max-height .4s ease}
.cc.open{max-height:3000px}
.au{display:flex;gap:.25rem;align-items:center;margin:.15rem 0}
.au code{flex:1;background:#13141e;padding:.18rem .35rem;border-radius:4px;font-size:.6rem;color:#22d3ee;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.au button{background:#6366f1;color:#fff;border:none;padding:.12rem .3rem;border-radius:4px;cursor:pointer;font-size:.55rem}
@keyframes blinkGreen{0%,100%{background:rgba(52,211,153,.08)}50%{background:rgba(52,211,153,.35)}}
.ct{display:inline-block;padding:.04rem .25rem;border-radius:3px;font-size:.52rem;font-weight:600;margin-left:.15rem}
.ct-f{background:rgba(99,102,241,.08);color:#818cf8;border:1px solid rgba(99,102,241,.12)}
.ct-s{background:rgba(251,146,60,.08);color:#fb923c;border:1px solid rgba(251,146,60,.12)}
</style></head><body>
<div class="page">
<div class="hdr">
  <div class="stat"><div class="n" id="s0">0</div><div class="l">Заказов</div></div>
  <div class="stat"><div class="n" id="s1">0</div><div class="l">км</div></div>
  <div class="stat"><div class="n" id="s2">0</div><div class="l">Перевозки ₽</div></div>
  <div class="stat"><div class="n" id="s3">0</div><div class="l">Товары ₽</div></div>
  <div class="stat"><div class="n" id="s4">0/0</div><div class="l">Фура/Сборн.</div></div>
  <div class="stat"><div class="n" id="s5">0</div><div class="l">Тонн</div></div>
</div>
<div class="bar">
  <div class="ctrl"><button class="gen" onclick="g1()">+ Заказ</button><button class="gen sec" onclick="g5()">+5</button><button class="gen sec" id="ab" onclick="ta()">▶ Онлайн</button></div>
  <div class="sep"></div>
  <div class="ctrl">
    <label><input type="checkbox" id="cR" checked onchange="tR()">Маршруты</label>
    <label><input type="checkbox" id="cA" checked onchange="tA()">Города</label>
    <label><input type="checkbox" id="cP" checked onchange="tP()">Цены</label>
    <label><input type="checkbox" id="cAn" onchange="tAn()">▶</label>
    <select id="cC" onchange="cC()"><option value="r">Цвета</option><option value="d">Расстояние</option><option value="p">Цена</option></select>
  </div>
  <div class="sep"></div>
  <div class="mw"><button class="mb" onclick="tm(event)">☰ Меню</button>
    <div class="md" id="mD">
      <a href="/map">🗺️ Полная карта</a><div class="s"></div>
      <a href="/api/xml/orders">📦 XML Заказы</a><a href="/api/xml/org">🏢 XML Организация</a>
      <a href="/api/xml/products">📦 XML Товары</a><a href="/api/json">📋 JSON</a>
      <div class="s"></div><a href="#" onclick="tApi();return false">📡 API endpoints</a>
    </div>
  </div>
</div>
<div id="map"></div>
<button class="cb" onclick="tT()"><span id="tA">▶</span> Маршруты (<span id="tC">0</span>)</button>
<div class="cc" id="tW"><table><thead><tr>
<th onclick="sr(0)">Заказ</th><th onclick="sr(1)">Контрагент</th><th onclick="sr(2)">Город</th><th onclick="sr(3)">Прибытие</th>
<th onclick="sr(4)">Груз</th><th onclick="sr(5)">Тип</th><th onclick="sr(6)">Тонн</th>
<th onclick="sr(7)">Расст.</th><th onclick="sr(8)">Цена</th><th onclick="sr(9)">Отпр.</th>
<th onclick="sr(10)">Статус</th>
</tr></thead><tbody id="tB"></tbody></table></div>
<button class="cb" onclick="tApi()"><span id="aA">▶</span> API для 1С</button>
<div class="cc" id="aW"><table>
<tr><td style="width:120px;color:#7c8298;font-size:.65rem">Заказы XML</td><td><div class="au"><code id="u1">http://localhost:5000/api/xml/orders</code><button onclick="cp('u1')">📋</button></div></td></tr>
<tr><td style="color:#7c8298;font-size:.65rem">Организация XML</td><td><div class="au"><code id="u2">http://localhost:5000/api/xml/org</code><button onclick="cp('u2')">📋</button></div></td></tr>
<tr><td style="color:#7c8298;font-size:.65rem">Товары XML</td><td><div class="au"><code id="u3">http://localhost:5000/api/xml/products</code><button onclick="cp('u3')">📋</button></div></td></tr>
</table></div>
</div>
<script>
const map=L.map('map',{zoomControl:!0}).setView([57,42],5);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',{attribution:'© OSM © CARTO',maxZoom:18}).addTo(map);
L.marker([55.7558,37.6173],{icon:L.divIcon({html:'<div style="background:#34d399;width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px #34d399;animation:pulse 2s infinite"></div>',className:'',iconSize:[14,14],iconAnchor:[7,7]})}).bindPopup('<b>Склад</b> Москва').addTo(map);

let RL=L.layerGroup().addTo(map),AL=L.layerGroup().addTo(map),AR=[],oc=0;
const CC=['#f472b6','#fb923c','#34d399','#22d3ee','#a78bfa','#fbbf24','#f87171','#818cf8','#c084fc','#2dd4bf','#e879f9','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
const ST={'Доставлен':'#34d399','В пути':'#22d3ee','На погрузке':'#fbbf24','Ожидает отправки':'#fb923c'};

function gc(r,s){if(s==='d')return r.distance>1000?'#f87171':r.distance>500?'#fb923c':r.distance>200?'#fbbf24':'#34d399';if(s==='p')return r.price>30000?'#f87171':r.price>15000?'#fb923c':'#34d399';return r.color}
function addRoute(r){
  if(r.coords.length<2)return;const s=document.getElementById('cC').value,c=gc(r,s);
  const ln=L.polyline(r.coords,{color:c,weight:2,opacity:0,dashArray:'8,8'}).addTo(RL);
  let st=0;const tot=35;
  const ai=setInterval(()=>{st++;const p=st/tot;ln.setStyle({opacity:p*.85,weight:2+p*1.5});
    if(st>=tot){clearInterval(ai);ln.setStyle({weight:3,dashArray:null});
      ln.bindPopup('<b>'+r.number+'</b> — '+r.name+'<br><b>'+r.city+'</b><hr style="border:1px solid #ddd;margin:3px 0">📦 '+r.cargo+' ('+r.cargoType+')<br>⚖️ '+r.weight+' т · 📏 '+r.distance+' км<br>🚛 <b>'+r.price.toLocaleString()+' руб.</b><br>📅 '+r.departure+' → '+r.arrival);
    }},35);
  if(r.lat)L.circleMarker([r.lat,r.lon],{radius:7,color:'#34d399',fill:!0,fillColor:'#34d399',fillOpacity:.5,weight:2}).bindPopup('<b>'+r.city+'</b><br>'+r.name).addTo(RL);
  L.circleMarker([55.7558,37.6173],{radius:3,color:'#fff',fillColor:'#34d399',fillOpacity:.8,weight:1}).addTo(RL);
}
function tR(){document.getElementById('cR').checked?RL.addTo(map):map.removeLayer(RL)}
function tA(){document.getElementById('cA').checked?AL.addTo(map):map.removeLayer(AL)}
function tP(){}
function cC(){RL.clearLayers();AR.forEach(r=>addRoute(r))}
let ai2=null;
function tAn(){if(document.getElementById('cAn').checked){let i=0;ai2=setInterval(()=>{RL.eachLayer(l=>{if(l.setStyle)l.setStyle({opacity:.1})});const ls=[];RL.eachLayer(l=>ls.push(l));if(ls[i]){ls[i].setStyle({opacity:1,weight:6});ls[i].openPopup()}i=(i+1)%ls.length},1200)}else{clearInterval(ai2);RL.eachLayer(l=>{if(l.setStyle)l.setStyle({opacity:.8,weight:3})})}}

async function g1(){try{
  const nd=await(await fetch('/api/new-order')).json();oc++;
  const rd=await(await fetch('/api/route?from=55.7558,37.6173&to='+nd.lat+','+nd.lon)).json();
  const r={number:'ЗК-'+String(oc).padStart(4,'0')+'-26',city:nd.city,name:nd.name,
    destination:'г. '+nd.city,cargo:nd.cargo,cargoType:nd.cargo_type,weight:nd.weight,
    distance:rd.distance_km||0,price:Math.round((rd.distance_km||0)*40),travel:rd.duration_hours||0,
    departure:new Date().toLocaleString('ru-RU'),arrival:new Date(Date.now()+(rd.duration_hours||0)*36e5).toLocaleString('ru-RU'),
    status:'На погрузке',sum:nd.sum||0,color:CC[oc%CC.length],lat:nd.lat,lon:nd.lon,coords:rd.route||[]};
  AR.push(r);addRoute(r);uS();aTR(r);
}catch(e){console.error(e)}}
async function g5(){for(let i=0;i<5;i++){await g1();await new Promise(r=>setTimeout(r,300))}}

let aI=null,aN=0;const MX=60;
function sA(){if(aI)return;aI=setInterval(()=>{if(aN>=MX){eA();return}g1();aN++},7000);
  document.getElementById('ab').textContent='⏸ Онлайн';document.getElementById('ab').classList.add('active');g1();aN=1}
function eA(){clearInterval(aI);aI=null;document.getElementById('ab').textContent='▶ Онлайн';document.getElementById('ab').classList.remove('active')}
function ta(){aI?eA():sA()}

const MX_T=20;
function aTR(r){
  const sc=ST[r.status]||'#7c8298';
  const ct=r.cargoType==='сборный'?'ct-s':'ct-f';
  const tr=document.createElement('tr');tr.style.animation='blinkGreen 2.5s ease-out';
  tr.innerHTML='<td><b>'+r.number+'</b></td><td>'+r.name+'</td><td>'+r.city+'</td><td style="color:#22d3ee">'+r.destination+'</td>'
    +'<td>'+r.cargo+'<span class="ct '+ct+'">'+r.cargoType+'</span></td>'
    +'<td style="font-size:.58rem">'+(r.cargoType==='сборный'?'📦':'🚛')+'</td>'
    +'<td style="text-align:right">'+r.weight+'</td>'
    +'<td style="text-align:right">'+r.distance+' км</td>'
    +'<td style="text-align:right;color:#f472b6"><b>'+r.price.toLocaleString()+'</b></td>'
    +'<td>'+r.departure+'</td><td><span style="color:'+sc+'">'+r.status+'</span></td>';
  document.getElementById('tB').prepend(tr);
  document.getElementById('tC').textContent=AR.length;
  const rows=document.getElementById('tB').rows;
  while(rows.length>MX_T)document.getElementById('tB').deleteRow(rows.length-1);
}
function uS(){document.getElementById('s0').textContent=AR.length;
  document.getElementById('s1').textContent=AR.reduce((s,r)=>s+r.distance,0).toLocaleString();
  document.getElementById('s2').textContent=AR.reduce((s,r)=>s+r.price,0).toLocaleString();
  document.getElementById('s3').textContent=AR.reduce((s,r)=>s+r.sum,0).toLocaleString();
  document.getElementById('s4').textContent=AR.filter(r=>r.cargoType==='фура').length+'/'+AR.filter(r=>r.cargoType==='сборный').length;
  document.getElementById('s5').textContent=AR.reduce((s,r)=>s+r.weight,0).toFixed(1);}

function tm(e){e.stopPropagation();document.getElementById('mD').classList.toggle('show')}
document.addEventListener('click',e=>{if(!e.target.closest('.mw'))document.getElementById('mD').classList.remove('show')});
function tT(){const e=document.getElementById('tW'),a=document.getElementById('tA');e.classList.toggle('open');a.textContent=e.classList.contains('open')?'▼':'▶'}
function tApi(){const e=document.getElementById('aW'),a=document.getElementById('aA');e.classList.toggle('open');a.textContent=e.classList.contains('open')?'▼':'▶'}
function cp(id){navigator.clipboard.writeText(document.getElementById(id).textContent).then(()=>{const b=document.getElementById(id).nextElementSibling;b.textContent='✅';setTimeout(()=>b.textContent='📋',1200)})}
let sd=1;
function sr(c){const tb=document.getElementById('tB'),rows=Array.from(tb.rows);rows.sort((a,b)=>{let va=a.cells[c].textContent.trim(),vb=b.cells[c].textContent.trim(),na=parseFloat(va.replace(/[^0-9.-]/g,'')),nb=parseFloat(vb.replace(/[^0-9.-]/g,''));if(!isNaN(na)&&!isNaN(nb))return(na-nb)*sd;return va.localeCompare(vb,'ru')*sd});sd*=-1;rows.forEach(r=>tb.appendChild(r))}
</script></body></html>'''

# ── New Order API ──
@app.route("/api/new-order")
def new_order():
    г=random.choice(ГОРОДА_ЦЕНТР)
    lat=г["lat"]+random.uniform(-0.03,0.03)
    lon=г["lon"]+random.uniform(-0.03,0.03)
    кт=random.choice(["ООО «ТехноПром»","ЗАО «СтройМаш»","ООО «АльфаСтрой»","ПАО «ПромСвязь»","ООО «МегаФуд»",
        "АО «ТрансЛогистик»","ООО «ИнфоСервис»","ООО «ПромТехника»","ЗАО «ЭнергоСнаб»","ООО «Восток-Трейд»",
        "ООО «НовыйГоризонт»","АО «СеверСталь»","ООО «Агро-Плюс»","ПАО «Ростелеком»","ООО «МедТехника»",
        "ООО «ЛогистикПро»","АО «АвиаТехСервис»","ООО «СтройДвор»","ООО «ТехноМир»","ЗАО «МеталлПром»"])
    items=random.sample(PRODUCTS,random.randint(2,5))
    total=sum(round(p["price"]*random.randint(1,10),2) for p in items)
    cargo=gen_cargo()
    return jsonify({"city":г["name"],"lat":round(lat,6),"lon":round(lon,6),"name":кт,"sum":round(total,2),**cargo})

@app.route("/api/status")
def status():return jsonify({"status":"ok"})

@app.route("/map")
def map_page():
    cache=load_cache();m=folium.Map(location=[57,42],zoom_start=5,tiles=None,control_scale=True)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",attr='© OSM © CARTO',name="Дороги").add_to(m)
    folium.TileLayer(tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",attr='© OSM',name="OSM").add_to(m)
    folium.Marker([55.7558,37.6173],popup="<b>Склад</b> Москва",icon=folium.Icon(color="green",icon="warehouse",prefix="fa")).add_to(m)
    rg=folium.FeatureGroup(name="Маршруты")
    for i,o in enumerate(cache.get("orders",[])):
        rc=o.get("route",[])
        if rc and len(rc)>1:
            folium.PolyLine(rc,color=CC[i%len(CC)],weight=3,opacity=.7,
                popup=f"<b>{o.get('number','')}</b><br>{o.get('distance_km',0)} км · {o.get('freight_price',0):,} руб.").add_to(rg)
    rg.add_to(m);folium.LayerControl().add_to(m)
    return Response(m._repr_html_(),mimetype="text/html")

CC=['#f472b6','#fb923c','#34d399','#22d3ee','#a78bfa','#fbbf24','#f87171','#818cf8','#c084fc','#2dd4bf','#e879f9','#f59e0b','#ef4444','#8b5cf6','#06b6d4']

@app.route("/api/route")
def api_route():
    try:
        lat1,lon1=map(float,request.args.get("from","55.7558,37.6173").split(","))
        lat2,lon2=map(float,request.args.get("to","54.5293,36.2754").split(","))
        r=get_route_road(lat1,lon1,lat2,lon2)
        return jsonify({"from":{"lat":lat1,"lon":lon1},"to":{"lat":lat2,"lon":lon2},"distance_km":r["distance_km"],"duration_hours":r["duration_hours"],"points":len(r["coordinates"]),"route":r["coordinates"]})
    except Exception as e:return jsonify({"error":str(e)}),400

@app.route("/api/json")
def api_json():return jsonify(load_cache())
@app.route("/api/json/orders")
def api_json_orders():return jsonify(load_cache().get("orders",[]))
@app.route("/api/org")
def api_org():return jsonify(ORG)
@app.route("/api/products")
def api_products():return jsonify(PRODUCTS)

@app.route("/api/xml/orders")
def xml_orders():
    cache=load_cache();orders=cache.get("orders",[]);now=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    L=['<?xml version="1.0" encoding="UTF-8"?>','<Message xmlns:msg="http://www.1c.ru/SSL/Exchange/Message" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
    f'\t<msg:Header><msg:Format>http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8</msg:Format><msg:CreationDate>{now}</msg:CreationDate><msg:AvailableVersion>1.8</msg:AvailableVersion></msg:Header>',
    f'\t<Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8">',
    f'\t\t<Справочник.Валюты><КлючевыеСвойства><Ссылка>7e3e0ef4-8295-11f1-8af8-04ecd881cf53</Ссылка><ДанныеКлассификатора><Код>643</Код><Наименование>руб.</Наименование></ДанныеКлассификатора></КлючевыеСвойства><ПараметрыПрописи>рубль, рубля, рублей, м, копейка, копейки, копеек, ж, 2 знака</ПараметрыПрописи></Справочник.Валюты>']
    kr={}
    for o in orders:
        n=o.get("counteragent_name","")
        if n and n not in kr:kr[n]=str(uuid.uuid4())
    for n,r in kr.items():L.append(f'\t\t<Справочник.Контрагенты><КлючевыеСвойства><Ссылка>{r}</Ссылка><Наименование>{xml_escape(n)}</Наименование><НаименованиеПолное>{xml_escape(n)}</НаименованиеПолное><ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо></КлючевыеСвойства></Справочник.Контрагенты>')
    for o in orders:
        r=kr.get(o.get("counteragent_name",""),str(uuid.uuid4()))
        L.append(f'\t\t<Документ.ЗаказКлиента><КлючевыеСвойства><Ссылка>{str(uuid.uuid4())}</Ссылка><Номер>{o.get("number","")}</Номер><Дата>{o.get("date","")}</Дата><Проведен>true</Проведен></КлючевыеСвойства><Организация><Ссылка>553d56f1-8295-11f1-8af8-04ecd881cf53</Ссылка><Наименование>Управленческая организация</Наименование></Организация><Контрагент><Ссылка>{r}</Ссылка><Наименование>{xml_escape(o.get("counteragent_name",""))}</Наименование><НаименованиеПолное>{xml_escape(o.get("counteragent_name",""))}</НаименованиеПолное><ЮридическоеФизическоеЛицо>ЮридическоеЛицо</ЮридическоеФизическоеЛицо></Контрагент><Валюта><Ссылка>7e3e0ef4-8295-11f1-8af8-04ecd881cf53</Ссылка><Наименование>руб.</Наименование></Валюта><Сумма>{o.get("sum",0)}</Сумма><Комментарий>{xml_escape(o.get("comment",""))}</Комментарий><Товары>')
        for it in o.get("items",[]):L.append(f'\t\t\t<Строка><НомерСтрокиДокумента>{it.get("line",0)}</НомерСтрокиДокумента><ДанныеНоменклатуры><Ссылка>{str(uuid.uuid4())}</Ссылка><Наименование>{xml_escape(it.get("item",""))}</Наименование></ДанныеНоменклатуры><ЕдиницаИзмерения><Ссылка>{str(uuid.uuid4())}</Ссылка><Наименование>{it.get("unit","шт")}</Наименование></ЕдиницаИзмерения><Количество>{it.get("qty",0)}</Количество><Цена>{it.get("price",0)}</Цена><Сумма>{it.get("sum",0)}</Сумма><СтавкаНДС>НДС20</СтавкаНДС><СуммаНДС>{round(it.get("sum",0)*.2,2)}</СуммаНДС></Строка>')
        L.append(f'\t\t\t</Товары></Документ.ЗаказКлиента>')
    L.extend([f'\t</Body>','</Message>'])
    return Response("\n".join(L),mimetype="text/xml; charset=utf-8")

@app.route("/api/xml/org")
def xml_org():
    o=ORG;now=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return Response(f'''<?xml version="1.0" encoding="UTF-8"?>
<Message xmlns:msg="http://www.1c.ru/SSL/Exchange/Message"><msg:Header><msg:Format>http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8</msg:Format><msg:CreationDate>{now}</msg:CreationDate><msg:AvailableVersion>1.8</msg:AvailableVersion></msg:Header>
<Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8"><Справочник.Организации><КлючевыеСвойства><Ссылка>{o["ref"]}</Ссылка><Наименование>{xml_escape(o["name"])}</Наименование><НаименованиеПолное>{xml_escape(o["name_full"])}</НаименованиеПолное><ИНН>{o["inn"]}</ИНН><КПП>{o["kpp"]}</КПП><ЮридическоеФизическоеЛицо>{o["juridical"]}</ЮридическоеФизическоеЛицо></КлючевыеСвойства><Префикс>ЦС</Префикс></Справочник.Организации></Body></Message>''',mimetype="text/xml; charset=utf-8")

@app.route("/api/xml/products")
def xml_products():
    now=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    L=['<?xml version="1.0" encoding="UTF-8"?>','<Message xmlns:msg="http://www.1c.ru/SSL/Exchange/Message"><msg:Header><msg:Format>http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8</msg:Format><msg:CreationDate>{now}</msg:CreationDate><msg:AvailableVersion>1.8</msg:AvailableVersion></msg:Header>',
    '\t<Body xmlns="http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.8">',
    '\t\t<Справочник.НоменклатураГруппа><КлючевыеСвойства><Ссылка>grp-home</Ссылка><Наименование>Товары для дома</Наименование></КлючевыеСвойства></Справочник.НоменклатураГруппа>']
    for i,p in enumerate(PRODUCTS,1):L.append(f'\t\t<Справочник.Номенклатура><КлючевыеСвойства><Ссылка>{str(uuid.uuid4())}</Ссылка><Наименование>{xml_escape(p["name"])}</Наименование><КодВПрограмме>{str(i).zfill(5)}</КодВПрограмме></КлючевыеСвойства><ТипНоменклатуры>Товар</ТипНоменклатуры><Описание>{xml_escape(p["desc"])}</Описание><ЕдиницаИзмерения><Ссылка>{p["unit_ref"]}</Ссылка><Наименование>{p["unit"]}</Наименование></ЕдиницаИзмерения><СтавкаНДС>НДС20</СтавкаНДС><Вес>{p["weight"]}</Вес></Справочник.Номенклатура>')
    L.extend(['\t</Body>','</Message>'])
    return Response("\n".join(L),mimetype="text/xml; charset=utf-8")

@app.route("/wsdl")
def wsdl():return Response(open("wsdl.xml","r",encoding="utf-8").read(),mimetype="text/xml")

if __name__=="__main__":
    print("="*60);print("  1C Routes v1.4 — Грузы + Шапка");print("  http://localhost:5000");print("="*60)
    app.run(debug=True,port=5000)
