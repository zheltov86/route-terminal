from flask import Flask, jsonify, Response
import json, os, random
from datetime import datetime

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), "orders.json")

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.route("/")
def index(): return Response(HTML, mimetype="text/html")

@app.route("/api/orders")
def api_orders(): return jsonify(load_orders())

@app.route("/api/random-order")
def api_random_order():
    orders = load_orders()
    if not orders: return jsonify({"error": "empty"}), 404
    o = dict(random.choice(orders))
    o["number"] = "ZK-" + str(random.randint(10000, 99999)) + "-26"
    o["date"] = datetime.now().strftime("%Y-%m-%d")
    o["status"] = random.choice(["New", "Processing", "Confirmed", "InTransit", "Delivered"])
    o["client"] = random.choice(["OOO TechnoProm","ZAO StroiMash","OOO AlphaStroy","PAO PromSvyaz","OOO MegaFood","AO TransLogistik","OOO InfoService","OOO PromTechnika","ZAO EnergoSnab","OOO Vostok-Trade"])
    o["delivery"] = random.choice(["Auto","Rail","Air","Sea"])
    o["notes"] = random.choice(["Standard delivery","Express required","Fragile goods","Perishable","Bulk order"])
    return jsonify(o)

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
.toolbar{display:flex;gap:4px;margin-left:16px}
.btn{background:#1a1b28;border:1px solid #1e2035;color:#8b8fa8;padding:3px 10px;border-radius:4px;font-size:9px;font-weight:600;cursor:pointer;font-family:inherit}
.btn:hover{border-color:#6366f1;color:#818cf8}
.btn.pri{background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;border-color:transparent}
.btn.dng{border-color:#dc2626;color:#f87171}
.btn.on{background:#059669;color:#fff;border-color:#34d399}
.sep{width:1px;height:14px;background:#1e2035}
.page{display:flex;height:calc(100vh - 34px)}
.left{flex:1;display:flex;flex-direction:column;min-width:0}
#map{flex:1;min-height:0}
.tbl{height:180px;border-top:1px solid #1e2035;flex-shrink:0;overflow-y:auto;overflow-x:hidden;background:#0a0b0f}
.tbl::-webkit-scrollbar{width:4px}
.tbl::-webkit-scrollbar-track{background:#0f1017}
.tbl::-webkit-scrollbar-thumb{background:#2a2d45;border-radius:2px}
table{width:100%;border-collapse:collapse;font-size:9px}
thead{position:sticky;top:0;z-index:2}
th{background:#13141e;padding:4px 6px;text-align:left;font-size:7px;color:#565a72;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #1e2035;white-space:nowrap;cursor:pointer;user-select:none}
th:hover{color:#818cf8}
td{padding:3px 6px;border-bottom:1px solid rgba(30,32,53,.3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px}
tr{transition:background .15s}
tr.hl td{background:rgba(99,102,241,.15)!important}
tr.active td{background:rgba(52,211,153,.1)!important}
tr.shortest td{background:rgba(251,191,36,.08)!important}
tr.shortest td:first-child::before{content:'\2B50 ';font-size:8px}
.badge{display:inline-block;padding:0 4px;border-radius:3px;font-size:7px;font-weight:600}
.b-New{background:rgba(129,140,248,.1);color:#818cf8;border:1px solid rgba(129,140,248,.15)}
.b-Processing{background:rgba(251,191,36,.1);color:#fbbf24;border:1px solid rgba(251,191,36,.15)}
.b-Confirmed{background:rgba(34,211,238,.1);color:#22d3ee;border:1px solid rgba(34,211,238,.15)}
.b-InTransit{background:rgba(251,146,60,.1);color:#fb923c;border:1px solid rgba(251,146,60,.15)}
.b-Delivered{background:rgba(52,211,153,.1);color:#34d399;border:1px solid rgba(52,211,153,.15)}
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
.ir .vl.gold{color:#fbbf24}
.route-box{margin-top:6px;padding:5px;background:#13141e;border:1px solid #1e2035;border-radius:4px;font-size:8px;color:#565a72;line-height:1.6}
.route-box b{color:#22d3ee}
.shortest-badge{display:inline-block;padding:1px 4px;border-radius:3px;font-size:7px;font-weight:700;background:rgba(251,191,36,.15);color:#fbbf24;border:1px solid rgba(251,191,36,.3);margin-left:4px}
.leaflet-popup-content-wrapper{background:#13141e!important;border:1px solid #1e2035!important;border-radius:8px!important;color:#e8eaf0!important;box-shadow:0 8px 32px rgba(0,0,0,.6)!important;min-width:220px}
.leaflet-popup-tip{background:#13141e!important}
.leaflet-popup-content{font-family:'Inter',sans-serif;font-size:10px;line-height:1.5;margin:8px 10px}
.lp-t{font-weight:700;color:#818cf8;margin-bottom:4px;font-size:12px}
.lp-r{display:flex;justify-content:space-between;padding:2px 0;font-size:9px}
.lp-r .a{color:#565a72}.lp-r .b{color:#e8eaf0;font-weight:500;font-family:'JetBrains Mono',monospace}
.lp-r .b.pk{color:#f472b6}.lp-r .b.cy{color:#22d3ee}.lp-r .b.gd{color:#fbbf24}
@keyframes fadeIn{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:translateY(0)}}
.row-new{animation:fadeIn .3s ease-out}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo"><i>RT</i><div><b>Route Terminal</b><br><small>Interactive Order Map</small></div></div>
  <div class="toolbar">
    <button class="btn pri" id="bAdd">+ Order</button>
    <button class="btn" id="bAdd5">+5</button>
    <button class="btn" id="bAuto">Auto 10s</button>
    <div class="sep"></div>
    <button class="btn dng" id="bClear">Clear</button>
  </div>
</div>
<div class="page">
  <div class="left">
    <div id="map"></div>
    <div class="tbl"><table><thead><tr>
      <th class="sh" data-c="0">No</th><th class="sh" data-c="1">From</th><th class="sh" data-c="2">To</th>
      <th class="sh" data-c="3">Cargo</th><th class="sh" data-c="4">km</th><th class="sh" data-c="5">Status</th>
    </tr></thead><tbody id="tB"></tbody></table></div>
  </div>
  <div class="rpanel">
    <div class="stats-box">
      <h4>Statistics</h4>
      <div class="sg">
        <div class="s"><div class="v" id="sT">0</div><div class="l">Orders</div></div>
        <div class="s up"><div class="v" id="sD">0</div><div class="l">Done</div></div>
        <div class="s"><div class="v" id="sK">0</div><div class="l">km</div></div>
      </div>
    </div>
    <div class="info-box" id="iBox"><div class="info-empty">Hover on route or click row</div></div>
  </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var WH=[55.7558,37.6173];
var CC=['#f472b6','#fb923c','#34d399','#22d3ee','#a78bfa','#fbbf24','#f87171','#818cf8','#c084fc','#2dd4bf','#e879f9','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
var orders=[],autoI=null,cIdx=0,selectedNum=null,shortestNum=null;

var map=L.map('map',{zoomControl:false,attributionControl:false}).setView([57,42],5);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:19}).addTo(map);
var routeLayer=L.layerGroup().addTo(map);
var markerLayer=L.layerGroup().addTo(map);

L.marker(WH,{icon:L.divIcon({html:'<div style="width:18px;height:18px;background:linear-gradient(135deg,#34d399,#059669);border-radius:50%;border:3px solid #fff;box-shadow:0 0 14px rgba(52,211,153,.6);display:flex;align-items:center;justify-content:center"><div style="width:5px;height:5px;background:#fff;border-radius:50%"></div></div>',className:'',iconSize:[18,18],iconAnchor:[9,9]})}).bindPopup('<b>Warehouse Moscow</b>').addTo(map);

function osrm(a,b){
  return fetch('https://router.project-osrm.org/route/v1/driving/'+a[1]+','+a[0]+';'+b[1]+','+b[0]+'?overview=full&geometries=geojson')
    .then(function(r){return r.json()})
    .then(function(d){if(d.code==='Ok'&&d.routes&&d.routes[0]){var r=d.routes[0];var c=r.geometry.coordinates.map(function(p){return[p[1],p[0]]});return{coords:c,dist:Math.round(r.distance/1000),dur:Math.round(r.duration/3600*10)/10};}return null;})
    .catch(function(){return null});
}

function buildRoute(stops){
  var pts=[WH];stops.forEach(function(s){pts.push([s.lat,s.lon]);});
  var allC=[],td=0,tu=0,i=0;
  function next(){
    if(i>=pts.length-1)return Promise.resolve({coords:allC,dist:td,dur:tu});
    return osrm(pts[i],pts[i+1]).then(function(r){
      if(r){if(i>0&&r.coords.length>0)r.coords=r.coords.slice(1);allC=allC.concat(r.coords);td+=r.dist;tu+=r.dur;}
      else{allC.push(pts[i],pts[i+1]);var dx=pts[i+1][0]-pts[i][0],dy=pts[i+1][1]-pts[i][1];td+=Math.round(Math.sqrt(dx*dx+dy*dy)*111);tu+=Math.round(Math.sqrt(dx*dx+dy*dy)*111/80*10)/10;}
      i++;return next();
    });
  }
  return next();
}

function findShortest(){
  var min=Infinity,sn=null;
  orders.forEach(function(o){if(o._dist&&o._dist>0&&o._dist<min){min=o._dist;sn=o.number;}});
  shortestNum=sn;
  document.querySelectorAll('#tB tr').forEach(function(tr){
    tr.classList.toggle('shortest',tr.getAttribute('data-num')===sn);
  });
}

function updateStats(){
  var n=orders.length,dl=0,km=0;
  orders.forEach(function(o){if(o.status==='Delivered')dl++;km+=o._dist||0;});
  document.getElementById('sT').textContent=n;
  document.getElementById('sD').textContent=dl;
  document.getElementById('sK').textContent=Math.round(km).toLocaleString();
}

function highlightRoute(num,on){
  if(num===shortestNum&&on)return;
  routeLayer.eachLayer(function(l){if(l._n===num){l.setStyle({weight:on?5:2.5,opacity:on?1:0.85});if(on)l.bringToFront();}});
  markerLayer.eachLayer(function(l){if(l._n===num&&on)l.bringToFront();});
}

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

function showInfo(o){
  var st=o.status||'New';
  var isShort=o.number===shortestNum;
  var el=document.getElementById('iBox');if(!el)return;
  el.innerHTML='<div class="info-hdr">'+o.number+(isShort?'<span class="shortest-badge">SHORTEST</span>':'')+'</div>'
    +'<div class="ir"><span class="lb">From</span><span class="vl">'+(o.from_city||'Moscow')+'</span></div>'
    +'<div class="ir"><span class="lb">To</span><span class="vl">'+o.city+'</span></div>'
    +'<div class="ir"><span class="lb">Client</span><span class="vl">'+(o.client||'...')+'</span></div>'
    +'<div class="ir"><span class="lb">Cargo</span><span class="vl">'+o.cargo+'</span></div>'
    +'<div class="ir"><span class="lb">Distance</span><span class="vl cyan">'+(o._dist||'...')+' km</span></div>'
    +'<div class="ir"><span class="lb">Duration</span><span class="vl cyan">'+(o._dur||'...')+' h</span></div>'
    +'<div class="ir"><span class="lb">Weight</span><span class="vl">'+o.weight+' t</span></div>'
    +'<div class="ir"><span class="lb">Sum</span><span class="vl pink">'+o.sum.toLocaleString()+' rub</span></div>'
    +'<div class="ir"><span class="lb">Status</span><span class="vl"><span class="badge b-'+st+'">'+st+'</span></span></div>'
    +'<div class="ir"><span class="lb">Delivery</span><span class="vl">'+(o.delivery||'...')+'</span></div>'
    +'<div class="ir"><span class="lb">Date</span><span class="vl">'+o.date+'</span></div>'
    +'<div class="ir"><span class="lb">Notes</span><span class="vl">'+(o.notes||'...')+'</span></div>'
    +'<div class="route-box"><b>Route:</b> '+(o.from_city||'Moscow')+' &rarr; '+o.city+'</div>';
}

function popupHtml(o,s,ct){
  var st=o.status||'New';
  var isShort=o.number===shortestNum;
  return '<div class="lp-t">'+o.number+(isShort?' <span style="color:#fbbf24">\u2B50</span>':'')+'</div>'
    +'<div class="lp-r"><span class="a">From</span><span class="b">'+(o.from_city||'Moscow')+'</span></div>'
    +'<div class="lp-r"><span class="a">To</span><span class="b">'+s.name+'</span></div>'
    +'<div class="lp-r"><span class="a">Client</span><span class="b">'+(o.client||'...')+'</span></div>'
    +'<div class="lp-r"><span class="a">Cargo</span><span class="b">'+o.cargo+' ('+ct+')</span></div>'
    +'<div class="lp-r"><span class="a">Weight</span><span class="b">'+o.weight+' t</span></div>'
    +'<div class="lp-r"><span class="a">Distance</span><span class="b cy">'+(o._dist||'...')+' km</span></div>'
    +'<div class="lp-r"><span class="a">Duration</span><span class="b cy">'+(o._dur||'...')+' h</span></div>'
    +'<div class="lp-r"><span class="a">Sum</span><span class="b pk">'+o.sum.toLocaleString()+' rub</span></div>'
    +'<div class="lp-r"><span class="a">Status</span><span class="b"><span class="badge b-'+st+'">'+st+'</span></span></div>'
    +'<div class="lp-r"><span class="a">Delivery</span><span class="b">'+(o.delivery||'...')+'</span></div>'
    +'<div class="lp-r"><span class="a">Date</span><span class="b">'+o.date+'</span></div>'
    +'<div class="lp-r"><span class="a">Notes</span><span class="b">'+(o.notes||'...')+'</span></div>';
}

function drawRoute(o){
  var color=CC[cIdx%CC.length];cIdx++;
  o._color=color;
  var isShort=o.number===shortestNum;
  if(o._coords&&o._coords.length>=2){
    var style={color:isShort?'#fbbf24':color,weight:isShort?4:2.5,opacity:isShort?1:0.85};
    if(isShort){style.dashArray=null;}
    var ln=L.polyline(o._coords,style).addTo(routeLayer);
    ln._n=o.number;
    ln.bringToFront();
    var num=o.number;
    if(!isShort){
      ln.on('mouseover',function(){highlightRoute(num,true);highlightRow(num,true);showInfo(findO(num));});
      ln.on('mouseout',function(){highlightRoute(num,false);highlightRow(num,false);});
    }else{
      ln.on('mouseover',function(){showInfo(findO(num));});
    }
  }
  if(o.stops){
    o.stops.forEach(function(s,i){
      var last=i===o.stops.length-1;
      var mc=isShort?'#fbbf24':(last?color:'#fff');
      var mk=L.marker([s.lat,s.lon],{icon:L.divIcon({html:'<div style="width:'+(last?9:6)+'px;height:'+(last?9:6)+'px;background:'+mc+';border-radius:50%;border:2px solid rgba(255,255,255,'+(last?1:0.5)+');box-shadow:0 0 6px '+mc+'80"></div>',className:'',iconSize:[last?9:6,last?9:6],iconAnchor:[last?5:3,last?5:3]})}).addTo(markerLayer);
      mk._n=o.number;
      var ct=o.cargo_type==='sborniy'?'Sbor':'Fura';
      mk.bindPopup(popupHtml(o,s,ct),{maxWidth:280});
    });
  }
}

function addRow(o,prep){
  var st=o.status||'New';
  var tr=document.createElement('tr');
  if(prep)tr.className='row-new';
  tr.setAttribute('data-num',o.number);
  var h='<td style="font-family:JetBrains Mono,monospace;color:#818cf8;font-weight:600;font-size:8px">'+o.number+'</td>';
  h+='<td style="font-size:8px">'+(o.from_city||'Moscow')+'</td>';
  h+='<td style="font-size:8px">'+o.city+'</td>';
  h+='<td style="font-size:7px">'+o.cargo+'</td>';
  h+='<td style="font-size:8px;color:#22d3ee;font-family:JetBrains Mono,monospace">'+(o._dist?o._dist+' km':'...')+'</td>';
  h+='<td><span class="badge b-'+st+'">'+st+'</span></td>';
  tr.innerHTML=h;
  var num=o.number;
  var order=o;
  tr.onmouseenter=function(){highlightRoute(num,true);showInfo(order);};
  tr.onmouseleave=function(){highlightRoute(num,false);};
  tr.onclick=function(){
    document.querySelectorAll('#tB tr.active').forEach(function(r){r.classList.remove('active')});
    tr.classList.add('active');
    selectedNum=num;
    routeLayer.eachLayer(function(l){if(l._n===num){l.setStyle({weight:5,opacity:1});l.bringToFront();map.fitBounds(l.getBounds().pad(0.3));}});
    markerLayer.eachLayer(function(l){if(l._n===num){l.bringToFront();try{l.openPopup();}catch(e){}}});
    showInfo(order);
  };
  var tb=document.getElementById('tB');
  if(prep)tb.insertBefore(tr,tb.firstChild);else tb.appendChild(tr);
}

function findO(num){for(var i=0;i<orders.length;i++){if(orders[i].number===num)return orders[i];}return null;}

function refreshAll(){
  routeLayer.clearLayers();markerLayer.clearLayers();cIdx=0;
  orders.forEach(function(o){drawRoute(o);});
  document.getElementById('tB').innerHTML='';
  orders.forEach(function(o){addRow(o,false);});
  findShortest();
}

function addOneOrder(){
  return fetch('/api/random-order').then(function(r){return r.json()}).then(function(o){
    o._coords=[];o._dist=0;o._dur=0;
    orders.unshift(o);
    addRow(o,true);
    drawRoute(o);
    updateStats();
    buildRoute(o.stops||[]).then(function(r){
      o._coords=r.coords;o._dist=r.dist;o._dur=r.dur;
      routeLayer.clearLayers();markerLayer.clearLayers();cIdx=0;
      orders.forEach(function(x){drawRoute(x);});
      var rows=document.getElementById('tB').rows;
      for(var i=0;i<rows.length;i++){
        if(rows[i].getAttribute('data-num')===o.number){rows[i].cells[4].textContent=o._dist+' km';break;}
      }
      updateStats();
      findShortest();
    }).catch(function(){});
  }).catch(function(e){console.error('addOneOrder error:',e);});
}

document.getElementById('bAdd').onclick=function(){addOneOrder();};
document.getElementById('bAdd5').onclick=function(){var i=0;function nx(){if(i>=5)return;i++;addOneOrder().then(function(){setTimeout(nx,600)});}nx();};
document.getElementById('bAuto').onclick=function(){
  var b=document.getElementById('bAuto');
  if(autoI){clearInterval(autoI);autoI=null;b.textContent='Auto 10s';b.classList.remove('on');}
  else{addOneOrder();autoI=setInterval(addOneOrder,10000);b.textContent='Stop';b.classList.add('on');}
};
document.getElementById('bClear').onclick=function(){
  orders=[];cIdx=0;selectedNum=null;shortestNum=null;
  routeLayer.clearLayers();markerLayer.clearLayers();
  document.getElementById('tB').innerHTML='';updateStats();
  map.setView([57,42],5);
  document.getElementById('iBox').innerHTML='<div class="info-empty">Hover on route or click row</div>';
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
    print("  Route Terminal - Interactive Map")
    print("  http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)
