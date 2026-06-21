import os
import json
import subprocess
import threading
import glob
import atexit
import signal
import webbrowser
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
APP_CONFIG_FILE = CONFIG_DIR / "app-config.json"

process = None
process_lock = threading.Lock()
log_file = None


def load_app_config():
    if APP_CONFIG_FILE.exists():
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "models_dir": "%USERPROFILE%/.lmstudio/models" if os.name == "nt" else "~/.lmstudio/models",
        "llama_server": "llamacpp/llama-server",
    }


def _resolve_path(path_str):
    resolved = Path(os.path.expandvars(path_str)).expanduser()
    if resolved.is_absolute():
        return resolved
    return BASE_DIR / resolved


def save_app_config(config):
    with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_models_dir():
    cfg = load_app_config()
    default_dir = "%USERPROFILE%/.lmstudio/models" if os.name == "nt" else "~/.lmstudio/models"
    return _resolve_path(cfg.get("models_dir", default_dir))


def get_llama_server():
    cfg = load_app_config()
    server_path = cfg.get("llama_server", "llamacpp/llama-server")
    if os.name == "nt" and not server_path.endswith(".exe"):
        server_path += ".exe"
    return _resolve_path(server_path)


def scan_models():
    MODELS_DIR = get_models_dir()
    all_gguf = []

    for gguf in MODELS_DIR.rglob("*.gguf"):
        rel_path = gguf.relative_to(MODELS_DIR)
        parent_dir = rel_path.parent

        stem_lower = gguf.stem.lower()
        is_mmproj = "mmproj" in stem_lower
        is_mtp_draft = stem_lower.startswith("mtp-")

        all_gguf.append(
            {
                "name": gguf.stem,
                "path": str(rel_path).replace("\\", "/"),
                "dir": str(parent_dir).replace("\\", "/"),
                "is_mmproj": is_mmproj,
                "is_mtp_draft": is_mtp_draft,
                "size_mb": gguf.stat().st_size // (1024 * 1024),
            }
        )

    models = []
    mmprojs = []
    mtp_drafts = []

    for g in all_gguf:
        if g["is_mmproj"]:
            mmprojs.append(g)
        elif g["is_mtp_draft"]:
            mtp_drafts.append(g)
        else:
            g["mmproj"] = None
            g["mmproj_name"] = None
            g["model_draft"] = None
            g["model_draft_name"] = None
            models.append(g)

    for m in mmprojs:
        for g in models:
            if g["dir"] == m["dir"]:
                g["mmproj"] = m["path"]
                g["mmproj_name"] = m["name"]
                break

    for d in mtp_drafts:
        for g in models:
            if g["dir"] == d["dir"]:
                g["model_draft"] = d["path"]
                g["model_draft_name"] = d["name"]
                break

    return models


def load_configs():
    configs = []
    CONFIG_DIR.mkdir(exist_ok=True)

    for cfg in CONFIG_DIR.glob("*.json"):
        if cfg.stem.startswith("app-config"):
            continue
        with open(cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
            configs.append({"name": cfg.stem, "path": cfg.name, "config": data})

    if not configs:
        default_cfg = {
            "name": "默认配置",
            "ctx_size": 131072,
            "temp": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0,
            "chat_template_kwargs": None,
            "port": 8080,
            "host": "0.0.0.0",
        }
        configs.append(
            {"name": "default", "path": "default.json", "config": default_cfg}
        )

    return configs


def save_config(name, config):
    CONFIG_DIR.mkdir(exist_ok=True)
    cfg_path = CONFIG_DIR / f"{name}.json"
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/models")
def api_models():
    return jsonify(scan_models())


@app.route("/api/configs")
def api_configs():
    return jsonify(load_configs())


@app.route("/api/configs", methods=["POST"])
def api_save_config():
    data = request.json
    name = data.get("name", "default")
    config = data.get("config", {})
    save_config(name, config)
    return jsonify({"success": True})


@app.route("/api/app-config")
def api_app_config():
    return jsonify(load_app_config())


@app.route("/api/app-config", methods=["POST"])
def api_save_app_config():
    data = request.json
    cfg = load_app_config()
    cfg.update(data)
    save_app_config(cfg)
    return jsonify({"success": True})


@app.route("/api/status")
def api_status():
    with process_lock:
        if process and process.poll() is None:
            return jsonify({"running": True, "pid": process.pid})
    return jsonify({"running": False})


@app.route("/api/start", methods=["POST"])
def api_start():
    global process

    with process_lock:
        if process and process.poll() is None:
            return jsonify({"error": "Server is already running"}), 400

        data = request.json
        model_path = data.get("model")
        mmproj_path = data.get("mmproj")
        config = data.get("config", {})

        if not model_path:
            return jsonify({"error": "No model selected"}), 400

        app_cfg = load_app_config()
        default_dir = "%USERPROFILE%/.lmstudio/models" if os.name == "nt" else "~/.lmstudio/models"
        models_dir = str(_resolve_path(app_cfg.get("models_dir", default_dir)))

        cmd = [
            str(get_llama_server()),
            "--model",
            str(Path(models_dir) / model_path),
            "--host",
            config.get("host", "0.0.0.0"),
            "--port",
            str(config.get("port", 8080)),
            "--ctx-size",
            str(config.get("ctx_size", 131072)),
            "--temp",
            str(config.get("temp", 0.6)),
            "--top-p",
            str(config.get("top_p", 0.95)),
            "--top-k",
            str(config.get("top_k", 20)),
            "--min-p",
            str(config.get("min_p", 0)),
        ]

        presence_penalty = config.get("presence_penalty") or config.get("presence-penalty")
        if presence_penalty:
            cmd.extend(["--presence-penalty", str(presence_penalty)])

        spec_type = config.get("spec_type") or config.get("spec-type")
        if spec_type:
            cmd.extend(["--spec-type", spec_type])

        spec_draft_n_max = config.get("spec_draft_n_max") or config.get("spec-draft-n-max")
        if spec_draft_n_max:
            cmd.extend(["--spec-draft-n-max", str(spec_draft_n_max)])

        chat_template_kwargs = config.get("chat_template_kwargs")
        if chat_template_kwargs:
            cmd.extend(["--chat-template-kwargs", chat_template_kwargs])

        model_draft = data.get("model_draft")
        if model_draft:
            cmd.extend(["--model-draft", str(Path(models_dir) / model_draft)])

        if data.get("mcp_proxy", True):
            cmd.append("--webui-mcp-proxy")

        if mmproj_path:
            cmd.extend(["--mmproj", str(Path(models_dir) / mmproj_path)])

        global log_file
        log_file = open(BASE_DIR / "server.log", "w", encoding="utf-8")

        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        return jsonify({"success": True, "pid": process.pid})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global process, log_file

    with process_lock:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if log_file:
            log_file.close()
            log_file = None
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No process running"})


@app.route("/api/log")
def api_log():
    log_file = BASE_DIR / "server.log"
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            return jsonify({"log": content[-5000:]})
    return jsonify({"log": ""})


def cleanup_process():
    global process, log_file
    with process_lock:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    if log_file:
        log_file.close()
        log_file = None


atexit.register(cleanup_process)


def signal_handler(sig, frame):
    cleanup_process()
    exit(0)


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        webbrowser.open("http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
