"""
增强的错误处理系统。

提供分层级错误类型、带恢复建议的错误格式化、重试机制和工具装饰器。
"""
import traceback
import time
import logging
from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Union

logger = logging.getLogger("mcpreaper")

# ============================================================
# 基础错误类
# ============================================================

class ReaperError(Exception):
    """所有 REAPER 相关错误的基类。"""
    def __init__(self, error_type: str, message: str, detail: str = "", suggestion: str = ""):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.detail = detail
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, str]:
        return {
            "success": False,
            "error_type": self.error_type,
            "error": self.message,
            "detail": self.detail,
            "suggestion": self.suggestion,
        }


# ============================================================
# 连接错误
# ============================================================

class ReaperConnectionError(ReaperError):
    """REAPER 连接失败。"""
    def __init__(self, detail: str = "", host: str = "", port: int = 0):
        location = f" ({host}:{port})" if host else ""
        super().__init__(
            error_type="ReaperConnectionError",
            message=f"无法连接到 REAPER{location}",
            detail=detail or "reapy 无法与 REAPER 建立连接",
            suggestion=(
                "请依次检查：\n"
                "1. REAPER 是否已启动并打开了目标工程\n"
                "2. 是否已运行 Script: enable_reapy_server.lua\n"
                "3. REAPER 网络设置：Options → Preferences → Control/OSC/web → 允许外部控制\n"
                "4. 防火墙是否放行了 REAPER Web 端口"
            ),
        )


class ReaperTimeoutError(ReaperError):
    """REAPER 操作超时。"""
    def __init__(self, operation: str, timeout_seconds: float):
        super().__init__(
            error_type="ReaperTimeoutError",
            message=f"操作超时：{operation}",
            detail=f"操作在 {timeout_seconds:.1f} 秒内未完成",
            suggestion="REAPER 可能正在处理大量数据，请稍后重试或增大超时时间",
        )


# ============================================================
# 资源未找到错误
# ============================================================

class TrackNotFoundError(ReaperError):
    """轨道未找到。"""
    def __init__(self, track_name: str, available_tracks: list = None):
        track_list = ", ".join(available_tracks[:20]) if available_tracks else "无可用轨道"
        if available_tracks and len(available_tracks) > 20:
            track_list += f" ... 及其他 ({len(available_tracks)} 条总计)"
        super().__init__(
            error_type="TrackNotFoundError",
            message=f"未找到音轨「{track_name}」",
            detail=f"当前项目中不存在名为「{track_name}」的音轨",
            suggestion=f"可用音轨：{track_list}",
        )


class ItemNotFoundError(ReaperError):
    """媒体项未找到。"""
    def __init__(self, track_name: str, item_index: int, max_index: int):
        super().__init__(
            error_type="ItemNotFoundError",
            message=f"未找到媒体项",
            detail=f"音轨「{track_name}」中不存在索引为 {item_index} 的项目项",
            suggestion=f"有效索引范围：0 到 {max_index}（共 {max_index + 1} 个项）",
        )


class FXNotFoundError(ReaperError):
    """效果器未找到。"""
    def __init__(self, track_name: str, fx_name: str, is_index: bool = False):
        if is_index:
            super().__init__(
                error_type="FXNotFoundError",
                message=f"效果器索引 {fx_name} 无效",
                detail=f"音轨「{track_name}」上没有索引 {fx_name} 的效果器",
                suggestion=f"请使用 reaper_get_track_fx_list 查看效果器列表",
            )
        else:
            super().__init__(
                error_type="FXNotFoundError",
                message=f"未找到插件「{fx_name}」",
                detail=f"音轨「{track_name}」上未安装「{fx_name}」插件",
                suggestion=(
                    f"可使用 reaper_add_fx_to_track 添加插件。\n"
                    f"常用 Rea 系列插件：ReaEQ、ReaComp、ReaVerb、ReaDelay、ReaPitch"
                ),
            )


class MIDIItemNotFoundError(ReaperError):
    """MIDI 项未找到。"""
    def __init__(self, track_name: str):
        super().__init__(
            error_type="MIDIItemNotFoundError",
            message=f"未找到 MIDI 项",
            detail=f"音轨「{track_name}」上没有 MIDI 项目",
            suggestion="请先创建 MIDI 项：使用 reaper_create_midi_item 或在 REAPER 中插入 MIDI 事件",
        )


class MarkerNotFoundError(ReaperError):
    """标记未找到。"""
    def __init__(self, identifier: str, total_markers: int = 0):
        super().__init__(
            error_type="MarkerNotFoundError",
            message=f"未找到标记「{identifier}」",
            detail=f"无法在 {total_markers} 个标记中找到目标",
            suggestion="请使用 reaper_get_all_markers 查看所有标记列表",
        )


class SendNotFoundError(ReaperError):
    """发送未找到。"""
    def __init__(self, track_name: str, send_index: int = -1):
        idx_msg = f"索引 {send_index}" if send_index >= 0 else ""
        super().__init__(
            error_type="SendNotFoundError",
            message=f"未找到发送/接收",
            detail=f"音轨「{track_name}」上不存在发送 {idx_msg}".strip(),
            suggestion="请使用 reaper_get_track_sends 或 reaper_get_track_receives 查看当前路由",
        )


# ============================================================
# 参数/操作错误
# ============================================================

class InvalidParameterError(ReaperError):
    """参数验证失败。"""
    def __init__(self, param_name: str, param_value: Any, valid_range: str = "", example: str = ""):
        suggestion_parts = [f"有效值范围：{valid_range}"] if valid_range else []
        if example:
            suggestion_parts.append(f"示例：{example}")
        super().__init__(
            error_type="InvalidParameterError",
            message=f"参数「{param_name}」无效：{param_value}",
            detail=f"参数值 {repr(param_value)} 超出有效范围或格式不正确",
            suggestion="\n".join(suggestion_parts) if suggestion_parts else "请检查参数格式和范围",
        )


class ReaperFileNotFoundError(ReaperError):
    """文件未找到。"""
    def __init__(self, file_path: str, file_type: str = "文件"):
        import os
        parent = os.path.dirname(file_path)
        parent_exists = os.path.exists(parent) if parent else False
        tips = []
        if not os.path.isabs(file_path):
            tips.append("提示：请使用绝对路径而非相对路径")
        if parent and not parent_exists:
            tips.append(f"提示：父目录不存在：{parent}")
        tip_text = "\n".join(tips)
        suggestion = "请检查文件路径是否正确，或文件是否已被移动/删除"
        if tip_text:
            suggestion = tip_text + "\n" + suggestion
        super().__init__(
            error_type="ReaperFileNotFoundError",
            message=f"{file_type}不存在",
            detail=f"无法找到{file_type}：{file_path}",
            suggestion=suggestion,
        )


class OperationFailedError(ReaperError):
    """操作执行失败。"""
    def __init__(self, operation: str, detail: str = "", recovery: str = ""):
        super().__init__(
            error_type="OperationFailedError",
            message=f"{operation} 失败",
            detail=detail or f"执行 {operation} 时发生错误",
            suggestion=recovery or "请检查 REAPER 状态后重试，或尝试先保存工程",
        )


class RenderError(ReaperError):
    """渲染操作失败。"""
    def __init__(self, detail: str = ""):
        super().__init__(
            error_type="RenderError",
            message="渲染失败",
            detail=detail or "音频渲染过程中发生错误",
            suggestion=(
                "常见原因：\n"
                "1. 输出目录不存在或无写入权限\n"
                "2. 磁盘空间不足\n"
                "3. 渲染范围内没有任何音频/MIDI 数据\n"
                "4. 选中的轨道没有输出内容"
            ),
        )


class ProjectStateError(ReaperError):
    """工程状态无效。"""
    def __init__(self, reason: str = ""):
        super().__init__(
            error_type="ProjectStateError",
            message="工程状态异常",
            detail=reason or "当前工程状态不支持此操作",
            suggestion="请确保工程已保存且未处于异常状态。可尝试重新打开工程",
        )


# ============================================================
# 响应格式化
# ============================================================

def format_error_response(error: ReaperError) -> Dict[str, Any]:
    """将 ReaperError 格式化为标准 MCP 错误响应。"""
    return {
        "success": False,
        "error_type": error.error_type,
        "error": error.message,
        "detail": error.detail,
        "suggestion": error.suggestion,
    }


def format_success_response(data: Any = None, message: str = "", meta: Dict = None) -> Dict[str, Any]:
    """格式化为标准 MCP 成功响应。"""
    response: Dict[str, Any] = {"success": True}
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    if meta:
        response["meta"] = meta
    return response


def format_warning_response(data: Any = None, warning: str = "") -> Dict[str, Any]:
    """格式化为带警告的成功响应（操作成功但有注意事项）。"""
    response = {"success": True}
    if warning:
        response["warning"] = warning
    if data is not None:
        response["data"] = data
    return response


# ============================================================
# 重试机制
# ============================================================

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """重试装饰器，支持指数退避。"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, max_retries, e)
                        logger.warning(
                            f"重试 {attempt + 1}/{max_retries}: {func.__name__} 失败 - {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception  # type: ignore
        return wrapper
    return decorator


# ============================================================
# 工具装饰器
# ============================================================

def reaper_tool_error_handler(func):
    """MCP 工具的通用错误处理装饰器。

    捕获所有异常并转换为结构化的 MCP 错误响应。
    分层处理：ReaperError → 系统错误 → 未知异常。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ReaperError as e:
            logger.error(f"[ReaperError] {func.__name__}: {e.message}", exc_info=True)
            return format_error_response(e)
        except ModuleNotFoundError as e:
            if "reapy" in str(e).lower():
                return format_error_response(
                    ReaperConnectionError(
                        detail=f"reapy 模块未安装：{e}. 请运行 pip install python-reapy"
                    )
                )
            return format_error_response(
                OperationFailedError(operation="导入模块", detail=str(e))
            )
        except ImportError as e:
            if "reapy" in str(e).lower():
                return format_error_response(
                    ReaperConnectionError(detail=f"无法导入 reapy：{e}")
                )
            return format_error_response(
                OperationFailedError(operation="导入模块", detail=str(e))
            )
        except ConnectionError as e:
            return format_error_response(
                ReaperConnectionError(detail=f"网络连接错误：{e}")
            )
        except TimeoutError as e:
            return format_error_response(
                ReaperTimeoutError("MCP 工具操作", 30.0)
            )
        except NameError as e:
            return format_error_response(
                OperationFailedError(operation="变量引用", detail=f"变量未定义：{e}")
            )
        except TypeError as e:
            return format_error_response(
                InvalidParameterError(
                    param_name="参数类型",
                    param_value=str(e),
                    valid_range="请检查参数类型是否正确",
                    example="数字参数使用 int/float，字符串使用 str 类型",
                )
            )
        except ValueError as e:
            return format_error_response(
                InvalidParameterError(
                    param_name="参数值",
                    param_value=str(e),
                    valid_range="请检查参数值是否在有效范围内",
                )
            )
        except IndexError as e:
            return format_error_response(
                InvalidParameterError(
                    param_name="索引",
                    param_value="越界",
                    valid_range="请确认索引从 0 开始且不超出可用数量",
                )
            )
        except Exception as e:
            logger.error(f"[UnknownError] {func.__name__}: {e}", exc_info=True)
            return format_error_response(
                OperationFailedError(
                    operation=func.__name__,
                    detail=f"{type(e).__name__}: {e}",
                    recovery="如问题持续，请尝试重启 REAPER 和 MCP 服务器",
                )
            )
    return wrapper


def validate_parameter(
    name: str, value: Any, min_val: Any = None, max_val: Any = None,
    allowed: List[Any] = None, example: str = "",
):
    """通用参数验证辅助函数。

    Args:
        name: 参数名称
        value: 参数值
        min_val: 最小值（包含）
        max_val: 最大值（包含）
        allowed: 允许的值列表
        example: 使用示例

    Raises:
        InvalidParameterError: 验证失败时抛出
    """
    range_str = ""
    if min_val is not None and max_val is not None:
        range_str = f"[{min_val}, {max_val}]"
    elif min_val is not None:
        range_str = f">= {min_val}"
    elif max_val is not None:
        range_str = f"<= {max_val}"
    if allowed:
        range_str = f"允许值: {allowed}"

    if value is None:
        raise InvalidParameterError(name, "None", range_str, example)

    if allowed is not None and value not in allowed:
        raise InvalidParameterError(name, value, range_str, example)

    if min_val is not None and value < min_val:
        raise InvalidParameterError(name, value, range_str, example)

    if max_val is not None and value > max_val:
        raise InvalidParameterError(name, value, range_str, example)


# ============================================================
# 辅助函数
# ============================================================

def get_available_track_names() -> List[str]:
    """获取当前工程中所有轨道名称列表。"""
    try:
        from reapy import reascript_api as reaper
        track_names = []
        num_tracks = reaper.CountTracks(0)
        for i in range(num_tracks):
            track = reaper.GetTrack(0, i)
            retval, name = reaper.GetTrackName(track, "", 256)
            track_names.append(name)
        return track_names
    except Exception:
        return []


def get_friendly_error_message(error_type: str) -> Dict[str, str]:
    """根据错误类型返回友好的错误说明。

    用于在 MCP 工具的描述中展示常见错误及其解决方案。
    """
    error_messages = {
        "ReaperConnectionError": {
            "cause": "无法与 REAPER 建立连接",
            "fix": "检查 REAPER 是否运行、reapy server 是否开启",
        },
        "TrackNotFoundError": {
            "cause": "请求的轨道名在当前工程中不存在",
            "fix": "使用 reaper_get_all_track_names 查看可用轨道",
        },
        "ItemNotFoundError": {
            "cause": "请求的媒体项索引越界",
            "fix": "使用 reaper_get_track_items 查看有效索引",
        },
        "FXNotFoundError": {
            "cause": "请求的效果器未加载到指定轨道",
            "fix": "使用 reaper_get_track_fx_list 查看已加载效果器",
        },
        "InvalidParameterError": {
            "cause": "传入的参数值不符合要求",
            "fix": "检查参数范围和类型说明",
        },
        "OperationFailedError": {
            "cause": "操作执行失败（如 REAPER 内部状态问题）",
            "fix": "保存工程后重试，必要时重启 REAPER",
        },
        "RenderError": {
            "cause": "音频渲染过程失败",
            "fix": "检查输出路径权限、磁盘空间、渲染范围",
        },
        "ProjectStateError": {
            "cause": "工程文件状态异常",
            "fix": "保存工程，重新打开后重试",
        },
    }
    return error_messages.get(error_type, {
        "cause": "未知错误",
        "fix": "查看详细错误信息排查",
    })
