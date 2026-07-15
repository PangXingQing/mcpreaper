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

def register_film_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_import_video(file_path: str = "") -> dict:
        """
        导入视频文件到项目。
        
        Args:
            file_path: 视频文件路径
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not file_path:
            raise InvalidParameterError("file_path", file_path, "请提供有效的视频文件路径")
        
        if not os.path.exists(file_path):
            raise ReaperFileNotFoundError(file_path)
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetProjectMediaFileName(file_path)
            update_arrange()
            return format_success_response(message=f"成功导入视频文件：{file_path}")
        except Exception as e:
            raise OperationFailedError("导入视频", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_timecode_format(format_type: str = "SMPTE") -> dict:
        """
        设置时间码格式。
        
        Args:
            format_type: 时间码格式（SMPTE, Feet+Frames, Samples, Beats）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        format_map = {
            "SMPTE": 0,
            "Feet+Frames": 1,
            "Samples": 2,
            "Beats": 3
        }
        
        if format_type not in format_map:
            raise InvalidParameterError(
                "format_type", format_type,
                f"可用格式：{list(format_map.keys())}"
            )
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetToggleCommandState(40634, 0, format_map[format_type])
            reaper.Main_OnCommand(40634, 0)
            return format_success_response(message=f"成功设置时间码格式为：{format_type}")
        except Exception as e:
            raise OperationFailedError("设置时间码格式", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_frame_rate(frame_rate: float = 24.0) -> dict:
        """
        设置项目帧率。
        
        Args:
            frame_rate: 帧率（如24.0, 25.0, 30.0, 60.0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if frame_rate <= 0 or frame_rate > 120:
            raise InvalidParameterError("frame_rate", frame_rate, "有效值范围：(0, 120]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.GetSetProjectInfo(project, "PROJECT_FPS", frame_rate, True)
            return format_success_response(message=f"成功设置项目帧率为：{frame_rate}fps")
        except Exception as e:
            raise OperationFailedError("设置项目帧率", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_start_timecode(hours: int = 0, minutes: int = 0, seconds: int = 0, frames: int = 0) -> dict:
        """
        设置项目开始时间码。
        
        Args:
            hours: 小时（0-23）
            minutes: 分钟（0-59）
            seconds: 秒（0-59）
            frames: 帧（0-30，取决于帧率）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if hours < 0 or hours > 23:
            raise InvalidParameterError("hours", hours, "有效值范围：[0, 23]")
        if minutes < 0 or minutes > 59:
            raise InvalidParameterError("minutes", minutes, "有效值范围：[0, 59]")
        if seconds < 0 or seconds > 59:
            raise InvalidParameterError("seconds", seconds, "有效值范围：[0, 59]")
        if frames < 0:
            raise InvalidParameterError("frames", frames, "有效值范围：>= 0")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            timecode_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
            reaper.GetSetProjectInfo_String(project, "PROJECT_TIMECODE_START", timecode_str, True)
            return format_success_response(message=f"成功设置项目开始时间码为：{timecode_str}")
        except Exception as e:
            raise OperationFailedError("设置开始时间码", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_sync_reference(mode: str = "Internal") -> dict:
        """
        设置同步参考模式。
        
        Args:
            mode: 同步模式（Internal, Video, MTC, SMPTE）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        mode_map = {
            "Internal": 0,
            "Video": 1,
            "MTC": 2,
            "SMPTE": 3
        }
        
        if mode not in mode_map:
            raise InvalidParameterError(
                "mode", mode,
                f"可用模式：{list(mode_map.keys())}"
            )
        
        try:
            from reapy import reascript_api as reaper
            reaper.GetSetProjectInfo(project, "PROJECT_SYNC_MODE", mode_map[mode], True)
            return format_success_response(message=f"成功设置同步参考模式为：{mode}")
        except Exception as e:
            raise OperationFailedError("设置同步参考模式", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_batch_render_tracks(output_dir: str = "", track_names: list = None, format: str = "wav") -> dict:
        """
        批量渲染多个音轨。
        
        Args:
            output_dir: 输出目录
            track_names: 要渲染的音轨名称列表
            format: 输出格式（wav, mp3, flac, ogg）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not output_dir:
            raise InvalidParameterError("output_dir", output_dir, "请提供有效的输出目录")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        from reapy import reascript_api as reaper
        reaper.Main_OnCommand(40297, 0)
        
        available_tracks = get_available_track_names()
        found_tracks = []
        missing_tracks = []
        
        for track_name in (track_names or []):
            track = get_track_by_name(track_name)
            if track:
                reaper.SetTrackSelected(track, True)
                found_tracks.append(track_name)
            else:
                missing_tracks.append(track_name)
        
        reaper.GetSetProjectInfo(project, "RENDER_STEMSFLAG", 1, True)
        
        format_map = {"wav": 0, "mp3": 1, "flac": 2, "ogg": 3}
        if format not in format_map:
            raise InvalidParameterError(
                "format", format,
                f"可用格式：{list(format_map.keys())}"
            )
        
        reaper.GetSetProjectInfo(project, "RENDER_FORMAT", format_map[format], True)
        reaper.GetSetProjectInfo_String(project, "RENDER_FILE", output_dir + os.sep, True)
        reaper.Main_OnCommand(41893, 0)
        
        message = f"开始批量渲染音轨到目录：{output_dir}"
        if found_tracks:
            message += f"\n已选择音轨：{', '.join(found_tracks)}"
        if missing_tracks:
            message += f"\n未找到的音轨：{', '.join(missing_tracks)}（已跳过）"
        
        return format_success_response(message=message)

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_render_stems(output_dir: str = "", stem_type: str = "all") -> dict:
        """
        渲染分轨（Stems）。
        
        Args:
            output_dir: 输出目录
            stem_type: 分轨类型（all, tracks, folders, selected）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not output_dir:
            raise InvalidParameterError("output_dir", output_dir, "请提供有效的输出目录")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        from reapy import reascript_api as reaper
        
        stem_flags = {
            "all": 2,
            "tracks": 1,
            "folders": 4,
            "selected": 8
        }
        
        if stem_type not in stem_flags:
            raise InvalidParameterError(
                "stem_type", stem_type,
                "可用类型：all, tracks, folders, selected"
            )
        
        reaper.GetSetProjectInfo(project, "RENDER_STEMSFLAG", stem_flags[stem_type], True)
        reaper.GetSetProjectInfo_String(project, "RENDER_FILE", output_dir + os.sep, True)
        reaper.Main_OnCommand(41893, 0)
        
        return format_success_response(message=f"开始渲染{stem_type}分轨到目录：{output_dir}")

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_adr_track(prefix: str = "ADR_", count: int = 1) -> dict:
        """
        创建ADR（自动对白替换）音轨组。
        
        Args:
            prefix: 音轨名称前缀
            count: 音轨数量（>= 1）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if count < 1:
            raise InvalidParameterError("count", count, "有效值范围：>= 1")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            created_tracks = []
            
            for i in range(count):
                reaper.Main_OnCommand(40701, 0)
                new_track = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
                track_name = f"{prefix}{i+1}"
                reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", track_name, True)
                created_tracks.append(track_name)
            
            update_arrange()
            return format_success_response(message=f"成功创建{count}个ADR音轨：{', '.join(created_tracks)}")
        except Exception as e:
            raise OperationFailedError("创建ADR音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_foley_tracks() -> dict:
        """
        创建标准拟音音轨组。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            foley_types = ["Foley_Footsteps", "Foley_Cloth", "Foley_Props", "Foley_Body", "Foley_Ambience"]
            
            for foley_name in foley_types:
                reaper.Main_OnCommand(40701, 0)
                new_track = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
                reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", foley_name, True)
            
            update_arrange()
            return format_success_response(message=f"成功创建拟音音轨组：{', '.join(foley_types)}")
        except Exception as e:
            raise OperationFailedError("创建拟音音轨组", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_sound_effects_tracks() -> dict:
        """
        创建标准音效音轨组。
        
        Returns:
            操作结果字典，包含success、message字段
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            sfx_types = ["SFX_Ambience", "SFX_FX", "SFX_Music", "SFX_Dialogue", "SFX_Dialogue_Clean"]
            
            for sfx_name in sfx_types:
                reaper.Main_OnCommand(40701, 0)
                new_track = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
                reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", sfx_name, True)
            
            update_arrange()
            return format_success_response(message=f"成功创建音效音轨组：{', '.join(sfx_types)}")
        except Exception as e:
            raise OperationFailedError("创建音效音轨组", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_video_info() -> dict:
        """
        获取视频信息。
        
        Returns:
            视频信息字典，包含success字段和视频信息
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            result1 = reaper.GetSetProjectInfo_String(project, "PROJECT_VIDEO_FILE", "", False)
            video_file = result1[3] if len(result1) > 3 else ""
            frame_rate = reaper.GetSetProjectInfo(project, "PROJECT_FPS", 0, False)
            result2 = reaper.GetSetProjectInfo_String(project, "PROJECT_TIMECODE_START", "", False)
            timecode_start = result2[3] if len(result2) > 3 else ""
            
            return format_success_response(data={
                "video_file": video_file if video_file else "未导入视频",
                "frame_rate": frame_rate,
                "timecode_start": timecode_start if timecode_start else "00:00:00:00"
            })
        except Exception as e:
            raise OperationFailedError("获取视频信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_cue_marker(time: float = 0.0, cue_name: str = "", color: int = 0) -> dict:
        """
        在时间轴上插入提示标记（用于同步）。
        
        Args:
            time: 时间位置（秒，>= 0）
            cue_name: 标记名称
            color: 颜色索引（0-15）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if time < 0:
            raise InvalidParameterError("time", time, "有效值范围：>= 0")
        if color < 0 or color > 15:
            raise InvalidParameterError("color", color, "有效值范围：[0, 15]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.AddProjectMarker(project, False, time, 0, cue_name, -1)
            update_arrange()
            return format_success_response(message=f"成功在{time}秒处插入提示标记「{cue_name}」。")
        except Exception as e:
            raise OperationFailedError("插入提示标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_export_session_info(file_path: str = "") -> dict:
        """
        导出会话信息（EDL/AAF格式）。
        
        Args:
            file_path: 输出文件路径
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not file_path:
            raise InvalidParameterError("file_path", file_path, "请提供有效的输出文件路径")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.Main_OnCommand(41752, 0)
            return format_success_response(message=f"成功导出会话信息到：{file_path}")
        except Exception as e:
            raise OperationFailedError("导出会话信息", str(e))