import os
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    get_track_by_name,
    update_arrange,
    reaper_tool_error_handler,
    TrackNotFoundError,
    ReaperFileNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
    get_available_track_names
)

def register_item_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_audio_to_track(track_name: str = "", file_path: str = "", position: float = 0.0) -> dict:
        """
        在指定时间点导入音频到音轨。
        
        Args:
            track_name: 目标音轨名称
            file_path: 音频文件绝对路径
            position: 插入位置（秒，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not file_path:
            raise InvalidParameterError("file_path", file_path, "请提供有效的音频文件路径")
        
        if position < 0:
            raise InvalidParameterError("position", position, "有效值范围：>= 0")
        
        if not os.path.exists(file_path):
            raise ReaperFileNotFoundError(file_path)
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            track.make_only_selected_track()
            reaper.InsertMedia(file_path, 0)
            item = track.items[-1]
            item.position = position
            update_arrange()
            return format_success_response(
                message=f"成功将音频文件导入到音轨「{track_name}」的{position}秒处。"
            )
        except Exception as e:
            raise OperationFailedError("导入音频", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_items(track_name: str = "") -> dict:
        """
        获取指定音轨的所有项目项信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            项目项信息字典，包含success字段和items数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            items_info = []
            for item in track.items:
                for take in item.takes:
                    items_info.append({
                        "item_id": item.id,
                        "take_name": take.name,
                        "position": item.position,
                        "length": item.length,
                        "volume": take.volume,
                        "pan": take.pan,
                        "mute": take.mute
                    })
            return format_success_response(data={"items": items_info, "count": len(items_info)})
        except Exception as e:
            raise OperationFailedError("获取项目项信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_move_item(track_name: str = "", item_index: int = 0, new_position: float = 0.0) -> dict:
        """
        移动项目项到新位置。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            new_position: 新位置（秒，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if new_position < 0:
            raise InvalidParameterError("new_position", new_position, "有效值范围：>= 0")
        
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
            item = track.items[item_index]
            old_position = item.position
            item.position = new_position
            update_arrange()
            return format_success_response(
                message=f"成功将项目项从{old_position}秒移动到{new_position}秒处。"
            )
        except Exception as e:
            raise OperationFailedError("移动项目项", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_resize_item(track_name: str = "", item_index: int = 0, new_length: float = 0.0) -> dict:
        """
        调整项目项长度。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            new_length: 新长度（秒，> 0）
        
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
            item = track.items[item_index]
            old_length = item.length
            item.length = new_length
            update_arrange()
            return format_success_response(
                message=f"成功将项目项长度从{old_length}秒调整为{new_length}秒。"
            )
        except Exception as e:
            raise OperationFailedError("调整项目项长度", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_item(track_name: str = "", item_index: int = 0) -> dict:
        """
        删除项目项。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
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
            item = track.items[item_index]
            item.delete()
            update_arrange()
            return format_success_response(message=f"成功删除项目项（索引：{item_index}）。")
        except Exception as e:
            raise OperationFailedError("删除项目项", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_split_item(track_name: str = "", item_index: int = 0, split_position: float = 0.0) -> dict:
        """
        在指定位置分割项目项。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            split_position: 分割位置（秒，必须在项目项范围内）
        
        Returns:
            操作结果字典，包含success、message字段
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
            item_start = item.position
            item_end = item.position + item.length
            
            if split_position <= item_start or split_position >= item_end:
                raise InvalidParameterError(
                    "split_position", split_position,
                    f"分割位置应在项目项范围内({item_start}, {item_end})"
                )
            
            reaper.SplitMediaItem(item, split_position)
            update_arrange()
            return format_success_response(message=f"成功在{split_position}秒处分割项目项。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("分割项目项", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_item_volume(track_name: str = "", item_index: int = 0, volume: float = 1.0) -> dict:
        """
        设置项目项音量。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            volume: 音量值，范围[0, 4]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if volume < 0 or volume > 4:
            raise InvalidParameterError("volume", volume, "有效值范围：[0, 4]")
        
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
            item = track.items[item_index]
            if not item.takes:
                raise OperationFailedError("设置项目项音量", "该项目项没有take")
            
            item.takes[0].volume = volume
            update_arrange()
            return format_success_response(
                message=f"成功设置项目项（索引：{item_index}）的音量为{volume}。"
            )
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("设置项目项音量", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_item_pan(track_name: str = "", item_index: int = 0, pan: float = 0.0) -> dict:
        """
        设置项目项声相。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            pan: 声相值，范围[-1, 1]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if pan < -1 or pan > 1:
            raise InvalidParameterError("pan", pan, "有效值范围：[-1, 1]")
        
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
            item = track.items[item_index]
            if not item.takes:
                raise OperationFailedError("设置项目项声相", "该项目项没有take")
            
            item.takes[0].pan = pan
            update_arrange()
            pan_label = "左" if pan < -0.1 else ("右" if pan > 0.1 else "中")
            return format_success_response(
                message=f"成功设置项目项（索引：{item_index}）的声相为{pan}（{pan_label}）。"
            )
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("设置项目项声相", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_copy_item(track_name: str = "", item_index: int = 0, new_track_name: str = "", new_position: float = 0.0) -> dict:
        """
        复制项目项到指定位置。
        
        Args:
            track_name: 源音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            new_track_name: 目标音轨名称（可选，默认为源音轨）
            new_position: 新位置（秒，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的源音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if new_position < 0:
            raise InvalidParameterError("new_position", new_position, "有效值范围：>= 0")
        
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
            
            if new_track_name:
                new_track = get_track_by_name(new_track_name)
                if new_track is None:
                    available_tracks = get_available_track_names()
                    raise TrackNotFoundError(new_track_name, available_tracks)
            else:
                new_track = track
            
            item.select()
            reaper.Main_OnCommand(40698, 0)
            new_track.make_only_selected_track()
            reaper.SetEditCurPos(new_position, True, False)
            reaper.Main_OnCommand(40697, 0)
            
            update_arrange()
            target_info = f"音轨「{new_track_name}」的{new_position}秒处" if new_track_name else f"同一音轨的{new_position}秒处"
            return format_success_response(message=f"成功复制项目项到{target_info}。")
        except TrackNotFoundError:
            raise
        except Exception as e:
            raise OperationFailedError("复制项目项", str(e))