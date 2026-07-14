from mcp.server.fastmcp import FastMCP
from utils.reaper_client import ensure_project_ready

def register_playback_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_play() -> str:
        """
        开始播放。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.play()
            return "开始播放。"
        except Exception as e:
            return f"播放失败：{e}"

    @mcp.tool()
    def reaper_stop() -> str:
        """
        停止播放。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.stop()
            return "停止播放。"
        except Exception as e:
            return f"停止失败：{e}"

    @mcp.tool()
    def reaper_toggle_play() -> str:
        """
        切换播放/暂停状态。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            if project.is_playing:
                project.pause()
                return "暂停播放。"
            else:
                project.play()
                return "开始播放。"
        except Exception as e:
            return f"切换播放状态失败：{e}"

    @mcp.tool()
    def reaper_pause() -> str:
        """
        暂停播放。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.pause()
            return "暂停播放。"
        except Exception as e:
            return f"暂停失败：{e}"

    @mcp.tool()
    def reaper_record() -> str:
        """
        开始录音。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.record()
            return "开始录音。"
        except Exception as e:
            return f"录音失败：{e}"

    @mcp.tool()
    def reaper_go_to_start() -> str:
        """
        将播放指针移动到项目开头。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.play_position = 0
            return "播放指针已移动到项目开头。"
        except Exception as e:
            return f"移动播放指针失败：{e}"

    @mcp.tool()
    def reaper_go_to_end() -> str:
        """
        将播放指针移动到项目末尾。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.play_position = project.length
            return "播放指针已移动到项目末尾。"
        except Exception as e:
            return f"移动播放指针失败：{e}"

    @mcp.tool()
    def reaper_set_play_position(time: float = 0.0) -> str:
        """
        设置播放指针位置。
        
        Args:
            time: 时间位置（秒）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            project.play_position = time
            return f"播放指针已移动到{time}秒处。"
        except Exception as e:
            return f"设置播放位置失败：{e}"

    @mcp.tool()
    def reaper_get_play_position() -> dict:
        """
        获取当前播放位置和状态。
        
        Returns:
            包含播放位置和状态的字典
        """
        success, message, project = ensure_project_ready()
        if not success:
            return {"error": message}
        try:
            return {
                "play_position": project.play_position,
                "is_playing": project.is_playing,
                "is_paused": project.is_paused,
                "is_recording": project.is_recording
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def reaper_set_loop_range(start_time: float = 0.0, end_time: float = 0.0) -> str:
        """
        设置循环播放范围。
        
        Args:
            start_time: 循环开始时间（秒）
            end_time: 循环结束时间（秒）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        if end_time <= start_time:
            return "结束时间必须大于开始时间。"
        try:
            from reapy import reascript_api as reaper
            reaper.SetLoopTimeRange(start_time, end_time, False)
            return f"循环范围已设置为{start_time}秒到{end_time}秒。"
        except Exception as e:
            return f"设置循环范围失败：{e}"

    @mcp.tool()
    def reaper_toggle_loop() -> str:
        """
        切换循环播放模式。
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            from reapy import reascript_api as reaper
            retval, loop_start, loop_end = reaper.GetSet_LoopTimeRange(False, False, 0, 0, False)
            if loop_start == loop_end:
                return "请先设置循环范围。"
            reaper.Main_OnCommand(40434, 0)
            return "循环播放模式已切换。"
        except Exception as e:
            return f"切换循环模式失败：{e}"