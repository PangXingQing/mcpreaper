from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    get_track_by_name,
    update_arrange,
    reaper_tool_error_handler,
    TrackNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
    get_available_track_names
)

def register_track_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_track(track_name: str = "") -> dict:
        """
        在Reaper中创建新音轨。
        
        Args:
            track_name: 新音轨的名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track = project.add_track(0, track_name)
            track.make_only_selected_track()
            update_arrange()
            return format_success_response(message=f"成功创建音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("创建音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_select_track(track_name: str = "") -> dict:
        """
        选择指定音轨。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.make_only_selected_track()
            update_arrange()
            return format_success_response(message=f"成功选择音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("选择音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_all_tracks() -> dict:
        """
        获取所有音轨信息。
        
        Returns:
            音轨信息字典，包含success字段和tracks数据列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track_info = []
            for track in project.tracks:
                track_info.append({
                    "name": track.name,
                    "volume": track.get_info_value('D_VOL'),
                    "pan": track.get_info_value('D_PAN'),
                    "mute": bool(track.get_info_value('B_MUTE')),
                    "solo": bool(track.get_info_value('I_SOLO')),
                    "rec_arm": bool(track.get_info_value('I_RECARM')),
                    "num_items": len(track.items),
                    "num_fx": len(track.fxs)
                })
            return format_success_response(data={"tracks": track_info, "count": len(track_info)})
        except Exception as e:
            raise OperationFailedError("获取音轨信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_all_track_names() -> dict:
        """
        获取所有音轨名称。
        
        Returns:
            音轨名称列表字典，包含success字段和track_names数据
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track_names = [track.name for track in project.tracks]
            return format_success_response(data={"track_names": track_names, "count": len(track_names)})
        except Exception as e:
            raise OperationFailedError("获取音轨名称", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_track(track_name: str = "") -> dict:
        """
        删除指定音轨。
        
        Args:
            track_name: 要删除的音轨名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.delete()
            update_arrange()
            return format_success_response(message=f"成功删除音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("删除音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_rename_track(track_name: str = "", new_name: str = "") -> dict:
        """
        重命名音轨。
        
        Args:
            track_name: 当前音轨名称
            new_name: 新名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not new_name:
            raise InvalidParameterError("new_name", new_name, "请提供有效的新名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            old_name = track.name
            track.name = new_name
            update_arrange()
            return format_success_response(message=f"成功将音轨「{old_name}」重命名为「{new_name}」。")
        except Exception as e:
            raise OperationFailedError("重命名音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_volume(track_name: str = "", volume: float = 1.0) -> dict:
        """
        设置音轨音量（线性值）。
        
        Args:
            track_name: 音轨名称
            volume: 音量值，范围[0, 4]，其中0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if volume < 0 or volume > 4:
            raise InvalidParameterError("volume", volume, "有效值范围：[0, 4]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.set_info_value('D_VOL', volume)
            update_arrange()
            db_value = 20 * (volume ** (1/10)) if volume > 0 else "-inf"
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的音量为{volume}（约{db_value}dB）。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨音量", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_volume_db(track_name: str = "", volume_db: float = 0.0) -> dict:
        """
        设置音轨音量（分贝值）。
        
        Args:
            track_name: 音轨名称
            volume_db: 分贝值，范围[-100, +12]dB
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            if volume_db < -100:
                track.set_info_value('D_VOL', 0)
                display_val = "-inf"
            elif volume_db > 12:
                track.set_info_value('D_VOL', 4)
                display_val = "+12dB"
            else:
                track.set_info_value('D_VOL', 10 ** (volume_db / 20))
                display_val = f"{volume_db}dB"
            update_arrange()
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的音量为{display_val}。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨音量（分贝）", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_pan(track_name: str = "", pan: float = 0.0) -> dict:
        """
        设置音轨声相。
        
        Args:
            track_name: 音轨名称
            pan: 声相值，范围[-1, 1]，-1=左，0=中，1=右
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if pan < -1 or pan > 1:
            raise InvalidParameterError("pan", pan, "有效值范围：[-1, 1]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.set_info_value('D_PAN', pan)
            update_arrange()
            pan_label = "左" if pan < -0.1 else ("右" if pan > 0.1 else "中")
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的声相为{pan}（{pan_label}）。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨声相", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_mute(track_name: str = "", mute: bool = False) -> dict:
        """
        设置音轨静音状态。
        
        Args:
            track_name: 音轨名称
            mute: 是否静音
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            if mute:
                track.mute()
            else:
                track.unmute()
            update_arrange()
            status = "静音" if mute else "取消静音"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置音轨静音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_solo(track_name: str = "", solo: bool = False) -> dict:
        """
        设置音轨独奏状态。
        
        Args:
            track_name: 音轨名称
            solo: 是否独奏
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetMediaTrackInfo_Value(track, 'I_SOLO', int(solo))
            update_arrange()
            status = "独奏" if solo else "取消独奏"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置音轨独奏", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_rec_arm(track_name: str = "", rec_arm: bool = False) -> dict:
        """
        设置音轨录音准备状态。
        
        Args:
            track_name: 音轨名称
            rec_arm: 是否启用录音准备
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetMediaTrackInfo_Value(track, 'I_RECARM', int(rec_arm))
            update_arrange()
            status = "启用录音准备" if rec_arm else "禁用录音准备"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置录音准备", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_info(track_name: str = "") -> dict:
        """
        获取指定音轨的详细信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            音轨信息字典，包含success字段和音轨详细信息
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            return format_success_response(data={
                "name": track.name,
                "volume": track.get_info_value('D_VOL'),
                "pan": track.get_info_value('D_PAN'),
                "mute": bool(track.get_info_value('B_MUTE')),
                "solo": bool(track.get_info_value('I_SOLO')),
                "rec_arm": bool(track.get_info_value('I_RECARM')),
                "num_items": len(track.items),
                "num_fx": len(track.fxs)
            })
        except Exception as e:
            raise OperationFailedError("获取音轨详细信息", str(e))