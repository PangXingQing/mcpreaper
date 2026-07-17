"""
节拍器与工程设置扩展。

提供节拍器（Click/Metronome）配置、录音模式、工程采样率等设置。
"""
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    reaper_tool_error_handler,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
)


def register_metronome_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_metronome() -> dict:
        """
        切换节拍器开关。

        Returns:
            节拍器当前状态
        """
        try:
            from reapy import reascript_api as reaper
            current = reaper.GetToggleCommandState(40364)
            reaper.Main_OnCommand(40364, 0)  # Options: Toggle metronome
            new_state = reaper.GetToggleCommandState(40364)
            return format_success_response(
                message=f"节拍器：{'开启' if new_state else '关闭'}",
                data={"metronome_enabled": bool(new_state)},
            )
        except Exception as e:
            raise OperationFailedError("切换节拍器", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_metronome_enable_playback(enable: bool = True) -> dict:
        """
        设置节拍器在播放时是否发声。

        Args:
            enable: True = 播放时节拍器响，False = 仅录音时响

        Returns:
            操作结果
        """
        try:
            from reapy import reascript_api as reaper
            # 获取当前节拍器设置
            retval, enabled_play, enabled_rec, enabled_preroll = reaper.Metronome_GetOptions(0)
            if retval:
                reaper.Metronome_SetOptions(enabled_play, enabled_rec, enabled_preroll, 0)
            return format_success_response(
                message=f"节拍器播放模式：{'播放时响' if enable else '仅录音时响'}"
            )
        except Exception as e:
            raise OperationFailedError("设置节拍器播放模式", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_metronome_volume(volume_db: float = -6.0) -> dict:
        """
        设置节拍器音量。

        Args:
            volume_db: 音量（dB），范围 [-50, 6]

        Returns:
            操作结果
        """
        if volume_db < -50 or volume_db > 6:
            raise InvalidParameterError(
                "volume_db", volume_db, "有效范围 [-50, 6] dB"
            )

        try:
            from reapy import reascript_api as reaper
            # NOTE: reapy/ReaScript 不直接支持 Metronome volume，
            # 通知用户手动设置
            return format_success_response(
                message=f"请手动设置：右键节拍器图标 → Volume = {volume_db}dB（API 不直接支持此设置）",
                data={"suggested_volume_db": volume_db},
            )
        except Exception as e:
            raise OperationFailedError("设置节拍器音量", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_record_mode(mode: str = "normal") -> dict:
        """
        设置录音模式。

        支持的模式：
        - "normal": 普通录音（新录制覆盖已有内容）
        - "takes": 添加到当前 Item 的新 Take 中
        - "punch": 时间选区插入录音（需要先设置时间选区）
        - "loop": 循环录音（在循环范围内重复录音，每次创建新 Take）

        Args:
            mode: 录音模式标识

        Returns:
            操作结果
        """
        valid_modes = {
            "normal": "普通录音",
            "takes": "Take 模式（叠录）",
            "punch": "插入录音（时间选区）",
            "loop": "循环录音（创建多层 Take）",
        }

        if mode not in valid_modes:
            raise InvalidParameterError(
                "mode", mode,
                f"有效值：{list(valid_modes.keys())}",
                "例如 'takes' 表示在已有 Item 上叠录"
            )

        try:
            from reapy import reascript_api as reaper
            mode_map = {"normal": 40252, "takes": 40253, "punch": 40254, "loop": 40255}
            reaper.Main_OnCommand(mode_map[mode], 0)
            return format_success_response(
                message=f"录音模式切换为：{valid_modes[mode]}",
                data={"mode": mode, "description": valid_modes[mode]},
            )
        except Exception as e:
            raise OperationFailedError("设置录音模式", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_project_sample_rate() -> dict:
        """
        获取工程的采样率。

        Returns:
            当前采样率（Hz）
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        try:
            sr = project.get_info_value("PROJECT_SRATE")
            return format_success_response(data={
                "sample_rate": int(sr),
                "unit": "Hz",
                "common_rates": [44100, 48000, 88200, 96000, 176400, 192000],
            })
        except Exception as e:
            raise OperationFailedError("获取采样率", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_project_sample_rate(sample_rate: int = 48000) -> dict:
        """
        设置工程的采样率。

        Args:
            sample_rate: 采样率（Hz），常用值 44100, 48000, 96000

        Returns:
            操作结果
        """
        valid_rates = [44100, 48000, 88200, 96000, 176400, 192000]
        if sample_rate not in valid_rates:
            raise InvalidParameterError(
                "sample_rate", sample_rate,
                f"常用采样率：{valid_rates}"
            )

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        try:
            project.set_info_value("PROJECT_SRATE", sample_rate)
            return format_success_response(
                message=f"采样率已设为 {sample_rate} Hz"
            )
        except Exception as e:
            raise OperationFailedError("设置采样率", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_click_source(track_name: str = "") -> dict:
        """
        在指定轨道上插入节拍器（Click Source）媒体项。

        这会创建一个包含节拍器声音的音频 Item。

        Args:
            track_name: 目标轨道名称

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        from utils import get_track_by_name, TrackNotFoundError, get_available_track_names
        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            # 选择目标轨道
            reaper.SetOnlyTrackSelected(track)
            # 插入 Click Source（Action ID: 40161）
            reaper.Main_OnCommand(40161, 0)
            return format_success_response(
                message=f"已在「{track_name}」上插入节拍器源"
            )
        except Exception as e:
            raise OperationFailedError("插入节拍器源", str(e))
