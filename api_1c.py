"""
1C API Service — EnterpriseData 1.8
Strict XML parsing per Схема_1_8_6.xsd and Тест.xml format.
Port 5001, API key: route-terminal-1c-key-2026
"""
import os, re, json, uuid, logging, threading
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_1c")
API_KEY = "route-terminal-1c-key-2026"
PORT = 5001

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(os.path.join(DATA_DIR, "api.log"), encoding="utf-8"), logging.StreamHandler()])
log = logging.getLogger("1c-api")

tasks = {}
refs_db = {}
orders_db = {}

SPRAVOCHNIKI_ORDER = [
    "Справочник.Валюты",
    "Справочник.ЕдиницыИзмерения",
    "Справочник.Организации",
    "Справочник.Контрагенты",
    "Справочник.СтатьиДоходов",
    "Справочник.Пользователи",
]

# ─── Auth ───
def check_auth():
    return (request.headers.get("X-API-Key") or request.args.get("api_key")) == API_KEY

@app.before_request
def auth_middleware():
    if request.endpoint and request.endpoint not in ("health", "index") and not check_auth():
        return jsonify({"success": False, "error": "UNAUTHORIZED", "message": "Invalid or missing API key"}), 401

# ─── XML Parsing (strict EnterpriseData 1.8) ───

def extract_tag(block, tag):
    """Extract value from <tag>value</tag>"""
    s = block.find(f"<{tag}>")
    if s == -1: return None
    s += len(tag) + 2
    e = block.find(f"</{tag}>", s)
    return block[s:e].strip() if e != -1 else None

def extract_key_prop(block, tag):
    """Extract from <КлючевыеСвойства><tag>...</tag></КлючевыеСвойства>"""
    ks = block.find("<КлючевыеСвойства>")
    if ks == -1: return None
    ke = block.find("</КлючевыеСвойства>", ks)
    if ke == -1: return None
    return extract_tag(block[ks:ke], tag)

def extract_ref(block):
    return extract_key_prop(block, "Ссылка")

def extract_all_blocks(xml, tag):
    """Extract all <tag>...</tag> blocks from XML."""
    blocks = []
    idx = 0
    while True:
        s = xml.find(f"<{tag}>", idx)
        if s == -1: break
        e = xml.find(f"</{tag}>", s)
        if e == -1: break
        blocks.append(xml[s:e + len(tag) + 3])
        idx = e + len(tag) + 3
    return blocks

def parse_spravochnik(xml, tag):
    """Parse a single reference (Справочник) from XML block."""
    ref = extract_ref(xml)
    name = extract_key_prop(xml, "Наименование") or extract_key_prop(xml, "Код") or ""
    full_name = extract_tag(xml, "НаименованиеПолное") or name
    code = ""
    kd = xml.find("<ДанныеКлассификатора>")
    if kd != -1:
        kd_end = xml.find("</ДанныеКлассификатора>", kd)
        if kd_end != -1:
            code = extract_tag(xml[kd:kd_end], "Код") or ""
    return {"ref": ref, "name": name, "full_name": full_name, "code": code.strip(), "raw_len": len(xml)}

def parse_order(xml):
    """Parse Документ.ЗаказКлиента from XML block."""
    ref = extract_ref(xml)
    number = extract_key_prop(xml, "Номер")
    date = extract_key_prop(xml, "Дата")
    posted = extract_key_prop(xml, "Проведен")

    org_ref = org_name = ""
    org_s = xml.find("<Организация>")
    if org_s != -1:
        org_e = xml.find("</Организация>", org_s)
        if org_e != -1:
            org_ref = extract_ref(xml[org_s:org_e])
            org_name = extract_tag(xml[org_s:org_e], "Наименование") or ""

    client_ref = client_name = client_full = client_jl = ""
    cl_s = xml.find("<Контрагент>")
    if cl_s != -1:
        cl_e = xml.find("</Контрагент>", cl_s)
        if cl_e != -1:
            cb = xml[cl_s:cl_e]
            client_ref = extract_ref(cb)
            client_name = extract_tag(cb, "Наименование") or ""
            client_full = extract_tag(cb, "НаименованиеПолное") or ""
            client_jl = extract_tag(cb, "ЮридическоеФизическоеЛицо") or ""

    cur_ref = cur_name = ""
    cur_s = xml.find("<Валюта>")
    if cur_s != -1:
        cur_e = xml.find("</Валюта>", cur_s)
        if cur_e != -1:
            cur_ref = extract_ref(xml[cur_s:cur_e])
            cur_name = extract_tag(xml[cur_s:cur_e], "Наименование") or ""

    amount = 0.0
    try: amount = float(extract_tag(xml, "Сумма") or "0")
    except: pass
    comment = extract_tag(xml, "Комментарий") or ""

    items = []
    items_s = xml.find("<Товары>")
    items_e = xml.find("</Товары>")
    if items_s != -1 and items_e != -1:
        for row in extract_all_blocks(xml[items_s:items_e + 9], "Строка"):
            nom_s = row.find("<ДанныеНоменклатуры>")
            nom_e = row.find("</ДанныеНоменклатуры>") if nom_s != -1 else -1
            nom_name = nom_ref = ""
            if nom_s != -1 and nom_e != -1:
                nom_ref = extract_ref(row[nom_s:nom_e])
                nom_name = extract_tag(row[nom_s:nom_e], "Наименование") or ""

            unit_s = row.find("<ЕдиницаИзмерения>")
            unit_e = row.find("</ЕдиницаИзмерения>") if unit_s != -1 else -1
            unit_name = unit_ref = ""
            if unit_s != -1 and unit_e != -1:
                unit_ref = extract_ref(row[unit_s:unit_e])
                unit_name = extract_tag(row[unit_s:unit_e], "Наименование") or ""

            qty = 0.0
            try: qty = float(extract_tag(row, "Количество") or "0")
            except: pass
            price = 0.0
            try: price = float(extract_tag(row, "Цена") or "0")
            except: pass
            sum_val = 0.0
            try: sum_val = float(extract_tag(row, "Сумма") or "0")
            except: pass
            vat_rate = extract_tag(row, "СтавкаНДС") or ""
            vat_sum = 0.0
            try: vat_sum = float(extract_tag(row, "СуммаНДС") or "0")
            except: pass
            line_num = extract_tag(row, "НомерСтрокиДокумента") or ""

            items.append({
                "line": line_num,
                "nomenclature_ref": nom_ref,
                "nomenclature_name": nom_name,
                "unit_ref": unit_ref,
                "unit_name": unit_name,
                "quantity": qty,
                "price": price,
                "sum": sum_val,
                "vat_rate": vat_rate,
                "vat_sum": vat_sum,
            })

    return {
        "ref": ref, "number": number, "date": date, "posted": posted == "true",
        "organization_ref": org_ref, "organization_name": org_name,
        "client_ref": client_ref, "client_name": client_name,
        "client_full_name": client_full, "client_juridical": client_jl,
        "currency_ref": cur_ref, "currency_name": cur_name,
        "amount": amount, "comment": comment, "items": items,
    }

def validate_xml(xml):
    errors = []
    if "<?xml" not in xml[:100] and "<Message" not in xml[:500]:
        errors.append({"code": "INVALID_XML", "message": "Not a valid XML document"})
    if "<Message" not in xml:
        errors.append({"code": "INVALID_XML", "message": "Root element <Message> not found"})
    if "EnterpriseData/1.8" not in xml and "EnterpriseData/1.7" not in xml:
        errors.append({"code": "INVALID_XML", "message": "Not EnterpriseData format"})
    if "<Body" not in xml:
        errors.append({"code": "INVALID_XML", "message": "<Body> section not found"})
    return errors

# ─── Async Processing ───

def process_task(task_id, xml):
    t = tasks[task_id]
    t["status"] = "processing"
    t["started"] = datetime.now().isoformat()
    log.info(f"Task {task_id}: processing started")

    errors = validate_xml(xml)
    if errors:
        t["status"] = "completed_with_errors"
        t["errors"] = errors
        t["finished"] = datetime.now().isoformat()
        log.warning(f"Task {task_id}: validation failed: {errors}")
        return

    refs_ok = 0
    for tag in SPRAVOCHNIKI_ORDER:
        blocks = extract_all_blocks(xml, tag)
        for block in blocks:
            parsed = parse_spravochnik(block, tag)
            if parsed["ref"]:
                key = f"{tag}:{parsed['ref']}"
                action = "updated" if key in refs_db else "created"
                refs_db[key] = parsed
                refs_ok += 1
                log.info(f"Task {task_id}: ref {tag} {parsed['ref'][:12]}... {parsed['name']} - {action}")

    orders_ok = 0
    orders_err = 0
    order_errors = []
    for block in extract_all_blocks(xml, "Документ.ЗаказКлиента"):
        order = parse_order(block)
        if not order["number"]:
            orders_err += 1
            order_errors.append({"code": "INVALID_ORDER_DATA", "message": "No order number"})
            continue
        if order["number"] in orders_db:
            orders_err += 1
            order_errors.append({"code": "DUPLICATE_ORDER", "message": f"Order {order['number']} already exists"})
            log.warning(f"Task {task_id}: duplicate {order['number']}")
            continue
        order["task_id"] = task_id
        order["loaded_at"] = datetime.now().isoformat()
        orders_db[order["number"]] = order
        orders_ok += 1
        log.info(f"Task {task_id}: order {order['number']} loaded ({len(order['items'])} items)")

    t["refs_ok"] = refs_ok
    t["orders_ok"] = orders_ok
    t["orders_err"] = orders_err
    t["errors"] = order_errors
    t["status"] = "completed" if orders_err == 0 else "completed_with_errors"
    t["finished"] = datetime.now().isoformat()
    log.info(f"Task {task_id}: done. refs={refs_ok} orders_ok={orders_ok} orders_err={orders_err}")

# ─── Endpoints ───

@app.route("/")
def index():
    return jsonify({
        "service": "1C API Service",
        "version": "1.0.0",
        "format": "EnterpriseData 1.8",
        "port": PORT,
        "endpoints": {
            "POST /api/upload": "Upload EnterpriseData XML file",
            "GET /api/status/<task_id>": "Check task processing status",
            "GET /api/order/<number>": "Get order by number",
            "GET /api/orders": "List all loaded orders",
            "GET /api/refs": "List all loaded references",
            "GET /health": "Health check (no auth)"
        },
        "auth": "X-API-Key header or ?api_key=",
        "api_key": API_KEY,
        "schema": "D:\\DATA\\Схема_1_8_6.xsd",
        "example": "D:\\DATA\\Выгрузка_Заказы.xml"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "1C API", "version": "1.0.0"})

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "INVALID_XML", "message": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename.endswith(".xml"):
        return jsonify({"success": False, "error": "INVALID_XML", "message": "File must be .xml"}), 400
    raw = f.read()
    # Try UTF-8 first, fallback to cp1251
    try:
        xml = raw.decode("utf-8")
    except UnicodeDecodeError:
        xml = raw.decode("cp1251", errors="replace")
    task_id = str(uuid.uuid4())
    with open(os.path.join(UPLOAD_DIR, f"{task_id}.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    tasks[task_id] = {"status": "pending", "filename": f.filename, "refs_ok": 0, "orders_ok": 0, "orders_err": 0, "errors": [], "started": None, "finished": None}
    threading.Thread(target=process_task, args=(task_id, xml), daemon=True).start()
    log.info(f"Task {task_id}: file {f.filename} uploaded ({len(xml)} bytes)")
    return jsonify({"success": True, "task_id": task_id, "message": f"Task {task_id} created"}), 202

@app.route("/api/status/<task_id>")
def status(task_id):
    t = tasks.get(task_id)
    if not t:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": f"Task {task_id} not found"}), 404
    return jsonify({"success": True, "task_id": task_id, **t})

@app.route("/api/order/<number>")
def get_order(number):
    o = orders_db.get(number)
    if not o:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": f"Order {number} not found"}), 404
    return jsonify({"success": True, "order": o})

@app.route("/api/orders")
def list_orders():
    return jsonify({"success": True, "count": len(orders_db), "orders": list(orders_db.values())})

@app.route("/api/refs")
def list_refs():
    summary = {}
    for k, v in refs_db.items():
        tag = v.get("ref", "").split(":")[0] if ":" in k else k.split(":")[0]
        if tag not in summary:
            summary[tag] = []
        summary[tag].append({"ref": v["ref"], "name": v["name"]})
    return jsonify({"success": True, "count": len(refs_db), "refs": summary})

if __name__ == "__main__":
    print(f"1C API on http://localhost:{PORT} | Key: {API_KEY}")
    print(f"Schema: D:\\DATA\\Схема_1_8_6.xsd")
    print(f"Example: D:\\DATA\\Выгрузка_Заказы.xml")
    app.run(debug=True, port=PORT)
