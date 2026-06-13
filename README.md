# LlamaShell - Llama.cpp Model Launcher

[中文文档](README_cn.md)

A web-based management tool for [llama.cpp](https://github.com/ggerganov/llama.cpp) server instances with GGUF model selection and parameter configuration.

## Features

- **Model Browser** — auto-scans directories for `.gguf` files with size and mmproj detection
- **Config Management** — save/load complete server configurations (parameters, model choice)
- **One-Click Launch** — start/stop llama-server with a web UI
- **Live Logs** — view server output in real-time
- **Cross-Platform** — Windows and Linux support with automatic path resolution

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [llama.cpp](https://github.com/ggerganov/llama.cpp) binaries in `llamacpp/`

### Run

```bash
uv run model_launcher.py
# or on Windows: start.bat
```

Opens `http://localhost:5000` in your browser.

## Configuration

### App Config (`config/app-config.json`)

| Key | Description | Default |
|-----|-------------|---------|
| `models_dir` | Directory to scan for GGUF models | `~/.lmstudio/models` (Linux) or `%USERPROFILE%/.lmstudio/models` (Windows) |
| `llama_server` | Path to llama-server binary (no `.exe` suffix) | `llamacpp/llama-server` |

The `llama_server` value is stored without extension — `.exe` is auto-appended on Windows at runtime.

### Model Configs (`config/*.json`)

Each config file stores llama-server parameters:

| Parameter | Default |
|-----------|---------|
| `ctx_size` | 131072 |
| `temp` | 0.6 |
| `top_p` | 0.95 |
| `top_k` | 20 |
| `min_p` | 0 |
| `host` | 0.0.0.0 |
| `port` | 8080 |

## Project Structure

```
├── model_launcher.py    # Flask app (all routes and logic)
├── templates/
│   └── index.html       # Frontend UI
├── config/              # User configs (gitignored)
│   └── app-config.json.example
├── llamacpp/            # Binaries and models (gitignored)
└── start.bat            # Windows launcher
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | List scanned GGUF models |
| `/api/configs` | GET | List saved configurations |
| `/api/configs` | POST | Save a configuration |
| `/api/app-config` | GET | Get application settings |
| `/api/app-config` | POST | Update application settings |
| `/api/status` | GET | Check server running status |
| `/api/start` | POST | Start llama-server |
| `/api/stop` | POST | Stop llama-server |
| `/api/log` | GET | Get server log output |

## License

MIT
