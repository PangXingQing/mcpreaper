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

def register_audio_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_record_on_track(track_name: str = "") -> dict:
        """
        在指定音轨上开始录音。
        
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
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40297, 0)
            reaper.SetTrackSelected(track, True)
            reaper.SetMediaTrackInfo_Value(track, "I_RECARM", 1)
            reaper.Main_OnCommand(1013, 0)
            return format_success_response(message=f"开始在音轨「{track_name}」上录音。")
        except Exception as e:
            raise OperationFailedError("开始录音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_stop_recording() -> dict:
        """
        停止录音。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(1014, 0)
            return format_success_response(message="已停止录音。")
        except Exception as e:
            raise OperationFailedError("停止录音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_normalize_audio_item(track_name: str = "", item_index: int = 0, target_db: float = 0.0) -> dict:
        """
        归一化音频项目项。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            target_db: 目标音量（dB），有效值范围：[-60, 0]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if target_db < -60 or target_db > 0:
            raise InvalidParameterError("target_db", target_db, "有效值范围：[-60, 0]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            item.select()
            reaper.Main_OnCommand(41131, 0)
            update_arrange()
            return format_success_response(message=f"成功归一化音频项目项到{target_db}dB。")
        except Exception as e:
            raise OperationFailedError("归一化音频", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_fade_audio_item(track_name: str = "", item_index: int = 0, fade_in_length: float = 0.0, fade_out_length: float = 0.0) -> dict:
        """
        设置音频项目项的淡入淡出。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            fade_in_length: 淡入时长（秒，>= 0）
            fade_out_length: 淡出时长（秒，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if fade_in_length < 0:
            raise InvalidParameterError("fade_in_length", fade_in_length, "有效值范围：>= 0")
        
        if fade_out_length < 0:
            raise InvalidParameterError("fade_out_length", fade_out_length, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            if fade_in_length > 0:
                reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", fade_in_length)
            if fade_out_length > 0:
                reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", fade_out_length)
            update_arrange()
            return format_success_response(message=f"成功设置淡入{fade_in_length}秒，淡出{fade_out_length}秒。")
        except Exception as e:
            raise OperationFailedError("设置淡入淡出", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_stretch_audio_item(track_name: str = "", item_index: int = 0, new_length: float = 0.0) -> dict:
        """
        拉伸音频项目项（改变时长，保持音高）。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            new_length: 新时长（秒，> 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if new_length <= 0:
            raise InvalidParameterError("new_length", new_length, "有效值范围：> 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            current_length = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
            stretch_factor = new_length / current_length
            reaper.SetMediaItemInfo_Value(item, "D_LENGTH", new_length)
            reaper.SetMediaItemInfo_Value(item, "D_STRETCH", stretch_factor)
            update_arrange()
            
            speed_percent = (1 / stretch_factor) * 100
            return format_success_response(
                message=f"成功拉伸音频项目项到{new_length}秒（原时长{current_length:.2f}秒，速度变化{speed_percent:.1f}%）。"
            )
        except Exception as e:
            raise OperationFailedError("拉伸音频", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_change_audio_pitch(track_name: str = "", item_index: int = 0, semitones: float = 0.0) -> dict:
        """
        改变音频项目项的音高。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            semitones: 音高变化（半音数，正数升高，负数降低），有效值范围：[-120, 120]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if semitones < -120 or semitones > 120:
            raise InvalidParameterError("semitones", semitones, "有效值范围：[-120, 120]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            reaper.SetMediaItemInfo_Value(item, "D_PITCH", semitones)
            update_arrange()
            
            direction = "升高" if semitones > 0 else ("降低" if semitones < 0 else "保持")
            return format_success_response(message=f"成功{direction}音频音高{abs(semitones)}个半音。")
        except Exception as e:
            raise OperationFailedError("改变音频音高", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_audio_item_info(track_name: str = "", item_index: int = 0) -> dict:
        """
        获取音频项目项的详细信息。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            音频项目项信息字典，包含success字段和详细信息
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("获取音频项目项信息", "该项目项没有take")
            
            take = item.takes[0]
            
            return format_success_response(data={
                "name": take.name,
                "length": reaper.GetMediaItemInfo_Value(item, "D_LENGTH"),
                "position": reaper.GetMediaItemInfo_Value(item, "D_POSITION"),
                "volume": reaper.GetMediaItemInfo_Value(item, "D_VOL"),
                "pan": reaper.GetMediaItemInfo_Value(item, "D_PAN"),
                "pitch": reaper.GetMediaItemInfo_Value(item, "D_PITCH"),
                "stretch": reaper.GetMediaItemInfo_Value(item, "D_STRETCH"),
                "fade_in_length": reaper.GetMediaItemInfo_Value(item, "D_FADEINLEN"),
                "fade_out_length": reaper.GetMediaItemInfo_Value(item, "D_FADEOUTLEN")
            })
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("获取音频项目项信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_remove_audio_silence(track_name: str = "", item_index: int = 0, threshold_db: float = -60.0) -> dict:
        """
        移除音频项目项中的静音部分。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            threshold_db: 静音阈值（dB），有效值范围：[-120, 0]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if threshold_db < -120 or threshold_db > 0:
            raise InvalidParameterError("threshold_db", threshold_db, "有效值范围：[-120, 0]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            item.select()
            reaper.Main_OnCommand(41305, 0)
            update_arrange()
            return format_success_response(message=f"成功移除音频静音部分（阈值：{threshold_db}dB）。")
        except Exception as e:
            raise OperationFailedError("移除音频静音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_audio_crossfade(track_name: str = "", item_index1: int = 0, item_index2: int = 1) -> dict:
        """
        在两个相邻音频项目项之间插入交叉淡化。
        
        Args:
            track_name: 音轨名称
            item_index1: 第一个项目项索引（>= 0）
            item_index2: 第二个项目项索引（>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index1 < 0:
            raise InvalidParameterError("item_index1", item_index1, "有效值范围：>= 0")
        
        if item_index2 < 0:
            raise InvalidParameterError("item_index2", item_index2, "有效值范围：>= 0")
        
        if item_index1 == item_index2:
            raise InvalidParameterError("item_index2", item_index2, "两个项目项索引不能相同")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index1 >= len(track.items):
            raise InvalidParameterError(
                "item_index1", item_index1,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        if item_index2 >= len(track.items):
            raise InvalidParameterError(
                "item_index2", item_index2,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item1 = track.items[item_index1]
            item2 = track.items[item_index2]
            reaper.SetMediaItemSelected(item1, True)
            reaper.SetMediaItemSelected(item2, True)
            reaper.Main_OnCommand(40038, 0)
            update_arrange()
            return format_success_response(message=f"成功在项目项{item_index1}和{item_index2}之间插入交叉淡化。")
        except Exception as e:
            raise OperationFailedError("插入交叉淡化", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_apply_audio_processing(track_name: str = "", item_index: int = 0, action_name: str = "") -> dict:
        """
        对音频项目项应用处理动作。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            action_name: 动作名称（如"Compressor", "Reverb", "EQ", "Noise Gate", "Delay", "Distortion"）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if not action_name:
            raise InvalidParameterError("action_name", action_name, "请提供有效的处理动作名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            item.select()
            
            action_map = {
                "Compressor": 41062,
                "Reverb": 41063,
                "EQ": 41064,
                "Noise Gate": 41065,
                "Delay": 41066,
                "Distortion": 41067
            }
            
            if action_name in action_map:
                reaper.Main_OnCommand(action_map[action_name], 0)
                update_arrange()
                return format_success_response(message=f"成功应用{action_name}处理。")
            else:
                raise InvalidParameterError(
                    "action_name", action_name,
                    f"不支持的处理动作。支持的动作：{list(action_map.keys())}"
                )
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("应用音频处理", str(e))