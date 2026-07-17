"""
REAPER 客户端连接管理。

管理 reapy 连接、工程缓存、连接健康检查和自动重连。
"""
import os
import socket
import threading
import time
from typing import Optional, Any, Tuple, Dict

_project_cache: Optional[Any] = None
_connection_lock = threading.Lock()
_last_health_check: float = 0.0
_health_check_interval: float = 30.0  # 秒
_connection_attempts: int = 0

REAPER_WEB_PORT = int(os.getenv("REAPER_WEB_PORT", "2307"))


def _get_local_ipv4_host() -> str:
    """解析本机 IPv4 地址。

    优先级：环境变量 REAPER_WEB_HOST > 物理网卡 IP > socket.gethostbyname
    """
    override_host = os.getenv("REAPER_WEB_HOST", "").strip()
    if override_host:
        return override_host

    # 获取物理网卡 IP
    try:
        import psutil
        for interfaces in psutil.net_if_addrs().values():
            for addr in interfaces:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address
    except Exception:
        pass

    # 回退方案
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        if host_ip and not host_ip.startswith("127."):
            return host_ip
    except Exception:
        pass

    raise RuntimeError(
        "无法解析本机 IPv4 地址。请设置环境变量 REAPER_WEB_HOST=你的IP地址"
    )


def _safe_project_info(project: Any) -> str:
    """安全获取工程名称和路径。"""
    try:
        name = project.name or "未命名工程"
        path = project.path or "未保存"
        return f"当前 REAPER 工程：{name}（路径：{path}）"
    except Exception:
        return "REAPER 工程（无法获取详情）"


def _connect_reaper_with_retries(reapy_module: Any) -> Tuple[bool, str]:
    """带重试的 reapy 连接逻辑。

    尝试连接到已知的 REAPER Web Interface 端点。
    """
    global _connection_attempts
    attempted: list = []
    ports = [REAPER_WEB_PORT]

    try:
        host = _get_local_ipv4_host()
    except RuntimeError as e:
        return (False, str(e))

    hosts = [host]

    config = getattr(reapy_module, "config", None)
    original_port = getattr(config, "WEB_INTERFACE_PORT", None) if config is not None else None

    for port in ports:
        if config is not None and original_port is not None:
            try:
                config.WEB_INTERFACE_PORT = port
            except Exception:
                pass

        for h in hosts:
            try:
                reapy_module.connect(h)
                _connection_attempts = 0
                return (True, f"reapy 连接成功：host={h}, port={port}")
            except Exception as e:
                attempted.append(f"host={h}, port={port} → {e}")
                _connection_attempts += 1
                try:
                    reapy_module.reconnect()
                except Exception:
                    pass

    # 恢复原始端口配置
    if config is not None and original_port is not None:
        try:
            config.WEB_INTERFACE_PORT = original_port
        except Exception:
            pass

    detail = "；".join(attempted[-6:]) if attempted else "无可用连接"
    return (False, detail)


def health_check() -> Dict[str, Any]:
    """执行快速连接健康检查。

    Returns:
        {"healthy": bool, "latency_ms": float, ...}
    """
    global _project_cache, _last_health_check

    result = {
        "healthy": False,
        "latency_ms": 0,
        "project_name": "",
        "track_count": 0,
        "timestamp": time.time(),
    }

    try:
        start = time.perf_counter()
        if _project_cache is not None:
            _ = _project_cache.name
            from reapy import reascript_api as reaper
            result["project_name"] = _project_cache.name
            result["track_count"] = reaper.CountTracks(0)
            result["healthy"] = True
        else:
            import reapy
            ok, _ = _connect_reaper_with_retries(reapy)
            if ok:
                _project_cache = reapy.Project()
                result["project_name"] = _project_cache.name
                from reapy import reascript_api as reaper
                result["track_count"] = reaper.CountTracks(0)
                result["healthy"] = True
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        _last_health_check = time.time()
    except Exception as e:
        result["healthy"] = False
        result["error"] = str(e)

    return result


def get_project(force_refresh: bool = False) -> Tuple[bool, str, Optional[Any]]:
    """获取当前 REAPER 工程对象。

    使用缓存减少重复连接，支持强制刷新。

    Args:
        force_refresh: 是否强制刷新缓存

    Returns:
        (成功标志, 消息, Project对象或None)
    """
    global _project_cache

    with _connection_lock:
        if force_refresh:
            _project_cache = None

        if _project_cache is not None:
            try:
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
                    "无法连接 REAPER。请确认：\n"
                    "1. REAPER 已启动并打开工程\n"
                    "2. 已运行 Script: enable_reapy_server.lua\n"
                    f"3. 网络可达（{detail}）",
                    None,
                )

            _project_cache = reapy.Project()
            return (True, _safe_project_info(_project_cache), _project_cache)

        except Exception as e:
            return (
                False,
                f"连接 REAPER 时发生异常：{e}\n请检查 reapy 安装：pip install python-reapy",
                None,
            )


def get_track_by_name(track_name: str) -> Optional[Any]:
    """按名称查找轨道。

    Args:
        track_name: 轨道名称（精确匹配）

    Returns:
        轨道对象，未找到返回 None
    """
    success, _, project = get_project()
    if not success or project is None:
        return None
    try:
        for track in project.tracks:
            if track.name == track_name:
                return track
    except Exception:
        pass
    return None


def get_track_by_index(index: int) -> Optional[Any]:
    """按索引获取轨道（从 0 开始）。"""
    success, _, project = get_project()
    if not success or project is None:
        return None
    try:
        from reapy import reascript_api as reaper
        return reaper.GetTrack(0, index)
    except Exception:
        return None


def update_arrange() -> None:
    """刷新 REAPER 排列视图。"""
    try:
        from reapy import reascript_api as reaper
        reaper.UpdateArrange()
    except Exception:
        pass


def ensure_project_ready() -> Tuple[bool, str, Optional[Any]]:
    """确保 REAPER 工程就绪（get_project 别名）。"""
    return get_project()


def invalidate_cache() -> None:
    """手动使工程缓存失效（在 REAPER 外部变更后调用）。"""
    global _project_cache
    _project_cache = None


def get_connection_status() -> Dict[str, Any]:
    """获取详细的连接状态信息。"""
    status = {
        "connected": _project_cache is not None,
        "host": os.getenv("REAPER_WEB_HOST", "auto"),
        "port": REAPER_WEB_PORT,
        "cache_active": _project_cache is not None,
        "attempts_since_last_success": _connection_attempts,
        "last_health_check": _last_health_check,
    }
    if _project_cache is not None:
        try:
            status["project_name"] = _project_cache.name
        except Exception:
            status["project_name"] = "<disconnected>"
    return status
