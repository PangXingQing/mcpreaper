"""
MCPReaper Web UI 模块。

提供基于 FastAPI 的 Web 界面，集成 LLM 对话、音频素材库管理、
REAPER 工程助手和 MIDI 工具。
"""

from .server import app, start_ui, start_ui_thread, AppConfig, app_config

__all__ = [
    "app",
    "start_ui",
    "start_ui_thread",
    "AppConfig",
    "app_config",
]
