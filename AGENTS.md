# AGENTS.md - Llama.cpp Model Launcher

Flask web app for managing llama.cpp server instances with GGUF model selection and parameter configuration.

## Run

```bash
uv run model_launcher.py
# or
start.bat
```

Runs on `http://localhost:5000` (opens browser automatically).

## Structure

- `model_launcher.py` - Single-file Flask app (all routes and logic)
- `templates/index.html` - Frontend UI
- `config/` - User configs **(entirely gitignored)**
- `llamacpp/` - Binaries and models **(gitignored)**

## Two Config Types

| File | Purpose | Tracked? |
|------|---------|----------|
| `config/app-config.json` | Paths: `models_dir`, `llama_server` | No (gitignored) |
| `config/*.json` (everything else) | Model params: ctx_size, temp, port, etc. | No (gitignored) |
| `config/app-config.json.example` | Reference example for app-config | Yes |

## Cross-Platform Path Resolution

`_resolve_path()` in `model_launcher.py` handles paths uniformly:
- `%USERPROFILE%` → expanded on Windows (`os.path.expandvars`)
- `~` → expanded to home dir (`Path.expanduser`)
- Absolute paths → returned as-is
- Relative paths → resolved against `BASE_DIR` (project root)

**Default `models_dir`:** `%USERPROFILE%/.lmstudio/models` (Windows) or `~/.lmstudio/models` (Linux)

**Default `llama_server`:** stored without `.exe` in config (`"llamacpp/llama-server"`). `get_llama_server()` auto-appends `.exe` on Windows at runtime. On Linux it stays bare.

## Architecture Notes

- `threading.Lock()` guards subprocess start/stop to prevent race conditions
- Server logs to `server.log` in project root
- Process cleanup registered via `atexit` + `signal.SIGINT` handler
- `subprocess.CREATE_NO_WINDOW` used only on Windows (`os.name == "nt"`)
- No tests, no pyproject.toml (uv auto-manages Flask dependency)
- `.venv/` and `__pycache__/` are both gitignored

## Adding API Endpoints

Edit `model_launcher.py`, add `@app.route()` decorator, return `jsonify()` responses.

## Modifying llama-server Args

Edit command construction in `api_start()`. Both hyphen (`--ctx-size`) and underscore (`--chat-template-kwargs`) variants of optional params are accepted from config. Model path is constructed as `{resolved_models_dir}/{model_relative_path}`.
