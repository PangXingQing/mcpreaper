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

def register_midi_ext_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_midi_cc(track_name: str = "", item_index: int = 0, cc_number: int = 1, position_ppq: int = 0, value: int = 64, channel: int = 0) -> dict:
        """
        在MIDI项目项中插入CC事件。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            cc_number: CC控制号（0-127）
            position_ppq: 位置（PPQ）
            value: CC值（0-127）
            channel: MIDI通道（0-15）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if cc_number < 0 or cc_number > 127:
            raise InvalidParameterError("cc_number", cc_number, "有效值范围：[0, 127]")
        
        if value < 0 or value > 127:
            raise InvalidParameterError("value", value, "有效值范围：[0, 127]")
        
        if channel < 0 or channel > 15:
            raise InvalidParameterError("channel", channel, "有效值范围：[0, 15]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("插入CC事件", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("插入CC事件", "该项目项不是MIDI类型")
            
            reaper.MIDI_InsertCC(take, False, False, position_ppq, cc_number, channel, value)
            update_arrange()
            
            cc_names = {1: "调制轮", 7: "音量", 10: "声相", 11: "表情", 64: "延音踏板", 65: "滑音", 91: "混响", 93: "合唱"}
            cc_name = cc_names.get(cc_number, f"CC{cc_number}")
            
            return format_success_response(message=f"成功插入{cc_name}事件，值{value}。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("插入CC事件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_midi_cc_events(track_name: str = "", item_index: int = 0) -> dict:
        """
        获取MIDI项目项中的所有CC事件。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            CC事件信息字典，包含success字段和cc_events数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("获取CC事件", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("获取CC事件", "该项目项不是MIDI类型")
            
            retval, _, cc_events_count, _ = reaper.MIDI_CountEvts(take)
            events = []
            
            cc_names = {1: "调制轮", 7: "音量", 10: "声相", 11: "表情", 64: "延音踏板", 65: "滑音", 91: "混响", 93: "合唱"}
            
            for i in range(cc_events_count):
                retval2, selected, muted, position_ppq, chanmsg, chan, msg2, msg3 = reaper.MIDI_GetCC(take, i)
                cc_name = cc_names.get(msg2, f"CC{msg2}")
                
                events.append({
                    "index": i,
                    "cc_number": msg2,
                    "cc_name": cc_name,
                    "value": msg3,
                    "position_ppq": position_ppq,
                    "channel": chan,
                    "selected": bool(selected),
                    "muted": bool(muted)
                })
            
            return format_success_response(data={"cc_events": events, "count": len(events)})
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取CC事件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_midi_text_event(track_name: str = "", item_index: int = 0, position_ppq: int = 0, text: str = "", event_type: int = 1) -> dict:
        """
        在MIDI项目项中插入文本事件。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            position_ppq: 位置（PPQ）
            text: 文本内容
            event_type: 事件类型：1=文本, 2=歌词, 3=标记, 4=曲名, 5=版权, 6=作者
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if event_type < 1 or event_type > 6:
            raise InvalidParameterError("event_type", event_type, "有效值范围：[1, 6]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("插入文本事件", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("插入文本事件", "该项目项不是MIDI类型")
            
            reaper.MIDI_InsertTextSysexEvt(take, False, False, position_ppq, event_type, text)
            update_arrange()
            
            type_names = {1: "文本", 2: "歌词", 3: "标记", 4: "曲名", 5: "版权", 6: "作者"}
            return format_success_response(message=f"成功插入{type_names[event_type]}事件：{text}")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("插入文本事件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_midi_text_events(track_name: str = "", item_index: int = 0) -> dict:
        """
        获取MIDI项目项中的所有文本事件。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            文本事件信息字典，包含success字段和text_events数据列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("获取文本事件", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("获取文本事件", "该项目项不是MIDI类型")
            
            retval, _, _, text_events_count = reaper.MIDI_CountEvts(take)
            events = []
            
            type_names = {1: "文本", 2: "歌词", 3: "标记", 4: "曲名", 5: "版权", 6: "作者"}
            
            for i in range(text_events_count):
                retval2, selected, muted, position_ppq, evt_type, text = reaper.MIDI_GetTextSysexEvt(take, i)
                
                events.append({
                    "index": i,
                    "type": type_names.get(evt_type, f"未知({evt_type})"),
                    "text": text,
                    "position_ppq": position_ppq,
                    "selected": bool(selected),
                    "muted": bool(muted)
                })
            
            return format_success_response(data={"text_events": events, "count": len(events)})
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取文本事件", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_quantize_midi_notes(track_name: str = "", item_index: int = 0, grid_div: int = 16, strength: int = 100) -> dict:
        """
        量化MIDI音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            grid_div: 网格细分（如16=16分音符），有效值范围：[1, 128]
            strength: 量化强度（0-100%），有效值范围：[0, 100]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if grid_div < 1 or grid_div > 128:
            raise InvalidParameterError("grid_div", grid_div, "有效值范围：[1, 128]")
        
        if strength < 0 or strength > 100:
            raise InvalidParameterError("strength", strength, "有效值范围：[0, 100]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("量化MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("量化MIDI音符", "该项目项不是MIDI类型")
            
            item.select()
            reaper.MIDI_SetGrid(take, grid_div)
            reaper.Main_OnCommand(40455, 0)
            update_arrange()
            
            return format_success_response(message=f"成功量化MIDI音符，网格{grid_div}分音符，强度{strength}%。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("量化MIDI音符", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_transpose_midi_notes(track_name: str = "", item_index: int = 0, semitones: int = 0) -> dict:
        """
        移调MIDI音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            semitones: 移调半音数（正数升调，负数降调），有效值范围：[-120, 120]
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if semitones < -120 or semitones > 120:
            raise InvalidParameterError("semitones", semitones, "有效值范围：[-120, 120]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("移调MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("移调MIDI音符", "该项目项不是MIDI类型")
            
            reaper.MIDI_SelectAll(take, True)
            reaper.MIDI_Transpose(take, semitones, False)
            update_arrange()
            
            direction = "升调" if semitones > 0 else ("降调" if semitones < 0 else "保持")
            return format_success_response(message=f"成功{direction}MIDI音符{abs(semitones)}个半音。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("移调MIDI音符", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_midi_item_info(track_name: str = "", item_index: int = 0) -> dict:
        """
        获取MIDI项目项的详细信息。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            MIDI项目项信息字典，包含success字段和详细信息
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        if item_index >= len(track.items):
            raise InvalidParameterError(
                "item_index", item_index,
                f"有效值范围：[0, {len(track.items)-1}]，该音轨共有{len(track.items)}个项目项"
            )
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("获取MIDI项目项信息", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("获取MIDI项目项信息", "该项目项不是MIDI类型")
            
            retval, num_notes, num_cc, num_text = reaper.MIDI_CountEvts(take)
            
            return format_success_response(data={
                "num_notes": num_notes,
                "num_cc_events": num_cc,
                "num_text_events": num_text,
                "ppq_per_quarter": reaper.MIDI_GetPPQPos_StartOfMeasure(take, 0),
                "length_ppq": reaper.MIDI_GetPPQPos_EndOfMeasure(take, 0) - reaper.MIDI_GetPPQPos_StartOfMeasure(take, 0),
                "item_length_seconds": item.length
            })
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取MIDI项目项信息", str(e))