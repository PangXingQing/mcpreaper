from mcp.server.fastmcp import FastMCP
from utils.reaper_client import get_track_by_name, update_arrange

def register_fx_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_add_fx_to_track(track_name: str = "", fx_name: str = "") -> str:
        """
        为音轨添加FX插件。
        
        Args:
            track_name: 音轨名称
            fx_name: FX插件名称
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            from reapy import reascript_api as reaper
            fx_index = reaper.TrackFX_AddByName(track, fx_name, False, -1)
            if fx_index >= 0:
                update_arrange()
                return f"成功为音轨「{track_name}」添加FX插件「{fx_name}」。"
            else:
                return f"添加FX插件失败，可能插件名称不正确：{fx_name}"
        except Exception as e:
            return f"添加FX插件失败：{e}"

    @mcp.tool()
    def reaper_remove_fx_from_track(track_name: str = "", fx_index: int = 0) -> str:
        """
        从音轨移除FX插件。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index < 0 or fx_index >= num_fx:
                return f"FX索引无效：{fx_index}，范围应为[0, {num_fx-1}]。"
            reaper.TrackFX_Delete(track, fx_index)
            update_arrange()
            return f"成功从音轨「{track_name}」移除第{fx_index}个FX插件。"
        except Exception as e:
            return f"移除FX插件失败：{e}"

    @mcp.tool()
    def reaper_get_track_fx_list(track_name: str = "") -> list[dict]:
        """
        获取音轨的FX插件列表。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            FX插件信息列表
        """
        track = get_track_by_name(track_name)
        if track is None:
            return [{"error": f"没有找到音轨「{track_name}」。"}]
        try:
            from reapy import reascript_api as reaper
            fx_list = []
            num_fx = reaper.TrackFX_GetCount(track)
            for i in range(num_fx):
                retval, fx_name = reaper.TrackFX_GetFXName(track, i, "", 256)
                enabled = reaper.TrackFX_GetEnabled(track, i)
                fx_list.append({
                    "index": i,
                    "name": fx_name,
                    "enabled": bool(enabled)
                })
            return fx_list
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_toggle_fx(track_name: str = "", fx_index: int = 0) -> str:
        """
        切换FX插件启用状态。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index < 0 or fx_index >= num_fx:
                return f"FX索引无效：{fx_index}，范围应为[0, {num_fx-1}]。"
            current_state = reaper.TrackFX_GetEnabled(track, fx_index)
            reaper.TrackFX_SetEnabled(track, fx_index, not current_state)
            update_arrange()
            status = "启用" if not current_state else "禁用"
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            return f"成功{status}FX插件「{fx_name}」。"
        except Exception as e:
            return f"切换FX状态失败：{e}"

    @mcp.tool()
    def reaper_set_fx_param(track_name: str = "", fx_index: int = 0, param_index: int = 0, value: float = 0.0) -> str:
        """
        设置FX插件参数值。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始）
            param_index: 参数索引（从0开始）
            value: 参数值（归一化值，0.0-1.0）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if value < 0 or value > 1:
            return f"参数值无效：{value}，范围应为[0, 1]。"
        try:
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index < 0 or fx_index >= num_fx:
                return f"FX索引无效：{fx_index}，范围应为[0, {num_fx-1}]。"
            num_params = reaper.TrackFX_GetNumParams(track, fx_index)
            if param_index < 0 or param_index >= num_params:
                return f"参数索引无效：{param_index}，范围应为[0, {num_params-1}]。"
            reaper.TrackFX_SetParamNormalized(track, fx_index, param_index, value)
            update_arrange()
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            retval2, param_name = reaper.TrackFX_GetParamName(track, fx_index, param_index, "", 256)
            return f"成功设置FX「{fx_name}」参数「{param_name}」为{value}。"
        except Exception as e:
            return f"设置FX参数失败：{e}"

    @mcp.tool()
    def reaper_get_fx_params(track_name: str = "", fx_index: int = 0) -> list[dict]:
        """
        获取FX插件的所有参数信息。
        
        Args:
            track_name: 音轨名称
            fx_index: FX插件索引（从0开始）
        
        Returns:
            参数信息列表
        """
        track = get_track_by_name(track_name)
        if track is None:
            return [{"error": f"没有找到音轨「{track_name}」。"}]
        try:
            from reapy import reascript_api as reaper
            num_fx = reaper.TrackFX_GetCount(track)
            if fx_index < 0 or fx_index >= num_fx:
                return [{"error": f"FX索引无效：{fx_index}，范围应为[0, {num_fx-1}]。"}]
            params = []
            num_params = reaper.TrackFX_GetNumParams(track, fx_index)
            retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "", 256)
            for i in range(num_params):
                retval2, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "", 256)
                param_value = reaper.TrackFX_GetParamNormalized(track, fx_index, i)
                params.append({
                    "index": i,
                    "name": param_name,
                    "value": param_value
                })
            return {
                "fx_name": fx_name,
                "params": params
            }
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_bypass_all_fx(track_name: str = "", bypass: bool = True) -> str:
        """
        旁路音轨的所有FX插件。
        
        Args:
            track_name: 音轨名称
            bypass: 是否旁路
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        try:
            from reapy import reascript_api as reaper
            reaper.TrackFX_SetEnabled(track, -1, not bypass)
            update_arrange()
            status = "旁路" if bypass else "启用"
            return f"成功{status}音轨「{track_name}」的所有FX插件。"
        except Exception as e:
            return f"操作失败：{e}"