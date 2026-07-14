import traceback
from functools import wraps
from typing import Any, Dict, Optional, Union

class ReaperError(Exception):
    def __init__(self, error_type: str, message: str, detail: str = "", suggestion: str = ""):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.detail = detail
        self.suggestion = suggestion

class ReaperConnectionError(ReaperError):
    def __init__(self, detail: str = ""):
        super().__init__(
            error_type="ReaperConnectionError",
            message="无法连接到Reaper",
            detail=detail,
            suggestion="请确保Reaper已启动并运行，且已启用外部脚本控制（Options -> Preferences -> Control/OSC/web -> ReaScript）"
        )

class TrackNotFoundError(ReaperError):
    def __init__(self, track_name: str, available_tracks: list = None):
        super().__init__(
            error_type="TrackNotFoundError",
            message=f"未找到音轨「{track_name}」",
            detail=f"当前项目中不存在名为「{track_name}」的音轨",
            suggestion=f"可用音轨列表：{available_tracks or '请先创建音轨'}"
        )

class ItemNotFoundError(ReaperError):
    def __init__(self, track_name: str, item_index: int, max_index: int):
        super().__init__(
            error_type="ItemNotFoundError",
            message=f"未找到项目项",
            detail=f"音轨「{track_name}」中不存在索引为 {item_index} 的项目项",
            suggestion=f"有效索引范围：[0, {max_index}]"
        )

class FXNotFoundError(ReaperError):
    def __init__(self, track_name: str, fx_name: str):
        super().__init__(
            error_type="FXNotFoundError",
            message=f"未找到插件「{fx_name}」",
            detail=f"音轨「{track_name}」上未安装「{fx_name}」插件",
            suggestion=f"请先调用 reaper_add_{fx_name.lower()} 或 reaper_add_fx_to_track 添加插件"
        )

class InvalidParameterError(ReaperError):
    def __init__(self, param_name: str, param_value: Any, valid_range: str = ""):
        super().__init__(
            error_type="InvalidParameterError",
            message=f"参数「{param_name}」无效",
            detail=f"参数值 {param_value} 超出有效范围或格式不正确",
            suggestion=f"有效值范围：{valid_range}"
        )

class ReaperFileNotFoundError(ReaperError):
    def __init__(self, file_path: str):
        super().__init__(
            error_type="ReaperFileNotFoundError",
            message=f"文件不存在",
            detail=f"无法找到文件：{file_path}",
            suggestion="请检查文件路径是否正确，或文件是否已删除"
        )

class OperationFailedError(ReaperError):
    def __init__(self, operation: str, detail: str = ""):
        super().__init__(
            error_type="OperationFailedError",
            message=f"{operation} 失败",
            detail=detail,
            suggestion="请检查Reaper状态或重试操作"
        )

def format_error_response(error: ReaperError) -> Dict[str, str]:
    return {
        "success": False,
        "error_type": error.error_type,
        "error": error.message,
        "detail": error.detail,
        "suggestion": error.suggestion
    }

def format_success_response(data: Any = None, message: str = "") -> Dict[str, Any]:
    response = {"success": True}
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    return response

def reaper_tool_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ReaperError as e:
            return format_error_response(e)
        except ModuleNotFoundError as e:
            if 'reapy' in str(e):
                return format_error_response(
                    ReaperConnectionError(
                        detail=f"reapy模块未找到：{str(e)}"
                    )
                )
            return format_error_response(
                OperationFailedError(
                    operation="导入模块",
                    detail=str(e)
                )
            )
        except ImportError as e:
            if 'reapy' in str(e):
                return format_error_response(
                    ReaperConnectionError(
                        detail=f"无法导入reapy：{str(e)}"
                    )
                )
            return format_error_response(
                OperationFailedError(
                    operation="导入模块",
                    detail=str(e)
                )
            )
        except NameError as e:
            return format_error_response(
                OperationFailedError(
                    operation="变量引用",
                    detail=f"变量未定义：{str(e)}"
                )
            )
        except TypeError as e:
            return format_error_response(
                InvalidParameterError(
                    param_name="参数类型",
                    param_value=str(e),
                    valid_range="请检查参数类型是否正确"
                )
            )
        except ValueError as e:
            return format_error_response(
                InvalidParameterError(
                    param_name="参数值",
                    param_value=str(e),
                    valid_range="请检查参数值是否在有效范围内"
                )
            )
        except Exception as e:
            return format_error_response(
                OperationFailedError(
                    operation="操作",
                    detail=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                )
            )
    return wrapper

def get_available_track_names() -> list:
    try:
        from reapy import reascript_api as reaper
        track_names = []
        num_tracks = reaper.CountTracks(0)
        for i in range(num_tracks):
            track = reaper.GetTrack(0, i)
            retval, name = reaper.GetTrackName(track, "", 256)
            track_names.append(name)
        return track_names
    except:
        return []