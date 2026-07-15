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

def register_render_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_render_project(output_path: str = "", render_mode: int = 0) -> dict:
        """
        渲染项目。
        
        Args:
            output_path: 输出文件路径（包含文件名和扩展名）
            render_mode: 渲染模式：0=时间选择范围, 1=整个项目, 2=选区媒体项, 3=轨道区域
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if not output_path:
            raise InvalidParameterError("output_path", output_path, "请提供有效的输出文件路径")
        
        dir_path = os.path.dirname(output_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        if render_mode < 0 or render_mode > 3:
            raise InvalidParameterError("render_mode", render_mode, "有效值范围：[0, 3]")
        
        try:
            from reapy import reascript_api as reaper
            reaper.GetSetProjectInfo_String(project, "RENDER_FILE", output_path, True)
            
            mode_names = ["时间选择范围", "整个项目", "选区媒体项", "轨道区域"]
            reaper.GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", render_mode, True)
            
            reaper.Main_OnCommand(41893, 0)
            return format_success_response(
                message=f"开始渲染项目（{mode_names[render_mode]}）到：{output_path}"
            )
        except Exception as e:
            raise OperationFailedError("渲染项目", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_render_selected_tracks(output_path: str = "", track_names: list = None) -> dict:
        """
        渲染选定的音轨。
        
        Args:
            output_path: 输出文件路径
            track_names: 要渲染的音轨名称列表
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if not output_path:
            raise InvalidParameterError("output_path", output_path, "请提供有效的输出文件路径")
        
        dir_path = os.path.dirname(output_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(40297, 0)
            
            found_tracks = []
            missing_tracks = []
            
            for track_name in (track_names or []):
                track = get_track_by_name(track_name)
                if track:
                    reaper.SetTrackSelected(track, True)
                    found_tracks.append(track_name)
                else:
                    missing_tracks.append(track_name)
            
            reaper.GetSetProjectInfo_String(project, "RENDER_FILE", output_path, True)
            reaper.GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 1, True)
            reaper.GetSetProjectInfo(project, "RENDER_STEMSFLAG", 0, True)
            
            reaper.Main_OnCommand(41893, 0)
            
            message = f"开始渲染选定音轨到：{output_path}"
            if found_tracks:
                message += f"\n已选择音轨：{', '.join(found_tracks)}"
            if missing_tracks:
                message += f"\n未找到的音轨：{', '.join(missing_tracks)}（已跳过）"
            
            return format_success_response(message=message)
        except Exception as e:
            raise OperationFailedError("渲染选定音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_render_settings() -> dict:
        """
        获取当前渲染设置。
        
        Returns:
            渲染设置字典，包含success字段和渲染参数
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            result = reaper.GetSetProjectInfo_String(project, "RENDER_FILE", "", False)
            render_file = result[3] if len(result) > 3 else ""
            bounds_flag = reaper.GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 0, False)
            sample_rate = reaper.GetSetProjectInfo(project, "RENDER_SRATE", 0, False)
            bit_depth = reaper.GetSetProjectInfo(project, "RENDER_BITDEPTH", 0, False)
            render_format = reaper.GetSetProjectInfo(project, "RENDER_FORMAT", 0, False)
            
            bounds_mapping = {0: "时间选择范围", 1: "整个项目", 2: "选区媒体项", 3: "轨道区域"}
            format_mapping = {0: "WAV", 1: "MP3", 2: "FLAC", 3: "OGG", 4: "AAC", 5: "WAV64"}
            
            return format_success_response(data={
                "output_file": render_file if render_file else "未设置",
                "render_bounds": bounds_mapping.get(bounds_flag, "未知"),
                "sample_rate": sample_rate,
                "bit_depth": bit_depth,
                "format": format_mapping.get(render_format, "未知")
            })
        except Exception as e:
            raise OperationFailedError("获取渲染设置", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_render_settings(sample_rate: int = 44100, bit_depth: int = 24) -> dict:
        """
        设置渲染参数。
        
        Args:
            sample_rate: 采样率（如44100, 48000, 96000），有效值范围：[8000, 384000]
            bit_depth: 位深度（如16, 24, 32），有效值范围：[8, 32]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if sample_rate < 8000 or sample_rate > 384000:
            raise InvalidParameterError("sample_rate", sample_rate, "有效值范围：[8000, 384000]")
        
        valid_bit_depths = [8, 16, 24, 32]
        if bit_depth not in valid_bit_depths:
            raise InvalidParameterError("bit_depth", bit_depth, f"有效值：{valid_bit_depths}")
        
        try:
            from reapy import reascript_api as reaper
            reaper.GetSetProjectInfo(project, "RENDER_SRATE", sample_rate, True)
            reaper.GetSetProjectInfo(project, "RENDER_BITDEPTH", bit_depth, True)
            return format_success_response(
                message=f"成功设置渲染参数：采样率{sample_rate}Hz，位深度{bit_depth}位。"
            )
        except Exception as e:
            raise OperationFailedError("设置渲染参数", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_render_item_as_new_take(track_name: str = "", item_index: int = 0) -> dict:
        """
        将媒体项渲染为新的take。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        try:
            from reapy import reascript_api as reaper
            if item_index >= len(track.items):
                raise InvalidParameterError(
                    "item_index", item_index,
                    f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
                )
            
            item = track.items[item_index]
            reaper.SetMediaItemSelected(item, True)
            reaper.Main_OnCommand(41588, 0)
            update_arrange()
            
            return format_success_response(message=f"成功将音轨「{track_name}」的第{item_index}个项目项渲染为新take。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("渲染项目项", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_render_marker_region(start_time: float = 0.0, end_time: float = 0.0, region_name: str = "Render") -> dict:
        """
        创建渲染区域标记。
        
        Args:
            start_time: 开始时间（秒，>= 0）
            end_time: 结束时间（秒，> start_time）
            region_name: 区域名称
        
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
            reaper.AddProjectMarker(project, True, start_time, end_time, region_name, -1)
            update_arrange()
            
            return format_success_response(
                message=f"成功设置渲染区域：{start_time}秒到{end_time}秒（名称：{region_name}）"
            )
        except Exception as e:
            raise OperationFailedError("设置渲染区域", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_render_free_item_position(track_name: str = "", item_index: int = 0, output_path: str = "") -> dict:
        """
        渲染选中媒体项的自由位置。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            output_path: 输出文件路径
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not output_path:
            raise InvalidParameterError("output_path", output_path, "请提供有效的输出文件路径")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        try:
            from reapy import reascript_api as reaper
            if item_index >= len(track.items):
                raise InvalidParameterError(
                    "item_index", item_index,
                    f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
                )
            
            dir_path = os.path.dirname(output_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            item = track.items[item_index]
            reaper.SetMediaItemSelected(item, True)
            
            reaper.GetSetProjectInfo_String(project, "RENDER_FILE", output_path, True)
            reaper.GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 2, True)
            reaper.GetSetProjectInfo(project, "RENDER_STEMSFLAG", 0, True)
            
            reaper.Main_OnCommand(41893, 0)
            
            return format_success_response(
                message=f"成功将音轨「{track_name}」的第{item_index}个项目项渲染到：{output_path}"
            )
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("渲染自由位置项目项", str(e))