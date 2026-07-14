from mcp.server.fastmcp import FastMCP
from utils import (
    get_track_by_name,
    update_arrange,
    reaper_tool_error_handler,
    TrackNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
    get_available_track_names
)

def register_eq_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_reaeq(track_name: str = "") -> dict:
        """
        为音轨添加ReaEQ插件。
        
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
            fx_idx = reaper.TrackFX_AddByName(track, "ReaEQ", False, -1)
            if fx_idx >= 0:
                update_arrange()
                return format_success_response(message=f"成功为音轨「{track_name}」添加ReaEQ插件。")
            else:
                raise OperationFailedError("添加ReaEQ", "ReaEQ插件未找到，请确保Reaper已正确安装")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("添加ReaEQ", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_reaeq_band(track_name: str = "", band_index: int = 0, freq_hz: float = 1000.0, gain_db: float = 0.0, q_factor: float = 1.0, filter_type: int = 0) -> dict:
        """
        设置ReaEQ的频段参数。
        
        Args:
            track_name: 音轨名称
            band_index: 频段索引（0-5，ReaEQ有6个频段）
            freq_hz: 频率（Hz），有效值范围：[20, 20000]
            gain_db: 增益（dB），有效值范围：[-12, 12]
            q_factor: Q值（带宽，越小越宽），有效值范围：[0.1, 30]
            filter_type: 滤波器类型：0=Peak, 1=Low Shelf, 2=High Shelf, 3=Low Pass, 4=High Pass, 5=Notch, 6=Band Pass
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if band_index < 0 or band_index > 5:
            raise InvalidParameterError("band_index", band_index, "有效值范围：[0, 5]")
        
        if freq_hz < 20 or freq_hz > 20000:
            raise InvalidParameterError("freq_hz", freq_hz, "有效值范围：[20, 20000]")
        
        if gain_db < -12 or gain_db > 12:
            raise InvalidParameterError("gain_db", gain_db, "有效值范围：[-12, 12]")
        
        if q_factor < 0.1 or q_factor > 30:
            raise InvalidParameterError("q_factor", q_factor, "有效值范围：[0.1, 30]")
        
        if filter_type < 0 or filter_type > 6:
            raise InvalidParameterError("filter_type", filter_type, "有效值范围：[0, 6]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            fx_idx = _find_fx_by_name(track, "ReaEQ")
            if fx_idx < 0:
                raise OperationFailedError(
                    "设置ReaEQ频段",
                    "音轨上没有找到ReaEQ插件。请先使用reaper_add_reaeq添加。"
                )
            
            band_offset = band_index * 5
            reaper.TrackFX_SetParam(track, fx_idx, band_offset, freq_hz)
            reaper.TrackFX_SetParam(track, fx_idx, band_offset + 1, gain_db)
            reaper.TrackFX_SetParam(track, fx_idx, band_offset + 2, q_factor)
            reaper.TrackFX_SetParam(track, fx_idx, band_offset + 4, filter_type)
            update_arrange()
            
            type_names = {0: "Peak", 1: "Low Shelf", 2: "High Shelf", 3: "Low Pass", 4: "High Pass", 5: "Notch", 6: "Band Pass"}
            return format_success_response(
                message=f"成功设置ReaEQ频段{band_index}：频率{freq_hz}Hz，增益{gain_db}dB，Q值{q_factor}，类型{type_names[filter_type]}。"
            )
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("设置ReaEQ频段", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_reaeq_band(track_name: str = "", band_index: int = 0) -> dict:
        """
        获取ReaEQ的频段参数。
        
        Args:
            track_name: 音轨名称
            band_index: 频段索引（0-5）
        
        Returns:
            频段参数字典，包含success字段和频段详细信息
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if band_index < 0 or band_index > 5:
            raise InvalidParameterError("band_index", band_index, "有效值范围：[0, 5]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            fx_idx = _find_fx_by_name(track, "ReaEQ")
            if fx_idx < 0:
                raise OperationFailedError("获取ReaEQ频段", "音轨上没有找到ReaEQ插件。")
            
            band_offset = band_index * 5
            freq_hz = reaper.TrackFX_GetParam(track, fx_idx, band_offset)
            gain_db = reaper.TrackFX_GetParam(track, fx_idx, band_offset + 1)
            q_factor = reaper.TrackFX_GetParam(track, fx_idx, band_offset + 2)
            filter_type = reaper.TrackFX_GetParam(track, fx_idx, band_offset + 4)
            
            type_names = {0: "Peak", 1: "Low Shelf", 2: "High Shelf", 3: "Low Pass", 4: "High Pass", 5: "Notch", 6: "Band Pass"}
            
            return format_success_response(data={
                "band_index": band_index,
                "frequency_hz": freq_hz,
                "gain_db": gain_db,
                "q_factor": q_factor,
                "filter_type": type_names.get(int(filter_type), f"未知({int(filter_type)})")
            })
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("获取ReaEQ频段", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_reset_reaeq(track_name: str = "") -> dict:
        """
        重置ReaEQ所有频段参数。
        
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
            fx_idx = _find_fx_by_name(track, "ReaEQ")
            if fx_idx < 0:
                raise OperationFailedError("重置ReaEQ", "音轨上没有找到ReaEQ插件。")
            
            reaper.TrackFX_SetPreset(track, fx_idx, "")
            update_arrange()
            return format_success_response(message=f"成功重置音轨「{track_name}」的ReaEQ参数。")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("重置ReaEQ", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_apply_eq_preset(track_name: str = "", preset_name: str = "") -> dict:
        """
        应用EQ预设。
        
        Args:
            track_name: 音轨名称
            preset_name: 预设名称（如"Vocal Boost", "Bass Cut", "Treble Boost", "Low Pass Filter", "High Pass Filter", "Midrange Cut"）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not preset_name:
            raise InvalidParameterError("preset_name", preset_name, "请提供有效的预设名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            fx_idx = _find_fx_by_name(track, "ReaEQ")
            if fx_idx < 0:
                raise OperationFailedError(
                    "应用EQ预设",
                    "音轨上没有找到ReaEQ插件。请先使用reaper_add_reaeq添加。"
                )
            
            presets = {
                "Vocal Boost": [
                    (0, 100, -3.0, 1.4, 1),
                    (1, 200, -2.0, 2.0, 1),
                    (2, 2500, 3.0, 1.0, 0),
                    (3, 5000, 2.0, 1.4, 0),
                    (4, 8000, 4.0, 1.0, 2),
                    (5, 12000, 2.0, 1.0, 2)
                ],
                "Bass Cut": [
                    (0, 80, -12.0, 1.0, 3),
                    (1, 0, 0, 1, 0),
                    (2, 0, 0, 1, 0),
                    (3, 0, 0, 1, 0),
                    (4, 0, 0, 1, 0),
                    (5, 0, 0, 1, 0)
                ],
                "Treble Boost": [
                    (0, 0, 0, 1, 0),
                    (1, 0, 0, 1, 0),
                    (2, 0, 0, 1, 0),
                    (3, 0, 0, 1, 0),
                    (4, 8000, 6.0, 1.0, 2),
                    (5, 12000, 4.0, 1.0, 2)
                ],
                "Low Pass Filter": [
                    (0, 2000, 0, 1.0, 3),
                    (1, 0, 0, 1, 0),
                    (2, 0, 0, 1, 0),
                    (3, 0, 0, 1, 0),
                    (4, 0, 0, 1, 0),
                    (5, 0, 0, 1, 0)
                ],
                "High Pass Filter": [
                    (0, 80, 0, 1.0, 4),
                    (1, 0, 0, 1, 0),
                    (2, 0, 0, 1, 0),
                    (3, 0, 0, 1, 0),
                    (4, 0, 0, 1, 0),
                    (5, 0, 0, 1, 0)
                ],
                "Midrange Cut": [
                    (0, 0, 0, 1, 0),
                    (1, 0, 0, 1, 0),
                    (2, 1000, -6.0, 2.0, 0),
                    (3, 2000, -4.0, 1.4, 0),
                    (4, 0, 0, 1, 0),
                    (5, 0, 0, 1, 0)
                ]
            }
            
            if preset_name not in presets:
                raise InvalidParameterError(
                    "preset_name", preset_name,
                    f"可用预设：{list(presets.keys())}"
                )
            
            for band_idx, freq, gain, q, ftype in presets[preset_name]:
                band_offset = band_idx * 5
                reaper.TrackFX_SetParam(track, fx_idx, band_offset, freq)
                reaper.TrackFX_SetParam(track, fx_idx, band_offset + 1, gain)
                reaper.TrackFX_SetParam(track, fx_idx, band_offset + 2, q)
                reaper.TrackFX_SetParam(track, fx_idx, band_offset + 4, ftype)
            
            update_arrange()
            return format_success_response(message=f"成功应用EQ预设「{preset_name}」。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("应用EQ预设", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_reacomp(track_name: str = "") -> dict:
        """
        为音轨添加ReaComp压缩器。
        
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
            fx_idx = reaper.TrackFX_AddByName(track, "ReaComp", False, -1)
            if fx_idx >= 0:
                update_arrange()
                return format_success_response(message=f"成功为音轨「{track_name}」添加ReaComp压缩器。")
            else:
                raise OperationFailedError("添加ReaComp", "ReaComp插件未找到，请确保Reaper已正确安装")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("添加ReaComp", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_reacomp_params(track_name: str = "", threshold_db: float = -18.0, ratio: float = 4.0, attack_ms: float = 10.0, release_ms: float = 100.0, knee_db: float = 3.0) -> dict:
        """
        设置ReaComp压缩器参数。
        
        Args:
            track_name: 音轨名称
            threshold_db: 阈值（dB），有效值范围：[-60, 0]
            ratio: 压缩比（如2.0, 4.0, 8.0），有效值范围：[1.0, 100.0]
            attack_ms: 攻击时间（毫秒），有效值范围：[0.01, 1000]
            release_ms: 释放时间（毫秒），有效值范围：[1, 5000]
            knee_db: 拐点（dB），有效值范围：[0, 20]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if threshold_db < -60 or threshold_db > 0:
            raise InvalidParameterError("threshold_db", threshold_db, "有效值范围：[-60, 0]")
        
        if ratio < 1.0 or ratio > 100.0:
            raise InvalidParameterError("ratio", ratio, "有效值范围：[1.0, 100.0]")
        
        if attack_ms < 0.01 or attack_ms > 1000:
            raise InvalidParameterError("attack_ms", attack_ms, "有效值范围：[0.01, 1000]")
        
        if release_ms < 1 or release_ms > 5000:
            raise InvalidParameterError("release_ms", release_ms, "有效值范围：[1, 5000]")
        
        if knee_db < 0 or knee_db > 20:
            raise InvalidParameterError("knee_db", knee_db, "有效值范围：[0, 20]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            fx_idx = _find_fx_by_name(track, "ReaComp")
            if fx_idx < 0:
                raise OperationFailedError(
                    "设置ReaComp参数",
                    "音轨上没有找到ReaComp插件。请先使用reaper_add_reacomp添加。"
                )
            
            reaper.TrackFX_SetParam(track, fx_idx, 0, threshold_db)
            reaper.TrackFX_SetParam(track, fx_idx, 1, ratio)
            reaper.TrackFX_SetParam(track, fx_idx, 2, attack_ms)
            reaper.TrackFX_SetParam(track, fx_idx, 3, release_ms)
            reaper.TrackFX_SetParam(track, fx_idx, 4, knee_db)
            update_arrange()
            
            return format_success_response(
                message=f"成功设置ReaComp参数：阈值{threshold_db}dB，压缩比{ratio}:1，攻击{attack_ms}ms，释放{release_ms}ms，拐点{knee_db}dB。"
            )
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("设置ReaComp参数", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_reafir(track_name: str = "") -> dict:
        """
        为音轨添加ReaFIR均衡器（高精度FIR滤波器）。
        
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
            fx_idx = reaper.TrackFX_AddByName(track, "ReaFIR", False, -1)
            if fx_idx >= 0:
                update_arrange()
                return format_success_response(message=f"成功为音轨「{track_name}」添加ReaFIR均衡器。")
            else:
                raise OperationFailedError("添加ReaFIR", "ReaFIR插件未找到，请确保Reaper已正确安装")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("添加ReaFIR", str(e))

def _find_fx_by_name(track, fx_name):
    """辅助函数：根据名称查找FX插件索引"""
    from reapy import reascript_api as reaper
    num_fx = reaper.TrackFX_GetCount(track)
    for i in range(num_fx):
        retval, name = reaper.TrackFX_GetFXName(track, i, "", 256)
        if fx_name in name:
            return i
    return -1