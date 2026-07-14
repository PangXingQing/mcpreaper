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

def register_envelope_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_envelopes(track_name: str = "") -> dict:
        """
        获取音轨的所有包络信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            包络信息字典，包含success字段和envelopes数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            envelopes = []
            num_envelopes = reaper.CountTrackEnvelopes(track)
            for i in range(num_envelopes):
                env = reaper.GetTrackEnvelope(track, i)
                retval, env_name = reaper.GetEnvelopeName(env, "", 256)
                envelopes.append({
                    "index": i,
                    "name": env_name,
                    "num_points": reaper.CountEnvelopePoints(env)
                })
            return format_success_response(data={"envelopes": envelopes, "count": len(envelopes)})
        except Exception as e:
            raise OperationFailedError("获取包络信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_envelope_point(track_name: str = "", envelope_index: int = 0, time: float = 0.0, value: float = 0.0, shape: int = 0) -> dict:
        """
        在包络上添加控制点。
        
        Args:
            track_name: 音轨名称
            envelope_index: 包络索引（从0开始，>= 0）
            time: 时间位置（秒，>= 0）
            value: 包络值（归一化值，范围[0, 1]）
            shape: 曲线形状：0=线性, 1=对数, 2=指数, 3=s形, 4=余弦（有效值范围：[0, 4]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if envelope_index < 0:
            raise InvalidParameterError("envelope_index", envelope_index, "有效值范围：>= 0")
        
        if time < 0:
            raise InvalidParameterError("time", time, "有效值范围：>= 0")
        
        if value < 0 or value > 1:
            raise InvalidParameterError("value", value, "有效值范围：[0, 1]")
        
        if shape < 0 or shape > 4:
            raise InvalidParameterError("shape", shape, "有效值范围：[0, 4]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_envelopes = reaper.CountTrackEnvelopes(track)
            if envelope_index >= num_envelopes:
                raise InvalidParameterError(
                    "envelope_index", envelope_index,
                    f"有效值范围：[0, {num_envelopes-1}]，该音轨共有{num_envelopes}个包络"
                )
            
            env = reaper.GetTrackEnvelope(track, envelope_index)
            reaper.InsertEnvelopePoint(env, time, value, shape, 0, False)
            reaper.Envelope_SortPoints(env)
            update_arrange()
            
            retval, env_name = reaper.GetEnvelopeName(env, "", 256)
            return format_success_response(message=f"成功在包络「{env_name}」的{time}秒处添加控制点，值为{value}。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("添加包络控制点", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_envelope_point(track_name: str = "", envelope_index: int = 0, point_index: int = 0) -> dict:
        """
        删除包络控制点。
        
        Args:
            track_name: 音轨名称
            envelope_index: 包络索引（从0开始，>= 0）
            point_index: 控制点索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if envelope_index < 0:
            raise InvalidParameterError("envelope_index", envelope_index, "有效值范围：>= 0")
        
        if point_index < 0:
            raise InvalidParameterError("point_index", point_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_envelopes = reaper.CountTrackEnvelopes(track)
            if envelope_index >= num_envelopes:
                raise InvalidParameterError(
                    "envelope_index", envelope_index,
                    f"有效值范围：[0, {num_envelopes-1}]，该音轨共有{num_envelopes}个包络"
                )
            
            env = reaper.GetTrackEnvelope(track, envelope_index)
            num_points = reaper.CountEnvelopePoints(env)
            if point_index >= num_points:
                raise InvalidParameterError(
                    "point_index", point_index,
                    f"有效值范围：[0, {num_points-1}]，该包络共有{num_points}个控制点"
                )
            
            reaper.DeleteEnvelopePointRange(env, 0, 0, point_index, False)
            update_arrange()
            
            retval, env_name = reaper.GetEnvelopeName(env, "", 256)
            return format_success_response(message=f"成功删除包络「{env_name}」的控制点（索引：{point_index}）。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("删除包络控制点", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_envelope_points(track_name: str = "", envelope_index: int = 0) -> dict:
        """
        获取包络的所有控制点。
        
        Args:
            track_name: 音轨名称
            envelope_index: 包络索引（从0开始，>= 0）
        
        Returns:
            控制点信息字典，包含success字段和points数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if envelope_index < 0:
            raise InvalidParameterError("envelope_index", envelope_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_envelopes = reaper.CountTrackEnvelopes(track)
            if envelope_index >= num_envelopes:
                raise InvalidParameterError(
                    "envelope_index", envelope_index,
                    f"有效值范围：[0, {num_envelopes-1}]，该音轨共有{num_envelopes}个包络"
                )
            
            env = reaper.GetTrackEnvelope(track, envelope_index)
            points = []
            num_points = reaper.CountEnvelopePoints(env)
            
            for i in range(num_points):
                retval, time, value, shape, tension = reaper.GetEnvelopePoint(env, i)
                points.append({
                    "index": i,
                    "time": time,
                    "value": value,
                    "shape": shape,
                    "tension": tension
                })
            
            retval, env_name = reaper.GetEnvelopeName(env, "", 256)
            return format_success_response(data={"envelope_name": env_name, "points": points, "count": len(points)})
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("获取包络控制点", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_envelope_value_at_time(track_name: str = "", envelope_index: int = 0, time: float = 0.0) -> dict:
        """
        获取包络在指定时间点的值。
        
        Args:
            track_name: 音轨名称
            envelope_index: 包络索引（从0开始，>= 0）
            time: 时间位置（秒，>= 0）
        
        Returns:
            包络值字典，包含success字段和time、value数据
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if envelope_index < 0:
            raise InvalidParameterError("envelope_index", envelope_index, "有效值范围：>= 0")
        
        if time < 0:
            raise InvalidParameterError("time", time, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_envelopes = reaper.CountTrackEnvelopes(track)
            if envelope_index >= num_envelopes:
                raise InvalidParameterError(
                    "envelope_index", envelope_index,
                    f"有效值范围：[0, {num_envelopes-1}]，该音轨共有{num_envelopes}个包络"
                )
            
            env = reaper.GetTrackEnvelope(track, envelope_index)
            retval, value = reaper.Envelope_Evaluate(env, time, 0, 0)
            
            retval2, env_name = reaper.GetEnvelopeName(env, "", 256)
            return format_success_response(data={"envelope_name": env_name, "time": time, "value": value})
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("获取包络值", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_clear_envelope_points(track_name: str = "", envelope_index: int = 0) -> dict:
        """
        清空包络的所有控制点。
        
        Args:
            track_name: 音轨名称
            envelope_index: 包络索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if envelope_index < 0:
            raise InvalidParameterError("envelope_index", envelope_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            num_envelopes = reaper.CountTrackEnvelopes(track)
            if envelope_index >= num_envelopes:
                raise InvalidParameterError(
                    "envelope_index", envelope_index,
                    f"有效值范围：[0, {num_envelopes-1}]，该音轨共有{num_envelopes}个包络"
                )
            
            env = reaper.GetTrackEnvelope(track, envelope_index)
            num_points = reaper.CountEnvelopePoints(env)
            
            for i in range(num_points - 1, -1, -1):
                reaper.DeleteEnvelopePointRange(env, 0, 0, i, False)
            
            update_arrange()
            
            retval, env_name = reaper.GetEnvelopeName(env, "", 256)
            return format_success_response(message=f"成功清空包络「{env_name}」的所有控制点。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("清空包络控制点", str(e))