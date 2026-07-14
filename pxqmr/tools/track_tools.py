from mcp.server.fastmcp import FastMCP
from utils.reaper_client import ensure_project_ready, get_track_by_name, update_arrange
import reapy
from reapy import reascript_api as reaper

def register_track_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_add_track(track_name: str = "") -> str:
        """
        在Reaper中创建新音轨。
        
        Args:
            track_name: 新音轨的名称
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            track = project.add_track(0, track_name)
            track.make_only_selected_track()
            update_arrange()
            return f"成功创建音轨「{track_name}」。"
        except Exception as e:
            return f"创建音轨失败：{e}"

    @mcp.tool()
    def reaper_select_track(track_name: str = "") -> str:
        """
        选择指定音轨。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.make_only_selected_track()
            update_arrange()
            return f"成功选择音轨「{track_name}」。"
        except Exception as e:
            return f"选择音轨失败：{e}"

    @mcp.tool()
    def reaper_get_all_tracks() -> list[dict]:
        """
        获取所有音轨信息。
        
        Returns:
            音轨信息列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            return [{"error": message}]
        try:
            track_info = []
            for track in project.tracks:
                track_info.append({
                    "name": track.name,
                    "volume": track.volume,
                    "pan": track.pan,
                    "mute": track.mute,
                    "solo": track.solo,
                    "rec_arm": track.rec_arm
                })
            return track_info
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_get_all_track_names() -> list[str]:
        """
        获取所有音轨名称。
        
        Returns:
            音轨名称列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            return [message]
        try:
            return [track.name for track in project.tracks]
        except Exception as e:
            return [str(e)]

    @mcp.tool()
    def reaper_delete_track(track_name: str = "") -> str:
        """
        删除指定音轨。
        
        Args:
            track_name: 要删除的音轨名称
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.delete()
            update_arrange()
            return f"成功删除音轨「{track_name}」。"
        except Exception as e:
            return f"删除音轨失败：{e}"

    @mcp.tool()
    def reaper_rename_track(track_name: str = "", new_name: str = "") -> str:
        """
        重命名音轨。
        
        Args:
            track_name: 当前音轨名称
            new_name: 新名称
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.name = new_name
            update_arrange()
            return f"成功将音轨「{track_name}」重命名为「{new_name}」。"
        except Exception as e:
            return f"重命名音轨失败：{e}"

    @mcp.tool()
    def reaper_set_track_volume(track_name: str = "", volume: float = 1.0) -> str:
        """
        设置音轨音量（线性值）。
        
        Args:
            track_name: 音轨名称
            volume: 音量值，范围[0, 4]，其中0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if volume < 0 or volume > 4:
            return f"音量参数无效：{volume}，范围应为[0, 4]。"
        try:
            track.volume = volume
            update_arrange()
            return f"成功设置音轨「{track_name}」的音量为{volume}。"
        except Exception as e:
            return f"设置音量失败：{e}"

    @mcp.tool()
    def reaper_set_track_volume_db(track_name: str = "", volume_db: float = 0.0) -> str:
        """
        设置音轨音量（分贝值）。
        
        Args:
            track_name: 音轨名称
            volume_db: 分贝值，范围[-100, +12]dB
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            if volume_db < -100:
                track.volume = 0
                display_val = "-inf"
            elif volume_db > 12:
                track.volume = 4
                display_val = "+12dB"
            else:
                track.volume = 10 ** (volume_db / 20)
                display_val = f"{volume_db}dB"
            update_arrange()
            return f"成功设置音轨「{track_name}」的音量为{display_val}。"
        except Exception as e:
            return f"设置音量失败：{e}"

    @mcp.tool()
    def reaper_set_track_pan(track_name: str = "", pan: float = 0.0) -> str:
        """
        设置音轨声相。
        
        Args:
            track_name: 音轨名称
            pan: 声相值，范围[-1, 1]，-1=左，0=中，1=右
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if pan < -1 or pan > 1:
            return f"声相参数无效：{pan}，范围应为[-1, 1]。"
        try:
            track.pan = pan
            update_arrange()
            return f"成功设置音轨「{track_name}」的声相为{pan}。"
        except Exception as e:
            return f"设置声相失败：{e}"

    @mcp.tool()
    def reaper_set_track_mute(track_name: str = "", mute: bool = False) -> str:
        """
        设置音轨静音状态。
        
        Args:
            track_name: 音轨名称
            mute: 是否静音
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.mute = mute
            update_arrange()
            status = "静音" if mute else "取消静音"
            return f"成功{status}音轨「{track_name}」。"
        except Exception as e:
            return f"设置静音状态失败：{e}"

    @mcp.tool()
    def reaper_set_track_solo(track_name: str = "", solo: bool = False) -> str:
        """
        设置音轨独奏状态。
        
        Args:
            track_name: 音轨名称
            solo: 是否独奏
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.solo = solo
            update_arrange()
            status = "独奏" if solo else "取消独奏"
            return f"成功{status}音轨「{track_name}」。"
        except Exception as e:
            return f"设置独奏状态失败：{e}"

    @mcp.tool()
    def reaper_set_track_rec_arm(track_name: str = "", rec_arm: bool = False) -> str:
        """
        设置音轨录音准备状态。
        
        Args:
            track_name: 音轨名称
            rec_arm: 是否启用录音准备
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            track.rec_arm = rec_arm
            update_arrange()
            status = "启用录音准备" if rec_arm else "禁用录音准备"
            return f"成功{status}音轨「{track_name}」。"
        except Exception as e:
            return f"设置录音准备状态失败：{e}"

    @mcp.tool()
    def reaper_get_track_info(track_name: str = "") -> dict:
        """
        获取指定音轨的详细信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            音轨信息字典
        """
        track = get_track_by_name(track_name)
        if track is None:
            return {"error": f"没有找到音轨「{track_name}」。"}
        try:
            return {
                "name": track.name,
                "volume": track.volume,
                "pan": track.pan,
                "mute": track.mute,
                "solo": track.solo,
                "rec_arm": track.rec_arm,
                "num_items": len(track.items),
                "num_fx": len(track.fxs)
            }
        except Exception as e:
            return {"error": str(e)}