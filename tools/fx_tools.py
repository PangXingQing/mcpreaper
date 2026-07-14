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
            from reapy import reascript_api as reaper
            fx_index = reaper.TrackFX_AddByName(track, fx_name, False, -1)
            if fx_index >= 0:
                update_arrange()
                return format_success_response(message=f"成功为音轨「{track_name}」添加FX插件「{fx_name}」。")
            else:
                raise OperationFailedError(
                    "添加FX插件",
                    f"插件名称不正确或插件不存在：{fx_name}\n提示：请确保插件名称与Reaper中显示的完全一致"
                )
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
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
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
            from reapy import reascript_api as reaper
            fx_list = []
            num_fx = reaper.TrackFX_GetCount(track)
            for i in range(num_fx):
                retval, fx_name = reaper.TrackFX_GetFXName(track, i, "", 256)
                enabled = bool(reaper.TrackFX_GetEnabled(track, i))
                num_params = reaper.TrackFX_GetNumParams(track, i)
                fx_list.append({
                    "index": i,
                    "name": fx_name,
                    "enabled": enabled,
                    "num_params": num_params
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
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            current_state = reaper.TrackFX_GetEnabled(track, fx_index)
            reaper.TrackFX_SetEnabled(track, fx_index, not current_state)
            update_arrange()
            
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            status = "启用" if not current_state else "禁用"
            return format_success_response(message=f"成功{status}FX插件「{fx_name}」。")
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
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            num_params = reaper.TrackFX_GetNumParams(track, fx_index)
            if param_index >= num_params:
                raise InvalidParameterError(
                    "param_index", param_index,
                    f"有效值范围：[0, {num_params-1}]，该FX插件共有{num_params}个参数"
                )
            
            reaper.TrackFX_SetParamNormalized(track, fx_index, param_index, value)
            update_arrange()
            
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            retval2, param_name = reaper.TrackFX_GetParamName(track, fx_index, param_index, "", 256)
            return format_success_response(message=f"成功设置FX「{fx_name}」参数「{param_name}」为{value}。")
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
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index >= num_fx:
                raise InvalidParameterError(
                    "fx_index", fx_index,
                    f"有效值范围：[0, {num_fx-1}]，该音轨共有{num_fx}个FX插件"
                )
            
            params = []
            num_params = reaper.TrackFX_GetNumParams(track, fx_index)
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            
            for i in range(num_params):
                retval2, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "", 256)
                param_value = reaper.TrackFX_GetParamNormalized(track, fx_index, i)
                retval3, param_label = reaper.TrackFX_GetParamLabel(track, fx_index, i, "", 256)
                params.append({
                    "index": i,
                    "name": param_name,
                    "value": param_value,
                    "label": param_label
                })
            
            return format_success_response(data={"fx_name": fx_name, "params": params, "num_params": num_params})
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