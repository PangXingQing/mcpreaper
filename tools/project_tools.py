import os
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    get_track_by_name,
    reaper_tool_error_handler,
    TrackNotFoundError,
    InvalidParameterError,
    ReaperFileNotFoundError,
    OperationFailedError,
    format_success_response,
    get_available_track_names
)

def register_project_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_project_info() -> dict:
        """
        获取当前项目信息。
        
        Returns:
            项目信息字典，包含success字段和项目详细信息
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            return format_success_response(data={
                "name": project.name,
                "path": project.path,
                "length": project.length,
                "num_tracks": len(project.tracks),
                "num_items": len(project.items),
                "sample_rate": project.get_info_value('PROJECT_SRATE'),
                "bpm": project.bpm,
                "is_playing": project.is_playing
            })
        except Exception as e:
            raise OperationFailedError("获取项目信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_save_project() -> dict:
        """
        保存当前项目。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            project.save()
            return format_success_response(message=f"项目已保存到：{project.path}")
        except Exception as e:
            raise OperationFailedError("保存项目", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_save_project_as(file_path: str = "") -> dict:
        """
        将项目另存为指定路径。
        
        Args:
            file_path: 目标文件路径（.rpp文件）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if not file_path:
            raise InvalidParameterError("file_path", file_path, "请提供有效的目标文件路径")
        
        try:
            from reapy import reascript_api as reaper
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            reaper.Main_SaveProjectEx(0, file_path, 0)
            return format_success_response(message=f"项目已保存到：{file_path}")
        except Exception as e:
            raise OperationFailedError("另存项目", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_new_project() -> dict:
        """
        创建新项目。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40022, 0)
            return format_success_response(message="成功创建新项目。")
        except Exception as e:
            raise OperationFailedError("创建新项目", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_open_project(file_path: str = "") -> dict:
        """
        打开项目文件。
        
        Args:
            file_path: 项目文件路径（.rpp文件）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not file_path:
            raise InvalidParameterError("file_path", file_path, "请提供有效的项目文件路径")
        
        if not os.path.exists(file_path):
            raise ReaperFileNotFoundError(file_path)
        
        if not file_path.endswith(".rpp"):
            raise InvalidParameterError("file_path", file_path, "项目文件必须是.rpp格式")
        
        try:
            from reapy import reascript_api as reaper
            reaper.Main_openProject(file_path)
            return format_success_response(message=f"成功打开项目：{file_path}")
        except Exception as e:
            raise OperationFailedError("打开项目", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_project_bpm(bpm: float = 120.0) -> dict:
        """
        设置项目BPM。
        
        Args:
            bpm: BPM值（有效值范围：[30, 300]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if bpm <= 0:
            raise InvalidParameterError("bpm", bpm, "BPM值必须大于0")
        
        if bpm < 30 or bpm > 300:
            raise InvalidParameterError("bpm", bpm, "有效值范围：[30, 300]")
        
        try:
            project.bpm = bpm
            return format_success_response(message=f"成功设置项目BPM为{bpm}。")
        except Exception as e:
            raise OperationFailedError("设置BPM", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_project_bpm() -> dict:
        """
        获取项目BPM。
        
        Returns:
            BPM信息字典，包含success字段和bpm数据
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            return format_success_response(data={"bpm": project.bpm})
        except Exception as e:
            raise OperationFailedError("获取BPM", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_project_time_signature(numerator: int = 4, denominator: int = 4) -> dict:
        """
        设置项目拍号。
        
        Args:
            numerator: 分子（每小节拍数，有效值范围：[1, 32]）
            denominator: 分母（拍的时值，有效值：2, 4, 8, 16）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if numerator <= 0 or numerator > 32:
            raise InvalidParameterError("numerator", numerator, "有效值范围：[1, 32]")
        
        valid_denominators = [2, 4, 8, 16]
        if denominator not in valid_denominators:
            raise InvalidParameterError("denominator", denominator, f"有效值：{valid_denominators}")
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetTempoTimeSigMarker(0, 0, 0, numerator, denominator, 0, 0, "")
            return format_success_response(message=f"成功设置项目拍号为{numerator}/{denominator}。")
        except Exception as e:
            raise OperationFailedError("设置拍号", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_undo() -> dict:
        """
        撤销上一步操作。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40001, 0)
            return format_success_response(message="已撤销上一步操作。")
        except Exception as e:
            raise OperationFailedError("撤销操作", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_redo() -> dict:
        """
        重做上一步操作。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40002, 0)
            return format_success_response(message="已重做上一步操作。")
        except Exception as e:
            raise OperationFailedError("重做操作", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_calculate_normalization(track_name: str = "") -> dict:
        """
        计算音轨归一化增益。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            归一化信息字典，包含success字段和峰值、RMS、增益数据
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            items = list(track.items)
            if not items:
                raise OperationFailedError("计算归一化", "该音轨没有项目项")
            
            take = items[0].takes[0]
            retval, peak, rms = reaper.CalculateNormalization(take, 0, 0, -18, 0, 0)
            
            return format_success_response(data={
                "track_name": track_name,
                "peak_level_db": peak,
                "rms_level_db": rms,
                "gain_to_normalize_db": -18 - rms if rms < -18 else 0
            })
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("计算归一化", str(e))