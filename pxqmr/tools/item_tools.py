import os
from mcp.server.fastmcp import FastMCP
from utils.reaper_client import get_track_by_name, update_arrange

def register_item_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_insert_audio_to_track(track_name: str = "", file_path: str = "", position: float = 0.0) -> str:
        """
        在指定时间点导入音频到音轨。
        
        Args:
            track_name: 目标音轨名称
            file_path: 音频文件绝对路径
            position: 插入位置（秒）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if not os.path.exists(file_path):
            return f"音频文件不存在：{file_path}"
        try:
            from reapy import reascript_api as reaper
            track.make_only_selected_track()
            reaper.InsertMedia(file_path, 0)
            item = track.items[-1]
            item.position = position
            update_arrange()
            return f"成功将音频文件导入到音轨「{track_name}」的{position}秒处。"
        except Exception as e:
            return f"导入音频失败：{e}"

    @mcp.tool()
    def reaper_get_track_items(track_name: str = "") -> list[dict]:
        """
        获取指定音轨的所有项目项信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            项目项信息列表
        """
        track = get_track_by_name(track_name)
        if track is None:
            return [{"error": f"没有找到音轨「{track_name}」。"}]
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
            return items_info
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_move_item(track_name: str = "", item_index: int = 0, new_position: float = 0.0) -> str:
        """
        移动项目项到新位置。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            new_position: 新位置（秒）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        try:
            item = track.items[item_index]
            item.position = new_position
            update_arrange()
            return f"成功将项目项移动到{new_position}秒处。"
        except Exception as e:
            return f"移动项目项失败：{e}"

    @mcp.tool()
    def reaper_resize_item(track_name: str = "", item_index: int = 0, new_length: float = 0.0) -> str:
        """
        调整项目项长度。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            new_length: 新长度（秒）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        if new_length <= 0:
            return f"长度参数无效：{new_length}，必须大于0。"
        try:
            item = track.items[item_index]
            item.length = new_length
            update_arrange()
            return f"成功将项目项长度调整为{new_length}秒。"
        except Exception as e:
            return f"调整项目项长度失败：{e}"

    @mcp.tool()
    def reaper_delete_item(track_name: str = "", item_index: int = 0) -> str:
        """
        删除项目项。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        try:
            item = track.items[item_index]
            item.delete()
            update_arrange()
            return f"成功删除项目项。"
        except Exception as e:
            return f"删除项目项失败：{e}"

    @mcp.tool()
    def reaper_split_item(track_name: str = "", item_index: int = 0, split_position: float = 0.0) -> str:
        """
        在指定位置分割项目项。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            split_position: 分割位置（秒）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            if split_position <= item.position or split_position >= item.position + item.length:
                return f"分割位置无效：{split_position}，应在项目项范围内。"
            reaper.SplitMediaItem(item, split_position)
            update_arrange()
            return f"成功在{split_position}秒处分割项目项。"
        except Exception as e:
            return f"分割项目项失败：{e}"

    @mcp.tool()
    def reaper_set_item_volume(track_name: str = "", item_index: int = 0, volume: float = 1.0) -> str:
        """
        设置项目项音量。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            volume: 音量值，范围[0, 4]
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        if volume < 0 or volume > 4:
            return f"音量参数无效：{volume}，范围应为[0, 4]。"
        try:
            item = track.items[item_index]
            item.takes[0].volume = volume
            update_arrange()
            return f"成功设置项目项音量为{volume}。"
        except Exception as e:
            return f"设置项目项音量失败：{e}"

    @mcp.tool()
    def reaper_set_item_pan(track_name: str = "", item_index: int = 0, pan: float = 0.0) -> str:
        """
        设置项目项声相。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            pan: 声相值，范围[-1, 1]
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        if pan < -1 or pan > 1:
            return f"声相参数无效：{pan}，范围应为[-1, 1]。"
        try:
            item = track.items[item_index]
            item.takes[0].pan = pan
            update_arrange()
            return f"成功设置项目项声相为{pan}。"
        except Exception as e:
            return f"设置项目项声相失败：{e}"