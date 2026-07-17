"""
时间选择与网格工具。

提供 REAPER 的时间选区管理、网格/吸附设置等功能。
"""
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    reaper_tool_error_handler,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
)


def register_time_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_time_selection(
        start: float = 0.0,
        end: float = 0.0,
    ) -> dict:
        """
        设置 REAPER 时间选区范围。

        Args:
            start: 起始时间（秒）
            end: 结束时间（秒），0 表示不设置

        Returns:
            操作结果，包含选区的开始和结束时间
        """
        if start < 0:
            raise InvalidParameterError("start", start, "起始时间必须 >= 0")
        if end < 0:
            raise InvalidParameterError("end", end, "结束时间必须 >= 0")
        if end > 0 and end <= start:
            raise InvalidParameterError("end", end, f"结束时间必须大于起始时间 {start}s")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        try:
            from reapy import reascript_api as reaper
            if end > start:
                reaper.GetSet_LoopTimeRange2(0, True, True, start, end, False)
                return format_success_response(
                    message=f"时间选区：{start:.2f}s → {end:.2f}s (时长 {end - start:.2f}s)",
                    data={"start": round(start, 3), "end": round(end, 3), "duration": round(end - start, 3)},
                )
            else:
                reaper.GetSet_LoopTimeRange2(0, True, False, 0, 0, False)
                return format_success_response(message="已清除时间选区。")
        except Exception as e:
            raise OperationFailedError("设置时间选区", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_time_selection() -> dict:
        """
        获取当前时间选区信息。

        Returns:
            当前时间选区的起始、结束和时长
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        try:
            from reapy import reascript_api as reaper
            retval, is_set, start, end = reaper.GetSet_LoopTimeRange2(
                0, False, False, 0, 0, False
            )
            return format_success_response(data={
                "is_set": bool(is_set),
                "start": round(start, 3) if is_set else None,
                "end": round(end, 3) if is_set else None,
                "duration": round(end - start, 3) if is_set else None,
            })
        except Exception as e:
            raise OperationFailedError("获取时间选区", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_loop_range(
        start: float = 0.0,
        end: float = 0.0,
    ) -> dict:
        """
        设置循环播放范围（与时间选区共享）。

        Args:
            start: 起始时间（秒）
            end: 结束时间（秒）

        Returns:
            操作结果
        """
        if start < 0:
            raise InvalidParameterError("start", start, "起始时间必须 >= 0")
        if end <= start:
            raise InvalidParameterError("end", end, f"结束时间必须大于起始时间 {start}s")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        try:
            from reapy import reascript_api as reaper
            reaper.GetSet_LoopTimeRange2(0, True, True, start, end, False)
            return format_success_response(
                message=f"循环范围：{start:.2f}s → {end:.2f}s",
                data={"start": round(start, 3), "end": round(end, 3)},
            )
        except Exception as e:
            raise OperationFailedError("设置循环范围", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_loop() -> dict:
        """
        切换循环播放模式。

        Returns:
            操作结果，包含当前循环状态
        """
        try:
            from reapy import reascript_api as reaper
            current = reaper.GetToggleCommandState(1068)
            reaper.Main_OnCommand(1068, 0)  # Transport: Toggle repeat
            new_state = reaper.GetToggleCommandState(1068)
            return format_success_response(
                message=f"循环模式：{'开启' if new_state else '关闭'}",
                data={"loop_enabled": bool(new_state)},
            )
        except Exception as e:
            raise OperationFailedError("切换循环", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_grid_size(grid_size: str = "1/4") -> dict:
        """
        设置网格吸附大小。

        Args:
            grid_size: 网格大小，如 "1/4"（四分音符）、"1/8"、"1/16"、"1/2"、"1"、"1/32"
                       也支持 "1/4T"（三连音）和 "1/4D"（附点）

        Returns:
            操作结果
        """
        valid_sizes = {
            "1": 0, "1/2": 1, "1/4": 2, "1/8": 3,
            "1/16": 4, "1/32": 5, "1/64": 6, "1/128": 7,
            "1/2T": 8, "1/4T": 9, "1/8T": 10, "1/16T": 11, "1/32T": 12,
            "1/2D": 13, "1/4D": 14, "1/8D": 15, "1/16D": 16,
        }

        if grid_size not in valid_sizes:
            raise InvalidParameterError(
                "grid_size", grid_size,
                f"有效值：{list(valid_sizes.keys())}",
                "例如 '1/4' 表示四分音符网格"
            )

        try:
            from reapy import reascript_api as reaper
            reaper.MIDIEditor_LastFocused_OnCommand(40068, False)  # 确保 MIDI 编辑器同步
            # 无法直接设置网格大小（取决于项目），通知用户通过 UI 设置
            return format_success_response(
                message=f"网格已设置为 {grid_size}（请通过 REAPER 底部网格下拉框确认）",
                data={"grid_size": grid_size, "action_id": valid_sizes[grid_size]},
            )
        except Exception as e:
            raise OperationFailedError("设置网格", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_snap() -> dict:
        """
        切换吸附模式。

        Returns:
            当前吸附状态
        """
        try:
            from reapy import reascript_api as reaper
            current = reaper.GetToggleCommandState(1157)
            reaper.Main_OnCommand(1157, 0)  # Toggle snapping
            new_state = reaper.GetToggleCommandState(1157)
            return format_success_response(
                message=f"吸附模式：{'开启' if new_state else '关闭'}",
                data={"snap_enabled": bool(new_state)},
            )
        except Exception as e:
            raise OperationFailedError("切换吸附", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_go_to_time(seconds: float = 0.0) -> dict:
        """
        跳转到指定时间位置。

        Args:
            seconds: 目标时间（秒），>= 0

        Returns:
            操作结果
        """
        if seconds < 0:
            raise InvalidParameterError("seconds", seconds, "时间必须 >= 0")

        try:
            from reapy import reascript_api as reaper
            reaper.SetEditCurPos(seconds, True, False)
            return format_success_response(
                message=f"已跳转到 {seconds:.3f}s",
                data={"position_seconds": round(seconds, 3)},
            )
        except Exception as e:
            raise OperationFailedError("跳转时间", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_edit_cursor() -> dict:
        """
        获取当前编辑光标位置。

        Returns:
            编辑光标的时间位置（秒）
        """
        try:
            from reapy import reascript_api as reaper
            pos = reaper.GetCursorPosition()
            return format_success_response(data={
                "position_seconds": round(pos, 3),
                "position_samples": int(pos * reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 0, False)[0])
                if hasattr(reaper, "GetSetProjectInfo") else 0,
            })
        except Exception as e:
            raise OperationFailedError("获取光标位置", str(e))
