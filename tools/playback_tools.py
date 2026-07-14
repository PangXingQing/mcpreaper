from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    reaper_tool_error_handler,
    InvalidParameterError,
    OperationFailedError,
    format_success_response
)

def register_playback_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_play() -> dict:
        """
        开始播放。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.play()
            return format_success_response(message="开始播放。")
        except Exception as e:
            raise OperationFailedError("播放", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_stop() -> dict:
        """
        停止播放。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.stop()
            return format_success_response(message="停止播放。")
        except Exception as e:
            raise OperationFailedError("停止播放", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_play() -> dict:
        """
        切换播放/暂停状态。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            if project.is_playing:
                project.pause()
                return format_success_response(message="暂停播放。")
            else:
                project.play()
                return format_success_response(message="开始播放。")
        except Exception as e:
            raise OperationFailedError("切换播放状态", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_pause() -> dict:
        """
        暂停播放。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.pause()
            return format_success_response(message="暂停播放。")
        except Exception as e:
            raise OperationFailedError("暂停播放", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_record() -> dict:
        """
        开始录音。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.record()
            return format_success_response(message="开始录音。")
        except Exception as e:
            raise OperationFailedError("录音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_go_to_start() -> dict:
        """
        将播放指针移动到项目开头。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.play_position = 0
            return format_success_response(message="播放指针已移动到项目开头。")
        except Exception as e:
            raise OperationFailedError("移动播放指针", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_go_to_end() -> dict:
        """
        将播放指针移动到项目末尾。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.play_position = project.length
            return format_success_response(message="播放指针已移动到项目末尾。")
        except Exception as e:
            raise OperationFailedError("移动播放指针", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_play_position(time: float = 0.0) -> dict:
        """
        设置播放指针位置。
        
        Args:
            time: 时间位置（秒，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if time < 0:
            raise InvalidParameterError("time", time, "有效值范围：>= 0")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            if time > project.length:
                raise InvalidParameterError(
                    "time", time,
                    f"不能超过项目长度({project.length}秒)"
                )
            
            project.play_position = time
            return format_success_response(message=f"播放指针已移动到{time}秒处。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("设置播放位置", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_play_position() -> dict:
        """
        获取当前播放位置和状态。
        
        Returns:
            播放状态字典，包含success字段和播放位置、状态数据
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            return format_success_response(data={
                "play_position": project.play_position,
                "is_playing": project.is_playing,
                "is_paused": project.is_paused,
                "is_recording": project.is_recording
            })
        except Exception as e:
            raise OperationFailedError("获取播放状态", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_loop_range(start_time: float = 0.0, end_time: float = 0.0) -> dict:
        """
        设置循环播放范围。
        
        Args:
            start_time: 循环开始时间（秒，>= 0）
            end_time: 循环结束时间（秒，> start_time）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if start_time < 0:
            raise InvalidParameterError("start_time", start_time, "有效值范围：>= 0")
        
        if end_time <= start_time:
            raise InvalidParameterError(
                "end_time", end_time,
                f"必须大于开始时间({start_time})，请提供更大的值"
            )
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetLoopTimeRange(start_time, end_time, False)
            return format_success_response(message=f"循环范围已设置为{start_time}秒到{end_time}秒。")
        except Exception as e:
            raise OperationFailedError("设置循环范围", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_loop() -> dict:
        """
        切换循环播放模式。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            retval, loop_start, loop_end = reaper.GetSet_LoopTimeRange(False, False, 0, 0, False)
            if loop_start == loop_end:
                raise OperationFailedError("切换循环模式", "请先设置循环范围")
            
            reaper.Main_OnCommand(40434, 0)
            return format_success_response(message="循环播放模式已切换。")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("切换循环模式", str(e))