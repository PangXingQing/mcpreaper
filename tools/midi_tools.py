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

def register_midi_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_create_midi_item(track_name: str = "", start_time: float = 0.0, length: float = 1.0) -> dict:
        """
        创建MIDI项目项。
        
        Args:
            track_name: 目标音轨名称
            start_time: 开始时间（秒，>= 0）
            length: 长度（秒，> 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if start_time < 0:
            raise InvalidParameterError("start_time", start_time, "有效值范围：>= 0")
        
        if length <= 0:
            raise InvalidParameterError("length", length, "有效值范围：> 0")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            reaper.CreateNewMIDIItemInProj(track, start_time, start_time + length)
            update_arrange()
            return format_success_response(
                message=f"成功在音轨「{track_name}」创建MIDI项目项，范围{start_time}秒到{start_time+length}秒。"
            )
        except Exception as e:
            raise OperationFailedError("创建MIDI项目项", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_midi_note(track_name: str = "", item_index: int = 0, pitch: int = 60, start_ppq: int = 0, duration_ppq: int = 960, velocity: int = 100) -> dict:
        """
        在MIDI项目项中插入音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            pitch: 音符音高（0-127）
            start_ppq: 开始位置（PPQ）
            duration_ppq: 持续时间（PPQ，> 0）
            velocity: 力度（0-127）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if pitch < 0 or pitch > 127:
            raise InvalidParameterError("pitch", pitch, "有效值范围：[0, 127]")
        
        if duration_ppq <= 0:
            raise InvalidParameterError("duration_ppq", duration_ppq, "有效值范围：> 0")
        
        if velocity < 0 or velocity > 127:
            raise InvalidParameterError("velocity", velocity, "有效值范围：[0, 127]")
        
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
                raise OperationFailedError("插入MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("插入MIDI音符", "该项目项不是MIDI类型")
            
            reaper.MIDI_InsertNote(take, False, False, start_ppq, start_ppq + duration_ppq, 0, pitch, velocity, False)
            update_arrange()
            
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            note_name = note_names[pitch % 12]
            octave = (pitch // 12) - 1
            return format_success_response(
                message=f"成功在MIDI项目项中插入音符：{note_name}{octave}（音高{pitch}），力度{velocity}。"
            )
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("插入MIDI音符", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_midi_notes(track_name: str = "", item_index: int = 0) -> dict:
        """
        获取MIDI项目项中的所有音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
        
        Returns:
            音符信息字典，包含success字段和notes数据列表
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
                raise OperationFailedError("获取MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("获取MIDI音符", "该项目项不是MIDI类型")
            
            notes = []
            retval, num_notes = reaper.MIDI_CountEvts(take)
            
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            
            for i in range(num_notes):
                retval2, selected, muted, start_ppq, end_ppq, chan, pitch, vel = reaper.MIDI_GetNote(take, i)
                note_name = note_names[pitch % 12]
                octave = (pitch // 12) - 1
                
                notes.append({
                    "index": i,
                    "pitch": pitch,
                    "note_name": f"{note_name}{octave}",
                    "start_ppq": start_ppq,
                    "end_ppq": end_ppq,
                    "duration_ppq": end_ppq - start_ppq,
                    "velocity": vel,
                    "channel": chan,
                    "selected": bool(selected),
                    "muted": bool(muted)
                })
            
            return format_success_response(data={"notes": notes, "count": len(notes)})
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取MIDI音符", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_midi_note_velocity(track_name: str = "", item_index: int = 0, note_index: int = 0, velocity: int = 100) -> dict:
        """
        设置MIDI音符力度。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            note_index: 音符索引（从0开始，>= 0）
            velocity: 力度（0-127）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if note_index < 0:
            raise InvalidParameterError("note_index", note_index, "有效值范围：>= 0")
        
        if velocity < 0 or velocity > 127:
            raise InvalidParameterError("velocity", velocity, "有效值范围：[0, 127]")
        
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
                raise OperationFailedError("设置MIDI音符力度", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("设置MIDI音符力度", "该项目项不是MIDI类型")
            
            retval, num_notes = reaper.MIDI_CountEvts(take)
            if note_index >= num_notes:
                raise InvalidParameterError(
                    "note_index", note_index,
                    f"有效值范围：[0, {num_notes-1}]，该MIDI项目项共有{num_notes}个音符"
                )
            
            retval2, selected, muted, start_ppq, end_ppq, chan, pitch, _ = reaper.MIDI_GetNote(take, note_index)
            reaper.MIDI_SetNote(take, note_index, selected, muted, start_ppq, end_ppq, chan, pitch, velocity, False)
            update_arrange()
            
            return format_success_response(message=f"成功设置音符力度为{velocity}。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置MIDI音符力度", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_midi_note(track_name: str = "", item_index: int = 0, note_index: int = 0) -> dict:
        """
        删除MIDI音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始，>= 0）
            note_index: 音符索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if note_index < 0:
            raise InvalidParameterError("note_index", note_index, "有效值范围：>= 0")
        
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
                raise OperationFailedError("删除MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                raise OperationFailedError("删除MIDI音符", "该项目项不是MIDI类型")
            
            retval, num_notes = reaper.MIDI_CountEvts(take)
            if note_index >= num_notes:
                raise InvalidParameterError(
                    "note_index", note_index,
                    f"有效值范围：[0, {num_notes-1}]，该MIDI项目项共有{num_notes}个音符"
                )
            
            reaper.MIDI_DeleteNote(take, note_index)
            update_arrange()
            
            return format_success_response(message=f"成功删除音符（索引：{note_index}）。")
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("删除MIDI音符", str(e))