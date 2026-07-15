import os
import socket
from typing import Optional, Any

_project_cache: Optional[Any] = None

REAPER_WEB_PORT = int(os.getenv("REAPER_WEB_PORT", "2307"))


def _get_local_ipv4_host() -> str:
    override_host = os.getenv("REAPER_WEB_HOST", "").strip()
    if override_host:
        return override_host

    try:
        import psutil

        for interfaces in psutil.net_if_addrs().values():
            for addr in interfaces:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address
    except Exception:
        pass

    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        if host_ip and not host_ip.startswith("127."):
            return host_ip
    except Exception:
        pass

    raise RuntimeError("无法解析本机IPv4地址，请设置 REAPER_WEB_HOST")


def _safe_project_info(project: Any) -> str:
    return f"当前Reaper项目名称为：{project.name}，路径为：{project.path}。"


def _connect_reaper_with_retries(reapy_module: Any) -> tuple[bool, str]:
    """Connect to the single supported Reaper Web Interface endpoint."""
    attempted: list[str] = []
    ports = [REAPER_WEB_PORT]
    hosts: list[Optional[str]] = [_get_local_ipv4_host()]

    config = getattr(reapy_module, "config", None)
    original_port = getattr(config, "WEB_INTERFACE_PORT", None) if config is not None else None

    for port in ports:
        if config is not None and original_port is not None:
            try:
                config.WEB_INTERFACE_PORT = port
            except Exception:
                pass

        for host in hosts:
            try:
                reapy_module.connect(host)
                return (True, f"reapy连接成功：host={host}, web_port={port}")
            except Exception as e:
                attempted.append(f"host={host},web_port={port},error={e}")
                try:
                    reapy_module.reconnect()
                except Exception:
                    pass

    if config is not None and original_port is not None:
        try:
            config.WEB_INTERFACE_PORT = original_port
        except Exception:
            pass

    detail = "；".join(attempted[-6:]) if attempted else "无可用连接尝试"
    return (False, detail)

def get_project() -> tuple[bool, str, Optional[Any]]:
    global _project_cache
    if _project_cache is not None:
        try:
            # Touching attributes forces detection of stale/disconnected cached objects.
            _ = _project_cache.name
            _ = _project_cache.path
            return (True, _safe_project_info(_project_cache), _project_cache)
        except Exception:
            _project_cache = None

    try:
        import reapy

        ok, detail = _connect_reaper_with_retries(reapy)
        if not ok:
            return (
                False,
                "无法打开REAPER工程，请检查REAPER是否打开，以及是否开启了reapy server。"
                f"\n连接尝试详情：{detail}",
                None,
            )

        _project_cache = reapy.Project()
        return (True, _safe_project_info(_project_cache), _project_cache)
    except Exception as e:
        return (False, f"无法打开REAPER工程，请检查REAPER是否打开，以及是否开启了reapy server。\n详细错误：{e}", None)

def get_track_by_name(track_name: str) -> Optional[Any]:
    success, message, project = get_project()
    if not success or project is None:
        return None
    try:
        for track in project.tracks:
            if track.name == track_name:
                return track
    except Exception:
        pass
    return None

def update_arrange() -> None:
    try:
        from reapy import reascript_api as reaper
        reaper.UpdateArrange()
    except Exception:
        pass

def ensure_project_ready() -> tuple[bool, str, Optional[Any]]:
    return get_project()