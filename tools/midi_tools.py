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
            track.add_midi_item(start_time, start_time + length)
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
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("插入MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            
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
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("获取MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not take.is_midi:
                return format_success_response(data={"notes": [], "count": 0})
            
            # Use take.notes (reapy property, runs inside_reaper) for reliable access
            notes = []
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            
            for i, note in enumerate(take.notes):
                note_name = note_names[note.pitch % 12]
                octave = (note.pitch // 12) - 1
                
                notes.append({
                    "index": i,
                    "pitch": note.pitch,
                    "note_name": f"{note_name}{octave}",
                    "start_ppq": note.start,
                    "end_ppq": note.end,
                    "duration_ppq": note.end - note.start,
                    "velocity": note.velocity,
                    "channel": note.channel,
                    "selected": note.is_selected,
                    "muted": note.is_muted
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
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("设置MIDI音符力度", "该项目项没有take")
            
            take = item.takes[0]
            retval, _, num_notes, num_cc, num_text = reaper.MIDI_CountEvts(take, 0, 0, 0)
            if num_notes == 0:
                return format_success_response(message="项目项没有MIDI音符，无法设置力度。")
            if note_index >= num_notes:
                raise InvalidParameterError(
                    "note_index", note_index,
                    f"有效值范围：[0, {num_notes-1}]，该MIDI项目项共有{num_notes}个音符"
                )
            
            retval2, _, selected, muted, start_ppq, end_ppq, chan, pitch, _ = reaper.MIDI_GetNote(
                take, note_index, False, False, 0.0, 0.0, 0, 0, 0
            )
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
        
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            
            if not item.takes:
                raise OperationFailedError("删除MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            retval, _, num_notes, num_cc, num_text = reaper.MIDI_CountEvts(take, 0, 0, 0)
            if num_notes == 0:
                return format_success_response(message="项目项没有MIDI音符，无需删除。")
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

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_midi_instrument(track_name: str = "", item_index: int = 0, channel: int = 0, program: int = 0, bank_msb: int = 0, bank_lsb: int = 0) -> dict:
        """
        设置MIDI音轨的乐器/音色（Program Change + Bank Select）。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            channel: MIDI通道（0-15）
            program: 乐器编号（0-127，GM标准乐器号）
            bank_msb: Bank Select MSB（0-127，默认0=GM音色库）
            bank_lsb: Bank Select LSB（0-127，默认0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if channel < 0 or channel > 15:
            raise InvalidParameterError("channel", channel, "有效值范围：[0, 15]")
        
        if program < 0 or program > 127:
            raise InvalidParameterError("program", program, "有效值范围：[0, 127]")
        
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
                raise OperationFailedError("设置MIDI乐器", "该项目项没有take")
            
            take = item.takes[0]
            
            # Insert Bank Select MSB (CC#0) if non-zero
            if bank_msb != 0:
                reaper.MIDI_InsertCC(take, False, False, 0, 0xB0 | (channel & 0xF), channel, 0, bank_msb)
            
            # Insert Bank Select LSB (CC#32) if non-zero
            if bank_lsb != 0:
                reaper.MIDI_InsertCC(take, False, False, 0, 0xB0 | (channel & 0xF), channel, 32, bank_lsb)
            
            # Insert Program Change at position 0
            reaper.MIDI_InsertCC(take, False, False, 0, 0xC0 | (channel & 0xF), channel, program, 0)
            
            update_arrange()
            
            # GM instrument names for common instruments
            gm_names = {
                0: "Acoustic Grand Piano", 1: "Bright Acoustic Piano",
                14: "Tubular Bells", 15: "Dulcimer",
                24: "Acoustic Guitar (nylon)", 25: "Acoustic Guitar (steel)",
                40: "Violin", 41: "Viola", 42: "Cello", 43: "Contrabass",
                46: "Orchestral Harp", 48: "String Ensemble 1", 49: "String Ensemble 2",
                52: "Choir Aahs", 54: "Voice Oohs",
                56: "Trumpet", 60: "French Horn", 66: "Tenor Sax",
                68: "Oboe", 71: "Bassoon",
                73: "Flute", 74: "Pan Flute", 75: "Blown Bottle",
                76: "Shakuhachi", 77: "Whistle",
                89: "Pad 2 (warm)", 91: "Pad 4 (choir)",
                107: "Koto"
            }
            inst_name = gm_names.get(program, f"Program {program}")
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的MIDI乐器为：{inst_name}（通道{channel}，Program {program}）。"
            )
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置MIDI乐器", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_insert_midi_notes_batch(track_name: str = "", item_index: int = 0, channel: int = 0, notes: list = None) -> dict:
        """
        批量插入MIDI音符。用于高效创建大规模MIDI编曲。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            channel: MIDI通道（0-15）
            notes: 音符列表，每个音符为 [pitch, start_ppq, duration_ppq, velocity]
                   例如: [[60, 0, 480, 100], [64, 480, 480, 90], [67, 960, 480, 80]]
        
        Returns:
            操作结果字典，包含success、message字段和插入的音符数量
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "有效值范围：>= 0")
        
        if channel < 0 or channel > 15:
            raise InvalidParameterError("channel", channel, "有效值范围：[0, 15]")
        
        if not notes or not isinstance(notes, list) or len(notes) == 0:
            raise InvalidParameterError("notes", notes, "请提供有效的音符列表")
        
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
                raise OperationFailedError("批量插入MIDI音符", "该项目项没有take")
            
            take = item.takes[0]
            if not take.is_midi:
                raise OperationFailedError("批量插入MIDI音符", "该项目项的take不是MIDI类型")
            
            inserted = 0
            errors_list = []
            
            for i, note_data in enumerate(notes):
                try:
                    if not isinstance(note_data, (list, tuple)) or len(note_data) < 4:
                        errors_list.append(f"索引{i}：格式无效，需要 [pitch, start, duration, velocity]")
                        continue
                    
                    pitch = int(note_data[0])
                    start_ppq = int(note_data[1])
                    duration_ppq = int(note_data[2])
                    velocity = int(note_data[3])
                    
                    if pitch < 0 or pitch > 127:
                        errors_list.append(f"索引{i}：音高{pitch}超出范围[0,127]")
                        continue
                    if duration_ppq <= 0:
                        errors_list.append(f"索引{i}：时长{duration_ppq}无效")
                        continue
                    if velocity < 0 or velocity > 127:
                        velocity = max(0, min(127, velocity))
                    
                    # Use take.add_note (inside_reaper) instead of raw MIDI_InsertNote
                    # for reliable distributed API execution
                    try:
                        take.add_note(
                            start_ppq, start_ppq + duration_ppq,
                            pitch, velocity, channel,
                            selected=False, muted=False, unit="ppq", sort=False
                        )
                        inserted += 1
                    except Exception as note_err:
                        # Fallback: try raw MIDI_InsertNote with return value check
                        result = reaper.MIDI_InsertNote(
                            take, False, False,
                            start_ppq, start_ppq + duration_ppq,
                            channel, pitch, velocity, False
                        )
                        if result:
                            inserted += 1
                        else:
                            errors_list.append(f"索引{i}：MIDI_InsertNote返回失败，音高{pitch}")
                except Exception as e:
                    errors_list.append(f"索引{i}：{str(e)}")
            
            # Sort events after batch insertion
            try:
                take.sort_events()
            except Exception:
                reaper.MIDI_Sort(take)
            
            update_arrange()
            
            msg = f"成功批量插入{inserted}个MIDI音符到音轨「{track_name}」。"
            if errors_list:
                msg += f" 跳过{len(errors_list)}个：{'；'.join(errors_list[:3])}"
            
            return format_success_response(message=msg, data={"inserted_count": inserted, "errors": errors_list})
        except (OperationFailedError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("批量插入MIDI音符", str(e))