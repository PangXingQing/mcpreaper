"""
MCPReaper Web UI - FastAPI 服务器。

提供 Web 界面用于：
- 与 LLM（OpenAI 兼容 API）对话
- 浏览和搜索音频素材库
- REAPER 工程助手
"""

import os
import json
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================
# 应用初始化
# ============================================================

app = FastAPI(
    title="MCPReaper Web UI",
    description="REAPER DAW 的 AI 对话与素材管理界面",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件路径
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 请求/响应模型
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    max_tokens: int = Field(2048, ge=1, le=32768, description="最大 token 数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度参数")


class ConfigRequest(BaseModel):
    api_key: str = Field("", description="OpenAI 兼容 API Key")
    api_base: str = Field("https://api.openai.com/v1", description="API 端点")
    model: str = Field("gpt-4o", description="模型名称")
    audio_library_path: Optional[str] = Field(None, description="音频素材库路径")


class AudioSearchRequest(BaseModel):
    query: str = Field("", description="搜索关键词")
    category: Optional[str] = Field(None, description="分类筛选")
    max_results: int = Field(50, ge=1, le=500)


class ProjectQueryRequest(BaseModel):
    query: str = Field(..., description="关于工程的问题")


# ============================================================
# 全局配置存储
# ============================================================

class AppConfig:
    """应用运行时配置。"""
    def __init__(self):
        self.api_key: str = ""
        self.api_base: str = "https://api.openai.com/v1"
        self.model: str = "gpt-4o"
        self.audio_library_path: str = ""

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_base": self.api_base,
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "audio_library_path": self.audio_library_path,
        }


app_config = AppConfig()

# 尝试从环境变量加载配置
app_config.api_key = os.getenv("OPENAI_API_KEY", "")
app_config.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
app_config.model = os.getenv("OPENAI_MODEL", "gpt-4o")
app_config.audio_library_path = os.getenv("AUDIO_LIBRARY_PATH", "")


# ============================================================
# 配置文件持久化
# ============================================================

CONFIG_FILE = Path(__file__).parent.parent / ".ui_config.json"


def _save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "api_base": app_config.api_base,
                "model": app_config.model,
                "audio_library_path": app_config.audio_library_path,
            }, f, indent=2)
    except Exception:
        pass


def _load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                app_config.api_base = data.get("api_base", app_config.api_base)
                app_config.model = data.get("model", app_config.model)
                app_config.audio_library_path = data.get("audio_library_path", app_config.audio_library_path)
    except Exception:
        pass


_load_config()


# ============================================================
# 配置 API
# ============================================================

@app.get("/api/config")
async def get_config():
    """获取当前配置（不返回 API Key 原文）。"""
    return app_config.to_dict()


@app.post("/api/config")
async def update_config(req: ConfigRequest):
    """更新配置。"""
    if req.api_key:
        app_config.api_key = req.api_key
    if req.api_base:
        app_config.api_base = req.api_base.rstrip("/")
    if req.model:
        app_config.model = req.model
    if req.audio_library_path is not None:
        app_config.audio_library_path = req.audio_library_path
    _save_config()
    return {"success": True, "config": app_config.to_dict()}


# ============================================================
# LLM 对话 API
# ============================================================

REAPER_SYSTEM_PROMPT = """你是一个专业的 REAPER DAW 音频工作站助手，名叫 MCPReaper Assistant。

你的专长领域：
1. REAPER 软件操作指南（轨道管理、MIDI编辑、混音、效果器、渲染等）
2. 音频制作知识（录音、混音、母带、MIDI编曲、音色设计）
3. 电影配乐和游戏音频设计
4. GM MIDI 音色选择和编曲建议
5. 音频工程理论和实践

你可以帮助用户：
- 解释 REAPER 的功能和操作方法
- 提供混音和编曲建议
- 推荐合适的 GM 音色和音色搭配
- 解答音频工程相关问题
- 通过 MCP 工具直接操作 REAPER 工程

请用专业但友好的语气回答。如果用户询问如何操作 REAPER，给出具体步骤。
如果涉及音频理论知识，简明扼要地解释。"""


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """发送消息到 LLM 并获取回复。"""
    if not app_config.is_configured():
        raise HTTPException(
            status_code=400,
            detail="请先在设置页面配置 API Key",
        )

    try:
        import httpx

        system_prompt = req.system_prompt or REAPER_SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message},
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{app_config.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {app_config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": app_config.model,
                    "messages": messages,
                    "max_tokens": req.max_tokens,
                    "temperature": req.temperature,
                },
            )

            if response.status_code != 200:
                error_detail = response.text[:500]
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM API 错误: {error_detail}",
                )

            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return {
                "success": True,
                "reply": reply,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            }

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="需要安装 httpx：pip install httpx",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


# ============================================================
# 音频素材库 API
# ============================================================

@app.get("/api/library")
async def list_audio_library(path: str = ""):
    """列出音频素材库内容。"""
    target = path or app_config.audio_library_path
    if not target or not os.path.isdir(target):
        return {"success": False, "error": "音频素材库路径未配置或无效", "files": []}

    try:
        from utils.audio_analysis import batch_analyze_directory, get_audio_library_stats
        stats = get_audio_library_stats(target)
        return {"success": True, **stats}
    except Exception as e:
        return {"success": False, "error": str(e), "files": []}


@app.post("/api/library/search")
async def search_audio_library(req: AudioSearchRequest):
    """搜索音频素材库。"""
    target = app_config.audio_library_path
    if not target or not os.path.isdir(target):
        return {"success": False, "error": "音频素材库路径未配置", "results": []}

    try:
        from utils.audio_analysis import batch_analyze_directory
        all_files = batch_analyze_directory(target)

        results = []
        query_lower = req.query.lower() if req.query else ""

        for f in all_files:
            filename = f.get("filename", "").lower()
            if not query_lower or query_lower in filename:
                # 对于 WAV 文件，获取更多信息
                if f.get("filepath", "").lower().endswith(".wav"):
                    from utils.audio_analysis import get_wav_info
                    detailed = get_wav_info(f["filepath"])
                    f.update({k: v for k, v in detailed.items() if k != "error"})
                results.append(f)
                if len(results) >= req.max_results:
                    break

        return {
            "success": True,
            "query": req.query,
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}


@app.get("/api/library/info/{filepath:path}")
async def get_audio_file_info(filepath: str):
    """获取单个音频文件的详细信息。"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    from utils.audio_analysis import get_wav_info, analyze_audio_levels
    info = get_wav_info(filepath)
    if "error" not in info:
        levels = analyze_audio_levels(filepath)
        info["levels"] = levels if "error" not in levels else None
    return {"success": True, "info": info}


# ============================================================
# 工程助手 API
# ============================================================

@app.post("/api/assistant/query")
async def project_query(req: ProjectQueryRequest):
    """处理工程相关的查询。

    可以查询工程结构、轨道状态、生成建议等。
    """
    try:
        from utils.project_reporter import generate_project_report
        report = generate_project_report()

        if not report["success"]:
            return {"success": False, "error": report.get("error", "无法生成工程报告")}

        # 构建针对问题的响应
        query_lower = req.query.lower()

        response_data = {
            "project_info": {
                "bpm": report.get("bpm"),
                "time_signature": report.get("time_signature"),
                "track_count": report.get("track_count"),
                "total_fx": report.get("total_fx"),
                "total_midi_notes": report.get("total_midi_notes"),
            },
        }

        if "轨道" in query_lower or "track" in query_lower:
            response_data["tracks"] = report.get("tracks_detail", [])
        if "fx" in query_lower or "效果" in query_lower:
            response_data["fx_summary"] = f"总计 {report.get('total_fx', 0)} 个效果器"
        if "midi" in query_lower.lower():
            response_data["midi_summary"] = f"总计 {report.get('total_midi_notes', 0)} 个 MIDI 音符"
        if "标记" in query_lower or "marker" in query_lower:
            response_data["markers"] = f"{report.get('total_markers', 0)} 个标记, {report.get('total_regions', 0)} 个区域"
        if "建议" in query_lower or "优化" in query_lower or "suggest" in query_lower.lower():
            response_data["suggestions"] = report.get("suggestions", [])
            response_data["warnings"] = report.get("warnings", [])

        # 如果配置了 LLM，生成智能响应
        if app_config.is_configured():
            try:
                import httpx

                context = json.dumps(response_data, ensure_ascii=False, indent=2)
                messages = [
                    {"role": "system", "content": f"你是 REAPER 工程助手。以下是当前工程数据：\n{context}\n请根据用户问题给出专业回答。"},
                    {"role": "user", "content": req.query},
                ]

                async with httpx.AsyncClient(timeout=30.0) as client:
                    llm_resp = await client.post(
                        f"{app_config.api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {app_config.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": app_config.model,
                            "messages": messages,
                            "max_tokens": 1024,
                            "temperature": 0.7,
                        },
                    )

                    if llm_resp.status_code == 200:
                        llm_data = llm_resp.json()
                        response_data["ai_response"] = llm_data["choices"][0]["message"]["content"]
            except Exception:
                response_data["ai_response"] = "(LLM 不可用，返回原始数据)"

        return {"success": True, "data": response_data}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/assistant/status")
async def assistant_status():
    """获取工程助手状态。"""
    try:
        from utils import health_check
        hc = health_check()
        return {
            "success": True,
            "reaper_connected": hc["healthy"],
            "llm_configured": app_config.is_configured(),
            "project_name": hc.get("project_name", ""),
            "track_count": hc.get("track_count", 0),
            "latency_ms": hc.get("latency_ms", 0),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# MIDI 工具 API
# ============================================================

@app.get("/api/midi/gm-instruments")
async def list_gm_instruments(category: str = ""):
    """列出 GM 音色库。"""
    from utils.midi_helpers import GM_INSTRUMENT_CATEGORIES, search_gm_instruments

    if category:
        results = search_gm_instruments(category)
        return {
            "success": True,
            "category": category,
            "instruments": [
                {"program": p, "name": n, "category": c}
                for p, n, c in results
            ],
        }

    instruments = {}
    for cat, items in GM_INSTRUMENT_CATEGORIES.items():
        instruments[cat] = [
            {"program": p, "name": n} for p, n in items
        ]

    return {"success": True, "instruments": instruments}


@app.get("/api/midi/scales")
async def list_scales():
    """列出可用音阶。"""
    from utils.midi_helpers import SCALE_INTERVALS
    return {
        "success": True,
        "scales": {
            name: len(intervals)
            for name, intervals in SCALE_INTERVALS.items()
        },
    }


@app.get("/api/midi/chords")
async def list_chords():
    """列出可用和弦类型。"""
    from utils.midi_helpers import CHORD_INTERVALS
    return {
        "success": True,
        "chord_types": {
            name: len(intervals)
            for name, intervals in CHORD_INTERVALS.items()
        },
    }


@app.get("/api/midi/convert")
async def convert_midi_note(note: str = ""):
    """音符名称与 MIDI 数字互转。"""
    from utils.midi_helpers import midi_note_to_name, name_to_midi_note

    try:
        # 如果是数字
        midi_num = int(note)
        name = midi_note_to_name(midi_num)
        return {"success": True, "midi_number": midi_num, "note_name": name}
    except ValueError:
        pass

    try:
        midi_num = name_to_midi_note(note)
        return {"success": True, "note_name": note.upper(), "midi_number": midi_num}
    except ValueError as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 健康检查
# ============================================================

@app.get("/api/health")
async def health_check_api():
    """API 健康检查。"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "reaper_available": _check_reaper(),
        "llm_configured": app_config.is_configured(),
    }


def _check_reaper() -> bool:
    try:
        from utils import health_check
        return health_check().get("healthy", False)
    except Exception:
        return False


# ============================================================
# 静态文件
# ============================================================

@app.get("/")
async def index():
    """主页面。"""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return HTMLResponse(_get_default_html())


def _get_default_html() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCPReaper Web UI</title>
    <style>
        :root {
            --bg: #1a1a2e;
            --panel: #16213e;
            --accent: #0f3460;
            --highlight: #e94560;
            --text: #eee;
            --text-dim: #999;
            --border: #2a2a4a;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg); color: var(--text);
            height: 100vh; display: flex;
        }
        .sidebar {
            width: 240px; background: var(--panel);
            padding: 16px; display: flex; flex-direction: column;
            border-right: 1px solid var(--border);
        }
        .sidebar h2 { color: var(--highlight); margin-bottom: 24px; font-size: 18px; }
        .sidebar nav a {
            display: block; color: var(--text-dim); text-decoration: none;
            padding: 10px 12px; border-radius: 6px; margin-bottom: 4px;
            transition: all .2s;
        }
        .sidebar nav a:hover, .sidebar nav a.active {
            background: var(--accent); color: var(--text);
        }
        .main { flex: 1; display: flex; flex-direction: column; }
        .header {
            padding: 16px 24px; background: var(--panel);
            border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .header .status { font-size: 13px; color: var(--text-dim); }
        .header .status .dot { display: inline-block; width: 8px; height: 8px;
            border-radius: 50%; margin-right: 6px; }
        .header .status .dot.ok { background: #4caf50; }
        .header .status .dot.err { background: #f44336; }
        .content { flex: 1; overflow-y: auto; padding: 24px; }
        .panel { display: none; }
        .panel.active { display: block; }

        .chat-container { display: flex; flex-direction: column; height: 100%; }
        .chat-messages {
            flex: 1; overflow-y: auto; padding: 16px;
            background: var(--panel); border-radius: 8px; margin-bottom: 16px;
        }
        .message { margin-bottom: 16px; }
        .message.user { text-align: right; }
        .message .bubble {
            display: inline-block; max-width: 80%; padding: 10px 16px;
            border-radius: 12px; font-size: 14px; line-height: 1.6;
        }
        .message.user .bubble { background: var(--accent); }
        .message.assistant .bubble { background: #2a2a4e; }
        .chat-input {
            display: flex; gap: 8px;
        }
        .chat-input input {
            flex: 1; padding: 12px 16px; border-radius: 8px;
            border: 1px solid var(--border); background: var(--panel);
            color: var(--text); font-size: 14px;
        }
        .chat-input button {
            padding: 12px 24px; border-radius: 8px; border: none;
            background: var(--highlight); color: white; cursor: pointer;
            font-size: 14px; font-weight: 600;
        }

        input, select, textarea {
            padding: 10px 12px; border-radius: 6px;
            border: 1px solid var(--border); background: var(--bg);
            color: var(--text); font-size: 14px; width: 100%;
        }
        label { display: block; margin-bottom: 6px; color: var(--text-dim); font-size: 13px; }
        .form-group { margin-bottom: 16px; }
        .btn {
            padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer;
            font-size: 14px; font-weight: 600; transition: all .2s;
        }
        .btn-primary { background: var(--highlight); color: white; }
        .btn-secondary { background: var(--accent); color: var(--text); }
        .file-list { list-style: none; }
        .file-list li {
            padding: 8px 12px; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between;
        }
        .file-list li:hover { background: var(--accent); }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px; margin-bottom: 24px;
        }
        .stat-card {
            background: var(--panel); padding: 16px; border-radius: 8px;
        }
        .stat-card .value { font-size: 28px; font-weight: 700; color: var(--highlight); }
        .stat-card .label { font-size: 13px; color: var(--text-dim); margin-top: 4px; }
        .track-row {
            display: flex; justify-content: space-between; padding: 8px 12px;
            border-bottom: 1px solid var(--border); align-items: center;
        }
    </style>
</head>
<body>
<div class="sidebar">
    <h2>MCPReaper</h2>
    <nav>
        <a href="#chat" class="active" onclick="showPanel('chat')">AI 对话</a>
        <a href="#library" onclick="showPanel('library')">素材库</a>
        <a href="#project" onclick="showPanel('project')">工程助手</a>
        <a href="#midi" onclick="showPanel('midi')">MIDI 工具</a>
        <a href="#settings" onclick="showPanel('settings')">设置</a>
    </nav>
    <div style="margin-top:auto; padding-top:16px; border-top:1px solid var(--border); font-size:12px; color:var(--text-dim)">
        v2.0.0 | MCPReaper
    </div>
</div>
<div class="main">
    <div class="header">
        <span id="pageTitle">AI 对话</span>
        <div class="status">
            <span class="dot" id="reaperDot"></span>
            <span id="reaperStatus">检查中...</span>
            &nbsp;|&nbsp;
            <span class="dot" id="llmDot"></span>
            <span id="llmStatus">未配置</span>
        </div>
    </div>
    <div class="content">
        <!-- Chat Panel -->
        <div id="panel-chat" class="panel active">
            <div class="chat-container" style="height: calc(100vh - 120px);">
                <div class="chat-messages" id="chatMessages">
                    <div class="message assistant">
                        <div class="bubble">你好！我是 MCPReaper Assistant，专业的 REAPER 音频工作站助手。我可以帮你解答 REAPER 操作、音频制作、MIDI 编曲等方面的问题。请先在上方设置中配置 API Key。</div>
                    </div>
                </div>
                <div class="chat-input">
                    <input type="text" id="chatInput" placeholder="输入你的问题..." onkeypress="if(event.key==='Enter')sendChat()">
                    <button onclick="sendChat()">发送</button>
                </div>
            </div>
        </div>
        <!-- Library Panel -->
        <div id="panel-library" class="panel">
            <h3>音频素材库</h3>
            <div style="margin-bottom:16px; display:flex; gap:8px;">
                <input type="text" id="libSearch" placeholder="搜索音频文件...">
                <button class="btn btn-primary" onclick="searchLibrary()">搜索</button>
                <button class="btn btn-secondary" onclick="loadLibrary()">刷新</button>
            </div>
            <div class="stats-grid" id="libStats"></div>
            <ul class="file-list" id="libFiles"></ul>
        </div>
        <!-- Project Panel -->
        <div id="panel-project" class="panel">
            <h3>工程助手</h3>
            <div class="stats-grid" id="projStats"></div>
            <div style="margin-bottom:16px;">
                <input type="text" id="projQuery" placeholder="询问工程相关问题...">
                <button class="btn btn-primary" onclick="queryProject()" style="margin-top:8px;">查询</button>
            </div>
            <div id="projResponse" style="background:var(--panel); padding:16px; border-radius:8px; white-space:pre-wrap;"></div>
        </div>
        <!-- MIDI Panel -->
        <div id="panel-midi" class="panel">
            <h3>MIDI 工具</h3>
            <div style="display:flex; gap:24px;">
                <div style="flex:1;">
                    <h4>音符转换</h4>
                    <input type="text" id="midiConvert" placeholder="输入音符名(如C4)或数字(如60)">
                    <button class="btn btn-primary" onclick="convertMidi()" style="margin-top:8px;">转换</button>
                    <div id="midiConvertResult" style="margin-top:12px;"></div>
                </div>
                <div style="flex:1;">
                    <h4>GM 音色搜索</h4>
                    <input type="text" id="gmSearch" placeholder="搜索音色(如Piano/Flute)">
                    <button class="btn btn-primary" onclick="searchGM()" style="margin-top:8px;">搜索</button>
                    <div id="gmResult" style="margin-top:12px; max-height:300px; overflow-y:auto;"></div>
                </div>
            </div>
        </div>
        <!-- Settings Panel -->
        <div id="panel-settings" class="panel">
            <h3>设置</h3>
            <div class="form-group">
                <label>API Key (OpenAI 兼容)</label>
                <input type="password" id="setApiKey" placeholder="sk-...">
            </div>
            <div class="form-group">
                <label>API Base URL</label>
                <input type="text" id="setApiBase" value="https://api.openai.com/v1">
            </div>
            <div class="form-group">
                <label>模型名称</label>
                <input type="text" id="setModel" value="gpt-4o">
            </div>
            <div class="form-group">
                <label>音频素材库路径</label>
                <input type="text" id="setLibPath" placeholder="C:/path/to/audio/library">
            </div>
            <button class="btn btn-primary" onclick="saveSettings()">保存设置</button>
            <div id="settingsResult" style="margin-top:12px;"></div>
        </div>
    </div>
</div>
<script>
    let currentPanel = 'chat';

    async function init() {
        await checkStatus();
        await loadConfig();
    }

    function showPanel(name) {
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        document.getElementById('panel-' + name).classList.add('active');
        document.querySelector(`nav a[href="#${name}"]`).classList.add('active');
        document.getElementById('pageTitle').textContent =
            {chat:'AI 对话', library:'素材库', project:'工程助手', midi:'MIDI 工具', settings:'设置'}[name];
        currentPanel = name;
        if (name === 'project') loadProjectStats();
        if (name === 'library') loadLibrary();
    }

    async function checkStatus() {
        try {
            const r = await fetch('/api/assistant/status');
            const d = await r.json();
            document.getElementById('reaperDot').className = 'dot ' + (d.reaper_connected ? 'ok' : 'err');
            document.getElementById('reaperStatus').textContent = d.reaper_connected ? 'REAPER 已连接' : 'REAPER 未连接';
            document.getElementById('llmDot').className = 'dot ' + (d.llm_configured ? 'ok' : 'err');
            document.getElementById('llmStatus').textContent = d.llm_configured ? 'LLM 已配置' : 'LLM 未配置';
        } catch(e) { console.error(e); }
    }

    async function loadConfig() {
        try {
            const r = await fetch('/api/config');
            const d = await r.json();
            document.getElementById('setApiBase').value = d.api_base || '';
            document.getElementById('setModel').value = d.model || '';
            document.getElementById('setLibPath').value = d.audio_library_path || '';
        } catch(e) { console.error(e); }
    }

    async function saveSettings() {
        const resp = await fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                api_key: document.getElementById('setApiKey').value,
                api_base: document.getElementById('setApiBase').value,
                model: document.getElementById('setModel').value,
                audio_library_path: document.getElementById('setLibPath').value,
            }),
        });
        const d = await resp.json();
        document.getElementById('settingsResult').textContent = d.success ? '设置已保存' : ('错误: ' + (d.detail || ''));
        await checkStatus();
    }

    async function sendChat() {
        const input = document.getElementById('chatInput');
        const msg = input.value.trim();
        if (!msg) return;
        addChatMessage('user', msg);
        input.value = '';
        try {
            const r = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg}),
            });
            const d = await r.json();
            if (d.success) addChatMessage('assistant', d.reply);
            else addChatMessage('assistant', '错误: ' + (d.detail || '未知错误'));
        } catch(e) {
            addChatMessage('assistant', '连接失败: ' + e.message);
        }
    }

    function addChatMessage(role, text) {
        const div = document.createElement('div');
        div.className = 'message ' + role;
        div.innerHTML = '<div class="bubble">' + text.replace(/\\n/g, '<br>') + '</div>';
        document.getElementById('chatMessages').appendChild(div);
        div.scrollIntoView({behavior: 'smooth'});
    }

    async function loadLibrary() {
        try {
            const r = await fetch('/api/library');
            const d = await r.json();
            if (d.success) {
                document.getElementById('libStats').innerHTML =
                    `<div class="stat-card"><div class="value">${d.total_files}</div><div class="label">文件</div></div>` +
                    `<div class="stat-card"><div class="value">${d.total_size_mb} MB</div><div class="label">总大小</div></div>` +
                    `<div class="stat-card"><div class="value">${d.total_duration_seconds}s</div><div class="label">总时长</div></div>`;
                let html = '';
                (d.files || []).forEach(f => {
                    html += `<li><span>${f.filename}</span><span>${(f.size_bytes/1024/1024||0).toFixed(1)}MB</span></li>`;
                });
                document.getElementById('libFiles').innerHTML = html;
            }
        } catch(e) { console.error(e); }
    }

    async function searchLibrary() {
        const q = document.getElementById('libSearch').value;
        try {
            const r = await fetch('/api/library/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: q}),
            });
            const d = await r.json();
            let html = '';
            (d.results || []).forEach(f => {
                html += `<li><span>${f.filename}</span><span>${f.sample_rate||''} ${f.num_channels||''}ch</span></li>`;
            });
            document.getElementById('libFiles').innerHTML = html || '<li>无结果</li>';
        } catch(e) { console.error(e); }
    }

    async function loadProjectStats() {
        try {
            const r = await fetch('/api/assistant/status');
            const d = await r.json();
            document.getElementById('projStats').innerHTML =
                `<div class="stat-card"><div class="value">${d.track_count || 0}</div><div class="label">轨道</div></div>` +
                `<div class="stat-card"><div class="value">${d.project_name || '-'}</div><div class="label">工程</div></div>` +
                `<div class="stat-card"><div class="value">${d.latency_ms || 0}ms</div><div class="label">延迟</div></div>`;
        } catch(e) { console.error(e); }
    }

    async function queryProject() {
        const q = document.getElementById('projQuery').value;
        try {
            const r = await fetch('/api/assistant/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: q}),
            });
            const d = await r.json();
            document.getElementById('projResponse').textContent = JSON.stringify(d, null, 2);
        } catch(e) { console.error(e); }
    }

    async function convertMidi() {
        const v = document.getElementById('midiConvert').value;
        try {
            const r = await fetch('/api/midi/convert?note=' + encodeURIComponent(v));
            const d = await r.json();
            document.getElementById('midiConvertResult').textContent = JSON.stringify(d, null, 2);
        } catch(e) { console.error(e); }
    }

    async function searchGM() {
        const q = document.getElementById('gmSearch').value;
        try {
            const r = await fetch('/api/midi/gm-instruments?category=' + encodeURIComponent(q));
            const d = await r.json();
            let html = '';
            (d.instruments || []).forEach(i => {
                html += `<div style="padding:4px 0;">[${i.program}] ${i.name} <span style="color:var(--text-dim)">${i.category}</span></div>`;
            });
            document.getElementById('gmResult').innerHTML = html || '无结果';
        } catch(e) { console.error(e); }
    }

    init();
    setInterval(checkStatus, 30000);
</script>
</body>
</html>"""


# ============================================================
# 启动函数
# ============================================================

def start_ui(host: str = "0.0.0.0", port: int = 8765):
    """启动 Web UI 服务器。

    Args:
        host: 绑定地址
        port: 端口号
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


def start_ui_thread(host: str = "0.0.0.0", port: int = 8765) -> threading.Thread:
    """在后台线程中启动 Web UI。

    Returns:
        运行中的线程对象
    """
    thread = threading.Thread(
        target=start_ui,
        args=(host, port),
        daemon=True,
        name="mcpreaper-ui",
    )
    thread.start()
    return thread


if __name__ == "__main__":
    start_ui()
