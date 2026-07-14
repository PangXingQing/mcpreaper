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

def register_send_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_track_send(source_track_name: str = "", destination_track_name: str = "") -> dict:
        """
        在两个音轨之间创建发送。
        
        Args:
            source_track_name: 源音轨名称
            destination_track_name: 目标音轨名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not source_track_name:
            raise InvalidParameterError("source_track_name", source_track_name, "请提供有效的源音轨名称")
        
        if not destination_track_name:
            raise InvalidParameterError("destination_track_name", destination_track_name, "请提供有效的目标音轨名称")
        
        if source_track_name == destination_track_name:
            raise InvalidParameterError("destination_track_name", destination_track_name, "源音轨和目标音轨不能相同")
        
        source_track = get_track_by_name(source_track_name)
        if source_track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(source_track_name, available_tracks)
        
        dest_track = get_track_by_name(destination_track_name)
        if dest_track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(destination_track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            send_idx = reaper.CreateTrackSend(source_track, dest_track)
            if send_idx >= 0:
                update_arrange()
                return format_success_response(
                    message=f"成功在音轨「{source_track_name}」和「{destination_track_name}」之间创建发送（索引：{send_idx}）。"
                )
            else:
                raise OperationFailedError("创建发送", "无法创建发送，请检查音轨状态")
        except OperationFailedError:
            raise
        except Exception as e:
            raise OperationFailedError("创建发送", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_track_send(track_name: str = "", send_index: int = 0) -> dict:
        """
        删除音轨的指定发送。
        
        Args:
            track_name: 音轨名称
            send_index: 发送索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if send_index < 0:
            raise InvalidParameterError("send_index", send_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_sends = reaper.GetTrackNumSends(track, 0)
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            reaper.RemoveTrackSend(track, 0, send_index)
            update_arrange()
            return format_success_response(message=f"成功删除音轨「{track_name}」的第{send_index}个发送。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("删除发送", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_sends(track_name: str = "") -> dict:
        """
        获取音轨的所有发送信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            发送信息字典，包含success字段和sends数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            sends = []
            num_sends = reaper.GetTrackNumSends(track, 0)
            
            for i in range(num_sends):
                dest_track = reaper.GetTrackSendInfo_Value(track, 0, i, "P_DESTTRACK")
                retval, dest_name = reaper.GetTrackName(dest_track, "", 256)
                send_vol = reaper.GetTrackSendInfo_Value(track, 0, i, "D_VOL")
                send_pan = reaper.GetTrackSendInfo_Value(track, 0, i, "D_PAN")
                sends.append({
                    "index": i,
                    "destination_track": dest_name,
                    "volume": send_vol,
                    "pan": send_pan
                })
            
            return format_success_response(data={"sends": sends, "count": len(sends)})
        except Exception as e:
            raise OperationFailedError("获取发送信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_send_volume(track_name: str = "", send_index: int = 0, volume: float = 1.0) -> dict:
        """
        设置发送音量。
        
        Args:
            track_name: 音轨名称
            send_index: 发送索引（从0开始，>= 0）
            volume: 音量值（线性值，范围[0, 4]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if send_index < 0:
            raise InvalidParameterError("send_index", send_index, "有效值范围：>= 0")
        
        if volume < 0 or volume > 4:
            raise InvalidParameterError("volume", volume, "有效值范围：[0, 4]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_sends = reaper.GetTrackNumSends(track, 0)
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            reaper.SetTrackSendInfo_Value(track, 0, send_index, "D_VOL", volume)
            update_arrange()
            
            db_value = 20 * (volume ** (1/10)) if volume > 0 else "-inf"
            return format_success_response(message=f"成功设置发送音量为{volume}（约{db_value}dB）。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("设置发送音量", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_send_pan(track_name: str = "", send_index: int = 0, pan: float = 0.0) -> dict:
        """
        设置发送声相。
        
        Args:
            track_name: 音轨名称
            send_index: 发送索引（从0开始，>= 0）
            pan: 声相值（范围[-1, 1]，-1=左，0=中，1=右）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if send_index < 0:
            raise InvalidParameterError("send_index", send_index, "有效值范围：>= 0")
        
        if pan < -1 or pan > 1:
            raise InvalidParameterError("pan", pan, "有效值范围：[-1, 1]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_sends = reaper.GetTrackNumSends(track, 0)
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            reaper.SetTrackSendInfo_Value(track, 0, send_index, "D_PAN", pan)
            update_arrange()
            
            pan_label = "左" if pan < -0.1 else ("右" if pan > 0.1 else "中")
            return format_success_response(message=f"成功设置发送声相为{pan}（{pan_label}）。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("设置发送声相", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_receives(track_name: str = "") -> dict:
        """
        获取音轨的所有接收信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            接收信息字典，包含success字段和receives数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            receives = []
            num_receives = reaper.GetTrackNumSends(track, 1)
            
            for i in range(num_receives):
                source_track = reaper.GetTrackSendInfo_Value(track, 1, i, "P_DESTTRACK")
                retval, source_name = reaper.GetTrackName(source_track, "", 256)
                receive_vol = reaper.GetTrackSendInfo_Value(track, 1, i, "D_VOL")
                receive_pan = reaper.GetTrackSendInfo_Value(track, 1, i, "D_PAN")
                receives.append({
                    "index": i,
                    "source_track": source_name,
                    "volume": receive_vol,
                    "pan": receive_pan
                })
            
            return format_success_response(data={"receives": receives, "count": len(receives)})
        except Exception as e:
            raise OperationFailedError("获取接收信息", str(e))