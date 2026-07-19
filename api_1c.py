from flask import Flask, request, jsonify, Response
import os, json, uuid, logging, threading
from datetime import datetime

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
        return jsonify({"success": False, "error": "UNAUTHORIZED"}), 401

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "1C API"})

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "INVALID_XML", "message": "No file"}), 400
    f = request.files["file"]
    if not f.filename.endswith(".xml"):
        return jsonify({"success": False, "error": "INVALID_XML", "message": "Must be .xml"}), 400
    xml_text = f.read().decode("utf-8")
    task_id = str(uuid.uuid4())
    with open(os.path.join(UPLOAD_DIR, f"{task_id}.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml_text)
    tasks[task_id] = {"status": "pending", "filename": f.filename, "orders_ok": 0, "orders_err": 0, "errors": [], "started": None, "finished": None}

    def process():
        t = tasks[task_id]
        t["status"] = "processing"
        t["started"] = datetime.now().isoformat()
        if "<Message" not in xml_text:
            t["status"] = "completed_with_errors"
            t["errors"] = [{"code": "INVALID_XML", "message": "Not valid XML"}]
            t["finished"] = datetime.now().isoformat()
            return
        # Parse references and orders
        parsed_refs = {}
        for spr in ["Valuty", "EdinicyIzmereniya", "Organizacii", "Kontragenty", "StatiDohodov", "Polzovateli"]:
            items = []
            idx = 0
            while True:
                s = xml_text.find(f"<{spr}>", idx)
                if s == -1: break
                e = xml_text.find(f"</{spr}>", s)
                if e == -1: break
                items.append(xml_text[s:e+len(spr)+3])
                idx = e + 1
            parsed_refs[spr] = items
            for item in items:
                ref_s = item.find("<ref>")
                ref_e = item.find("</ref>")
                if ref_s != -1 and ref_e != -1:
                    refs_db[f"{spr}:{item[ref_s+5:ref_e]}"] = {"type": spr}
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
                if num not in orders_db:
                    orders_db[num] = {"number": num, "raw": block[:500]}
                    t["orders_ok"] += 1
                else:
                    t["errors"].append({"code": "DUPLICATE_ORDER", "message": f"{num} exists"})
                    t["orders_err"] += 1
            idx = e + 1
        t["status"] = "completed" if t["orders_err"] == 0 else "completed_with_errors"
        t["finished"] = datetime.now().isoformat()

    threading.Thread(target=process, daemon=True).start()
    return jsonify({"success": True, "task_id": task_id, "message": f"Task {task_id} created"}), 202

@app.route("/api/status/<task_id>")
def status(task_id):
    t = tasks.get(task_id)
    if not t:
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404
    return jsonify({"success": True, "task_id": task_id, **t})

@app.route("/api/order/<number>")
def get_order(number):
    o = orders_db.get(number)
    if not o:
        return jsonify({"success": False, "error": "NOT_FOUND"}), 404
    return jsonify({"success": True, "order": o})

@app.route("/api/orders")
def list_orders():
    return jsonify({"success": True, "count": len(orders_db), "orders": list(orders_db.values())})

@app.route("/api/refs")
def list_refs():
    return jsonify({"success": True, "count": len(refs_db), "refs": list(refs_db.keys())})

@app.route("/")
def index():
    return Response("<h1>1C API Service</h1><p>Running on port 5001</p><p>API Key: " + API_KEY + "</p>", mimetype="text/html")

if __name__ == "__main__":
    print(f"1C API on http://localhost:{PORT} | Key: {API_KEY}")
    app.run(debug=True, port=PORT)
