import os
from mcp.server.fastmcp import FastMCP
from utils.reaper_client import ensure_project_ready

def register_project_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_get_project_info() -> dict:
        """
        获取当前项目信息。
        
        Returns:
            项目信息字典
        """
        success, message, project = ensure_project_ready()
        if not success:
            return {"error": message}
        try:
            return {
                "name": project.name,
                "path": project.path,
                "length": project.length,
                "num_tracks": len(project.tracks),
                "num_items": len(project.items),
                "sample_rate": project.sample_rate,
                "bpm": project.bpm,
                "is_playing": project.is_playing
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def reaper_save_project() -> str:
        """
        保存当前项目。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.save()
            return f"项目已保存到：{project.path}"
        except Exception as e:
            return f"保存项目失败：{e}"

    @mcp.tool()
    def reaper_save_project_as(file_path: str = "") -> str:
        """
        将项目另存为指定路径。
        
        Args:
            file_path: 目标文件路径（.rpp文件）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        if not file_path:
            return "请提供目标文件路径。"
        try:
            from reapy import reascript_api as reaper
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            reaper.Main_SaveProjectEx(0, file_path, 0)
            return f"项目已保存到：{file_path}"
        except Exception as e:
            return f"另存项目失败：{e}"

    @mcp.tool()
    def reaper_new_project() -> str:
        """
        创建新项目。
        
        Returns:
            操作结果消息
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40022, 0)
            return "成功创建新项目。"
        except Exception as e:
            return f"创建新项目失败：{e}"

    @mcp.tool()
    def reaper_open_project(file_path: str = "") -> str:
        """
        打开项目文件。
        
        Args:
            file_path: 项目文件路径（.rpp文件）
        
        Returns:
            操作结果消息
        """
        if not file_path:
            return "请提供项目文件路径。"
        if not os.path.exists(file_path):
            return f"项目文件不存在：{file_path}"
        try:
            from reapy import reascript_api as reaper
            reaper.Main_openProject(file_path)
            return f"成功打开项目：{file_path}"
        except Exception as e:
            return f"打开项目失败：{e}"

    @mcp.tool()
    def reaper_set_project_bpm(bpm: float = 120.0) -> str:
        """
        设置项目BPM。
        
        Args:
            bpm: BPM值
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        if bpm <= 0:
            return "BPM值必须大于0。"
        try:
            project.bpm = bpm
            return f"成功设置项目BPM为{bpm}。"
        except Exception as e:
            return f"设置BPM失败：{e}"

    @mcp.tool()
    def reaper_get_project_bpm() -> dict:
        """
        获取项目BPM。
        
        Returns:
            包含BPM的字典
        """
        success, message, project = ensure_project_ready()
        if not success:
            return {"error": message}
        try:
            return {"bpm": project.bpm}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def reaper_set_project_time_signature(numerator: int = 4, denominator: int = 4) -> str:
        """
        设置项目拍号。
        
        Args:
            numerator: 分子（每小节拍数）
            denominator: 分母（拍的时值）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        if numerator <= 0 or denominator <= 0:
            return "拍号参数必须大于0。"
        try:
            from reapy import reascript_api as reaper
            reaper.SetTempoTimeSigMarker(0, 0, 0, numerator, denominator, 0, 0, "")
            return f"成功设置项目拍号为{numerator}/{denominator}。"
        except Exception as e:
            return f"设置拍号失败：{e}"

    @mcp.tool()
    def reaper_undo() -> str:
        """
        撤销上一步操作。
        
        Returns:
            操作结果消息
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40001, 0)
            return "已撤销上一步操作。"
        except Exception as e:
            return f"撤销失败：{e}"

    @mcp.tool()
    def reaper_redo() -> str:
        """
        重做上一步操作。
        
        Returns:
            操作结果消息
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40002, 0)
            return "已重做上一步操作。"
        except Exception as e:
            return f"重做失败：{e}"

    @mcp.tool()
    def reaper_calculate_normalization(track_name: str = "") -> dict:
        """
        计算音轨归一化增益。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            包含归一化信息的字典
        """
        from utils.reaper_client import get_track_by_name
        track = get_track_by_name(track_name)
        if track is None:
            return {"error": f"没有找到音轨「{track_name}」。"}
        try:
            from reapy import reascript_api as reaper
            items = list(track.items)
            if not items:
                return {"error": "音轨没有项目项。"}
            take = items[0].takes[0]
            retval, peak, rms = reaper.CalculateNormalization(take, 0, 0, -18, 0, 0)
            return {
                "track_name": track_name,
                "peak_level_db": peak,
                "rms_level_db": rms,
                "gain_to_normalize_db": -18 - rms if rms < -18 else 0
            }
        except Exception as e:
            return {"error": str(e)}