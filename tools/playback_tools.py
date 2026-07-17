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
            from reapy import reascript_api as reaper
            reaper.SetEditCurPos(0, True, False)
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
            from reapy import reascript_api as reaper
            reaper.SetEditCurPos(project.length, True, False)
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
            
            from reapy import reascript_api as reaper
            reaper.SetEditCurPos(time, True, False)
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
            reaper.GetSet_LoopTimeRange(True, True, start_time, end_time, False)
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
            retval, proj, loop_start, loop_end, allowauto = reaper.GetSet_LoopTimeRange(False, False, 0, 0, False)
            if loop_start == loop_end:
                raise OperationFailedError("切换循环模式", "请先设置循环范围")

            reaper.Main_OnCommand(40434, 0)
            return format_success_response(message="循环播放模式已切换。")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("切换循环模式", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_stop_recording() -> dict:
        """
        停止录音（保留已录制的音频）。

        Returns:
            操作结果
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            project.stop()
            return format_success_response(message="录音已停止，已录制的音频已保留。")
        except Exception as e:
            raise OperationFailedError("停止录音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_go_to_marker(marker_name: str = "") -> dict:
        """
        跳转到指定名称的标记位置。

        Args:
            marker_name: 标记名称（精确匹配）

        Returns:
            操作结果，包含跳转后的时间位置
        """
        if not marker_name:
            raise InvalidParameterError("marker_name", marker_name, "请提供标记名称")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total = num_markers + num_regions

            for i in range(total):
                retval, is_rgn, pos, rgnend, name, mrk_idx = reaper.EnumProjectMarkers(project, i, False, 0, 0, '')
                if name == marker_name:
                    reaper.SetEditCurPos(pos, True, False)
                    return format_success_response(
                        message=f"已跳转到标记「{marker_name}」({pos:.3f}s)",
                        data={"position": round(pos, 3), "marker_name": marker_name},
                    )

            raise OperationFailedError("跳转标记", f"未找到名为「{marker_name}」的标记")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("跳转标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_scrub_forward(seconds: float = 1.0) -> dict:
        """
        快进指定秒数。

        Args:
            seconds: 快进秒数（> 0）

        Returns:
            操作结果
        """
        if seconds <= 0:
            raise InvalidParameterError("seconds", seconds, "必须 > 0")

        try:
            from reapy import reascript_api as reaper
            cur = reaper.GetCursorPosition()
            new_pos = cur + seconds
            reaper.SetEditCurPos(new_pos, True, False)
            return format_success_response(
                message=f"已快进 {seconds}s → {new_pos:.3f}s",
                data={"from_position": round(cur, 3), "to_position": round(new_pos, 3)},
            )
        except Exception as e:
            raise OperationFailedError("快进", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_rewind(seconds: float = 1.0) -> dict:
        """
        后退指定秒数。

        Args:
            seconds: 后退秒数（> 0）

        Returns:
            操作结果
        """
        if seconds <= 0:
            raise InvalidParameterError("seconds", seconds, "必须 > 0")

        try:
            from reapy import reascript_api as reaper
            cur = reaper.GetCursorPosition()
            new_pos = max(0, cur - seconds)
            reaper.SetEditCurPos(new_pos, True, False)
            return format_success_response(
                message=f"已后退 {seconds}s → {new_pos:.3f}s",
                data={"from_position": round(cur, 3), "to_position": round(new_pos, 3)},
            )
        except Exception as e:
            raise OperationFailedError("后退", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_transport_state() -> dict:
        """
        获取完整的传输状态信息。

        返回播放位置、是否播放/暂停/录音中、循环状态、
        时间选区等全部传输相关状态。

        Returns:
            传输状态字典
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper

            play_pos = reaper.GetPlayPosition()
            cur_pos = reaper.GetCursorPosition()
            play_state = reaper.GetPlayState()

            # play_state: 0=stopped, 1=playing, 2=paused, 4=recording
            state_map = {0: "stopped", 1: "playing", 2: "paused", 4: "recording"}

            # 获取循环状态
            retval, _, loop_start, loop_end, allow_auto = reaper.GetSet_LoopTimeRange2(
                0, False, False, 0, 0, False
            )

            loop_active = bool(reaper.GetToggleCommandState(1068))

            return format_success_response(data={
                "play_state": state_map.get(play_state, f"unknown({play_state})"),
                "play_position": round(play_pos, 3),
                "cursor_position": round(cur_pos, 3),
                "project_length": round(project.length, 3),
                "is_playing": project.is_playing,
                "is_paused": project.is_paused,
                "is_recording": project.is_recording,
                "loop_active": loop_active,
                "loop_start": round(loop_start, 3) if loop_end > loop_start else None,
                "loop_end": round(loop_end, 3) if loop_end > loop_start else None,
                "play_rate": reaper.Master_GetPlayRate(0)[0],
            })
        except Exception as e:
            raise OperationFailedError("获取传输状态", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_playback_rate(rate: float = 1.0) -> dict:
        """
        设置播放速率（变速播放，不影响音高）。

        Args:
            rate: 播放速率倍数，0.25 到 4.0（1.0 = 正常速度）

        Returns:
            操作结果
        """
        if rate < 0.25 or rate > 4.0:
            raise InvalidParameterError("rate", rate, "有效范围 [0.25, 4.0]")

        try:
            from reapy import reascript_api as reaper
            reaper.Master_SetPlayRate(0, rate)
            return format_success_response(
                message=f"播放速率已设为 {rate}x",
                data={"play_rate": rate},
            )
        except Exception as e:
            raise OperationFailedError("设置播放速率", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_track_solo_exclusive(track_name: str = "") -> dict:
        """
        独奏指定轨道（并取消其他轨道的独奏状态）。

        相当于"独占独奏"，只监听一条轨道。

        Args:
            track_name: 要独奏的轨道名称

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供轨道名称")

        from utils import get_track_by_name, TrackNotFoundError, get_available_track_names
        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper

            # 取消所有轨道的独奏
            num_tracks = reaper.CountTracks(0)
            for i in range(num_tracks):
                t = reaper.GetTrack(0, i)
                reaper.SetMediaTrackInfo_Value(t, "I_SOLO", 0)

            # 独奏目标轨道
            reaper.SetMediaTrackInfo_Value(track, "I_SOLO", 1)
            reaper.UpdateArrange()

            return format_success_response(
                message=f"已独占独奏音轨「{track_name}」（其他轨道已取消独奏）",
            )
        except Exception as e:
            raise OperationFailedError("独占独奏", str(e))