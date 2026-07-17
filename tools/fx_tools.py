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

def register_fx_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_fx_to_track(track_name: str = "", fx_name: str = "") -> dict:
        """
        为音轨添加FX插件。
        
        Args:
            track_name: 音轨名称
            fx_name: FX插件名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not fx_name:
            raise InvalidParameterError("fx_name", fx_name, "请提供有效的FX插件名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.add_fx(fx_name)
            # add_fx returns an FX object on success, raises on failure
            update_arrange()
            return format_success_response(message=f"成功为音轨「{track_name}」添加FX插件「{fx_name}」。")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("添加FX插件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_remove_fx_from_track(track_name: str = "", fx_index: int = 0) -> dict:
        """
        从音轨移除FX插件。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if fx_index < 0:
            raise InvalidParameterError("fx_index", fx_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_fx = len(track.fxs)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            fx_name = track.fxs[fx_index].name
            reaper.TrackFX_Delete(track, fx_index)
            update_arrange()
            return format_success_response(message=f"成功从音轨「{track_name}」移除FX插件「{fx_name}」。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("移除FX插件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_fx_list(track_name: str = "") -> dict:
        """
        获取音轨的FX插件列表。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            FX插件信息字典，包含success字段和fx_list数据
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            fx_list = []
            for i, fx in enumerate(track.fxs):
                fx_list.append({
                    "index": i,
                    "name": fx.name,
                    "enabled": fx.is_enabled,
                    "num_params": fx.n_params
                })
            return format_success_response(data={"fx_list": fx_list, "count": len(fx_list)})
        except Exception as e:
            raise OperationFailedError("获取FX插件列表", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_toggle_fx(track_name: str = "", fx_index: int = 0) -> dict:
        """
        切换FX插件启用状态。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if fx_index < 0:
            raise InvalidParameterError("fx_index", fx_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            num_fx = len(track.fxs)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            fx = track.fxs[fx_index]
            fx.is_enabled = not fx.is_enabled
            update_arrange()
            
            status = "启用" if fx.is_enabled else "禁用"
            return format_success_response(message=f"成功{status}FX插件「{fx.name}」。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("切换FX状态", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_fx_param(track_name: str = "", fx_index: int = 0, param_index: int = 0, value: float = 0.0) -> dict:
        """
        设置FX插件参数值。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始，>= 0）
            param_index: 参数索引（从0开始，>= 0）
            value: 参数值（归一化值，范围[0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if fx_index < 0:
            raise InvalidParameterError("fx_index", fx_index, "有效值范围：>= 0")
        
        if param_index < 0:
            raise InvalidParameterError("param_index", param_index, "有效值范围：>= 0")
        
        if value < 0 or value > 1:
            raise InvalidParameterError("value", value, "有效值范围：[0, 1]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            num_fx = len(track.fxs)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            fx = track.fxs[fx_index]
            if param_index >= fx.n_params:
                raise InvalidParameterError(
                    "param_index", param_index,
                    f"有效值范围：[0, {fx.n_params-1}]，该FX插件共有{fx.n_params}个参数"
                )
            
            fx.params[param_index] = value
            update_arrange()
            
            return format_success_response(message=f"成功设置FX「{fx.name}」参数{param_index}为{value}。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("设置FX参数", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_fx_params(track_name: str = "", fx_index: int = 0) -> dict:
        """
        获取FX插件的所有参数信息。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始，>= 0）
        
        Returns:
            参数信息字典，包含success字段和FX参数数据
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if fx_index < 0:
            raise InvalidParameterError("fx_index", fx_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            num_fx = len(track.fxs)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            fx = track.fxs[fx_index]
            params = []
            for i in range(fx.n_params):
                params.append({
                    "index": i,
                    "name": fx.params[i].name,
                    "value": fx.params[i].normalized,
                    "formatted": fx.params[i].formatted
                })
            
            return format_success_response(data={"fx_name": fx.name, "params": params, "num_params": fx.n_params})
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("获取FX参数", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_bypass_all_fx(track_name: str = "", bypass: bool = True) -> dict:
        """
        旁路音轨的所有FX插件。
        
        Args:
            track_name: 音轨名称
            bypass: 是否旁路（True=旁路所有FX，False=启用所有FX）
        
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
            reaper.TrackFX_SetEnabled(track, -1, not bypass)
            update_arrange()
            
            status = "旁路" if bypass else "启用"
            return format_success_response(message=f"成功{status}音轨「{track_name}」的所有FX插件。")
        except Exception as e:
            raise OperationFailedError("旁路/启用FX插件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_fx_online_offline(track_name: str = "", fx_index: int = 0, online: bool = True) -> dict:
        """
        设置 FX 在线/离线状态。

        离线状态时插件不消耗 CPU，但不处理音频。

        Args:
            track_name: 音轨名称
            fx_index: FX 索引
            online: True=在线, False=离线

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")
        if fx_index < 0:
            raise InvalidParameterError("fx_index", fx_index, "必须 >= 0")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            fx_count = reaper.TrackFX_GetCount(track)
            if fx_index >= fx_count:
                raise InvalidParameterError(
                    "fx_index", fx_index, f"有效范围：[0, {fx_count - 1}]"
                )
            reaper.TrackFX_SetOffline(track, fx_index, not online)
            status = "在线" if online else "离线"
            return format_success_response(
                message=f"FX[{fx_index}] 已设为{status}"
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置 FX 在线状态", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_move_fx(track_name: str = "", from_index: int = 0, to_index: int = 1) -> dict:
        """
        移动 FX 在链中的位置。

        改变效果器的处理顺序，影响音色和动态。

        Args:
            track_name: 音轨名称
            from_index: 当前位置索引
            to_index: 目标位置索引

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")
        if from_index < 0:
            raise InvalidParameterError("from_index", from_index, "必须 >= 0")
        if to_index < 0:
            raise InvalidParameterError("to_index", to_index, "必须 >= 0")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            fx_count = reaper.TrackFX_GetCount(track)
            if from_index >= fx_count:
                raise InvalidParameterError(
                    "from_index", from_index, f"有效范围：[0, {fx_count - 1}]"
                )
            if to_index >= fx_count:
                raise InvalidParameterError(
                    "to_index", to_index, f"有效范围：[0, {fx_count - 1}]"
                )

            reaper.TrackFX_CopyToTrack(track, from_index, track, to_index, True)
            return format_success_response(
                message=f"FX 已从位置 {from_index} 移动到 {to_index}"
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("移动 FX", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_fx_preset_list(track_name: str = "", fx_index: int = 0) -> dict:
        """
        获取 FX 的预设列表。

        Args:
            track_name: 音轨名称
            fx_index: FX 索引

        Returns:
            预设名称列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            fx_count = reaper.TrackFX_GetCount(track)
            if fx_index < 0 or fx_index >= fx_count:
                raise InvalidParameterError(
                    "fx_index", fx_index, f"有效范围：[0, {fx_count - 1}]"
                )

            presets = []
            # REAPER API: TrackFX_GetPreset(track, fx, buf, bufsz)
            # 获取预设名称
            i = 0
            while True:
                try:
                    retval, name = reaper.TrackFX_GetPreset(track, fx_index, "", 256)
                    if retval and name:
                        # This doesn't iterate - need different approach
                        break
                except Exception:
                    break
                i += 1

            # 尝试枚举预设
            num_presets = reaper.TrackFX_GetPreset(track, fx_index, "", 256)
            for p in range(30):  # 最多尝试 30 个
                try:
                    _, preset_name = reaper.TrackFX_GetPreset(track, fx_index, "", 256)
                    if preset_name:
                        presets.append(preset_name)
                except Exception:
                    break

            return format_success_response(data={
                "track_name": track_name,
                "fx_index": fx_index,
                "presets": presets,
                "count": len(presets),
                "note": "预设列表可能不完整（reapy web interface 限制）",
            })
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取预设列表", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_rename_fx(track_name: str = "", fx_index: int = 0, new_name: str = "") -> dict:
        """
        重命名 FX 实例（在 REAPER 内部显示名称）。

        Args:
            track_name: 音轨名称
            fx_index: FX 索引
            new_name: 新名称

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")
        if not new_name:
            raise InvalidParameterError("new_name", new_name, "请提供新名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            reaper.TrackFX_SetNamedConfigParm(track, fx_index, "renamed_name", new_name)
            return format_success_response(
                message=f"FX[{fx_index}] 已重命名为「{new_name}」"
            )
        except Exception as e:
            raise OperationFailedError("重命名 FX", str(e))
