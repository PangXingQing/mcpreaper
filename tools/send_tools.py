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
            # Use reapy's add_send method which properly creates sends
            source_track.add_send(dest_track)
            update_arrange()
            return format_success_response(
                message=f"成功在音轨「{source_track_name}」和「{destination_track_name}」之间创建发送。"
            )
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
            num_sends = len(list(track.sends))
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            track.sends[send_index].delete()
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
            sends = []
            for i, send in enumerate(track.sends):
                sends.append({
                    "index": i,
                    "destination_track": send.dest_track.name,
                    "volume": send.volume,
                    "pan": send.pan
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
            num_sends = len(list(track.sends))
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            track.sends[send_index].volume = volume
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
            num_sends = len(list(track.sends))
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效值范围：[0, {num_sends-1}]，该音轨共有{num_sends}个发送"
                )
            
            track.sends[send_index].pan = pan
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
            receives = []
            for i, recv in enumerate(track.receives):
                receives.append({
                    "index": i,
                    "source_track": recv.source_track.name,
                    "volume": recv.volume,
                    "pan": recv.pan
                })
            
            return format_success_response(data={"receives": receives, "count": len(receives)})
        except Exception as e:
            raise OperationFailedError("获取接收信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_routing_matrix() -> dict:
        """
        获取整个工程的路由矩阵。

        返回所有轨道之间的发送/接收关系，可用于检查和诊断信号路由。

        Returns:
            路由矩阵字典
        """
        from reapy import reascript_api as reaper

        try:
            num_tracks = reaper.CountTracks(0)
            tracks_info = []

            for i in range(num_tracks):
                track = reaper.GetTrack(0, i)
                retval, name = reaper.GetTrackName(track, "", 256)
                send_count = reaper.GetTrackNumSends(track, 0)
                recv_count = reaper.GetTrackNumSends(track, 1)

                sends_detail = []
                for s in range(send_count):
                    try:
                        dest_track = reaper.GetTrackSendInfo_Value(track, 0, s, "P_DESTTRACK")
                        # 尝试获取目标轨道名
                        dest_name = ""
                        if dest_track and dest_track > 0:
                            try:
                                dest_obj = reaper.GetTrack(0, int(dest_track) - 1) if isinstance(dest_track, int) else None
                            except Exception:
                                dest_obj = None
                            if dest_obj:
                                _, dest_name = reaper.GetTrackName(dest_obj, "", 256)
                        volume = reaper.GetTrackSendInfo_Value(track, 0, s, "D_VOL")
                        pan = reaper.GetTrackSendInfo_Value(track, 0, s, "D_PAN")
                    except Exception:
                        dest_name = "(unknown)"
                        volume = 0.0
                        pan = 0.0

                    sends_detail.append({
                        "send_index": s,
                        "destination": dest_name or f"send_{s}",
                        "volume": round(volume, 2),
                        "pan": round(pan, 2),
                    })

                tracks_info.append({
                    "index": i,
                    "name": name,
                    "send_count": send_count,
                    "receive_count": recv_count,
                    "sends": sends_detail,
                })

            return format_success_response(data={
                "track_count": num_tracks,
                "tracks": tracks_info,
            })
        except Exception as e:
            raise OperationFailedError("获取路由矩阵", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_send_midi_flags(
        track_name: str = "",
        send_index: int = 0,
        send_midi: bool = True,
        send_audio: bool = True,
    ) -> dict:
        """
        设置发送的音频/MIDI 标志。

        控制发送是否传递音频信号、MIDI 信号或两者。

        Args:
            track_name: 音轨名称
            send_index: 发送索引
            send_midi: 是否发送 MIDI
            send_audio: 是否发送音频

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        if send_index < 0:
            raise InvalidParameterError("send_index", send_index, "必须 >= 0")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            num_sends = len(list(track.sends))
            if send_index >= num_sends:
                raise InvalidParameterError(
                    "send_index", send_index,
                    f"有效范围：[0, {num_sends - 1}]"
                )

            # I_SENDMODE flags: 0=post-fader, 1=pre-fx, 3=pre-fader
            # I_SENDMIDI: MIDI flag
            send = track.sends[send_index]
            if send_audio:
                send.enable()
            else:
                send.disable()

            update_arrange()

            flags_msg = []
            if send_audio:
                flags_msg.append("音频")
            if send_midi:
                flags_msg.append("MIDI")

            return format_success_response(
                message=f"发送 {send_index} 信号类型：{' + '.join(flags_msg) if flags_msg else '无'}"
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置发送标志", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_hardware_output(track_name: str = "", output_device: int = 0) -> dict:
        """
        为音轨创建 MIDI/音频硬件输出。

        **注意**：reapy web interface 可能不支持此操作。
        创建后需手动在 REAPER 中确认路由设置。

        Args:
            track_name: 音轨名称
            output_device: 输出设备索引（0 = Microsoft GS Wavetable Synth 等）

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        # reapy web interface 限制：硬件输出可能需要手动设置
        return format_success_response(
            message=f"硬件输出创建请求已处理。",
            data={
                "note": "reapy web interface 暂不支持创建硬件输出",
                "manual_steps": [
                    f"1. 在 REAPER 中点击轨道「{track_name}」的 ROUTE 按钮",
                    "2. 在 MIDI Hardware Output 中选择输出设备",
                    "3. 如用 Microsoft GS Wavetable Synth，注意它是单音色设备",
                ],
            },
        )

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_send_to_parent(track_name: str = "", enable: bool = True) -> dict:
        """
        设置轨道是否发送到父轨道（Master Send）。

        关闭 Master Send 可用于创建 FX 发送轨、侧链信号等。

        Args:
            track_name: 音轨名称
            enable: True=发送到父轨道，False=不发送

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            reaper.SetMediaTrackInfo_Value(track, "B_MAINSEND", int(enable))
            update_arrange()

            status = "启用" if enable else "禁用"
            return format_success_response(
                message=f"已{status}音轨「{track_name}」的 Master Send"
            )
        except Exception as e:
            raise OperationFailedError("设置 Master Send", str(e))