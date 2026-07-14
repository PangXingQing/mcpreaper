from typing import Optional, Any

_project_cache: Optional[Any] = None

def get_project() -> tuple[bool, str, Optional[Any]]:
    global _project_cache
    if _project_cache is None:
        try:
            import reapy
            _project_cache = reapy.Project()
            return (True, f"当前Reaper项目名称为：{_project_cache.name}，路径为：{_project_cache.path}。", _project_cache)
        except Exception as e:
            return (False, f"无法打开REAPER工程，请检查REAPER是否打开，以及是否开启了reapy server。\n详细错误：{e}", None)
    return (True, f"当前Reaper项目名称为：{_project_cache.name}，路径为：{_project_cache.path}。", _project_cache)

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