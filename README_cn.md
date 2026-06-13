# LlamaShell - Llama.cpp 模型启动器

基于 Web 的 [llama.cpp](https://github.com/ggerganov/llama.cpp) 服务管理工具，支持 GGUF 模型选择与参数配置。

## 功能

- **模型浏览** — 自动扫描目录中的 `.gguf` 文件，显示大小，自动关联 mmproj
- **配置管理** — 保存/加载完整的服务器配置（参数、模型选择）
- **一键启动** — 通过 Web 界面启动/停止 llama-server
- **实时日志** — 查看服务器运行输出
- **跨平台** — 支持 Windows 和 Linux，自动解析路径

## 快速开始

### 前提

- [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- [llama.cpp](https://github.com/ggerganov/llama.cpp) 二进制文件置于 `llamacpp/`

### 运行

```bash
uv run model_launcher.py
# Windows 也可用: start.bat
```

自动打开 `http://localhost:5000`。

## 配置说明

### 应用配置 (`config/app-config.json`)

| 键 | 说明 | 默认值 |
|-----|------|--------|
| `models_dir` | 扫描 GGUF 模型的目录 | Linux: `~/.lmstudio/models`；Windows: `%USERPROFILE%/.lmstudio/models` |
| `llama_server` | llama-server 可执行文件路径（不带 `.exe` 后缀） | `llamacpp/llama-server` |

`llama_server` 在配置中不包含后缀 — Windows 下运行时会自动追加 `.exe`。

路径支持 `~`（Linux）和 `%VAR%`（Windows）变量展开，相对路径相对于项目根目录。

### 模型配置 (`config/*.json`)

每个配置文件存储 llama-server 参数：

| 参数 | 默认值 |
|------|--------|
| `ctx_size` | 131072 |
| `temp` | 0.6 |
| `top_p` | 0.95 |
| `top_k` | 20 |
| `min_p` | 0 |
| `host` | 0.0.0.0 |
| `port` | 8080 |

## 项目结构

```
├── model_launcher.py    # Flask 应用（全部路由和逻辑）
├── templates/
│   └── index.html       # 前端界面
├── config/              # 用户配置（gitignored）
│   └── app-config.json.example
├── llamacpp/            # 二进制文件和模型（gitignored）
└── start.bat            # Windows 启动脚本
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/models` | GET | 列出扫描到的 GGUF 模型 |
| `/api/configs` | GET | 列出已保存的配置 |
| `/api/configs` | POST | 保存配置 |
| `/api/app-config` | GET | 获取应用设置 |
| `/api/app-config` | POST | 更新应用设置 |
| `/api/status` | GET | 查看服务器运行状态 |
| `/api/start` | POST | 启动 llama-server |
| `/api/stop` | POST | 停止 llama-server |
| `/api/log` | GET | 获取服务器日志 |

## 许可

MIT
