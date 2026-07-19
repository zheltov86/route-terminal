"""
1C API Service - EnterpriseData 1.8 XML upload, validation, async processing.
Port 5001, API key: route-terminal-1c-key-2026
"""
import os, json, uuid, logging, threading
from datetime import datetime
from flask import Flask, request, jsonify, Response

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
orders_db = {}
refs_db = {}

def check_auth():
    return (request.headers.get("X-API-Key") or request.args.get("api_key")) == API_KEY

@app.before_request
def auth_middleware():
    if request.endpoint and request.endpoint != "health" and not check_auth():
        return jsonify({"success": False, "error": "UNAUTHORIZED", "message": "Invalid or missing API key"}), 401

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
    xml_text = f.read().decode("utf-8")
    task_id = str(uuid.uuid4())
    with open(os.path.join(UPLOAD_DIR, f"{task_id}.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml_text)
    tasks[task_id] = {"status": "pending", "filename": f.filename, "orders_ok": 0, "orders_err": 0, "errors": [], "started": None, "finished": None}

    def process():
        t = tasks[task_id]
        t["status"] = "processing"
        t["started"] = datetime.now().isoformat()
        log.info(f"Task {task_id}: processing started")
        if "<Message" not in xml_text:
            t["status"] = "completed_with_errors"
            t["errors"] = [{"code": "INVALID_XML", "message": "Not valid EnterpriseData XML"}]
            t["finished"] = datetime.now().isoformat()
            return
        # Parse references
        for spr in ["Valuty", "EdinicyIzmereniya", "Organizacii", "Kontragenty", "StatiDohodov", "Polzovateli"]:
            idx = 0
            while True:
                s = xml_text.find(f"<{spr}>", idx)
                if s == -1: break
                e = xml_text.find(f"</{spr}>", s)
                if e == -1: break
                block = xml_text[s:e+len(spr)+3]
                ref_s = block.find("<ref>")
                ref_e = block.find("</ref>")
                if ref_s != -1 and ref_e != -1:
                    ref = block[ref_s+5:ref_e]
                    refs_db[f"{spr}:{ref}"] = {"type": spr, "raw": block[:300]}
                    log.info(f"Task {task_id}: ref {spr} {ref} processed")
                idx = e + 1
        # Parse orders
        idx = 0
        while True:
            s = xml_text.find("<order>", idx)
            if s == -1: break
            e = xml_text.find("</order>", s)
            if e == -1: break
            block = xml_text[s+7:e]
            num_s = block.find("<number>")
            num_e = block.find("</number>")
            if num_s != -1 and num_e != -1:
                num = block[num_s+8:num_e]
                if num in orders_db:
                    t["errors"].append({"code": "DUPLICATE_ORDER", "message": f"Order {num} already exists"})
                    t["orders_err"] += 1
                    log.warning(f"Task {task_id}: duplicate order {num}")
                else:
                    orders_db[num] = {"number": num, "raw": block[:500], "task_id": task_id, "loaded_at": datetime.now().isoformat()}
                    t["orders_ok"] += 1
                    log.info(f"Task {task_id}: order {num} loaded")
            idx = e + 1
        t["status"] = "completed" if t["orders_err"] == 0 else "completed_with_errors"
        t["finished"] = datetime.now().isoformat()
        log.info(f"Task {task_id}: done. OK={t['orders_ok']} ERR={t['orders_err']}")

    threading.Thread(target=process, daemon=True).start()
    log.info(f"Task {task_id}: file {f.filename} uploaded")
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
    return jsonify({"success": True, "count": len(refs_db), "refs": {k: {"type": v["type"]} for k, v in refs_db.items()}})

if __name__ == "__main__":
    print(f"1C API on http://localhost:{PORT} | Key: {API_KEY}")
    app.run(debug=True, port=PORT)
