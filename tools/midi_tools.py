from mcp.server.fastmcp import FastMCP
from utils.reaper_client import get_track_by_name, update_arrange

def register_midi_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_create_midi_item(track_name: str = "", start_time: float = 0.0, length: float = 1.0) -> str:
        """
        创建MIDI项目项。
        
        Args:
            track_name: 目标音轨名称
            start_time: 开始时间（秒）
            length: 长度（秒）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if length <= 0:
            return "长度必须大于0。"
        try:
            from reapy import reascript_api as reaper
            reaper.CreateNewMIDIItemInProj(track, start_time, start_time + length)
            update_arrange()
            return f"成功在音轨「{track_name}」创建MIDI项目项，范围{start_time}秒到{start_time+length}秒。"
        except Exception as e:
            return f"创建MIDI项目项失败：{e}"

    @mcp.tool()
    def reaper_insert_midi_note(track_name: str = "", item_index: int = 0, pitch: int = 60, start_ppq: int = 0, duration_ppq: int = 960, velocity: int = 100) -> str:
        """
        在MIDI项目项中插入音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            pitch: 音符音高（0-127）
            start_ppq: 开始位置（PPQ）
            duration_ppq: 持续时间（PPQ）
            velocity: 力度（0-127）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        if pitch < 0 or pitch > 127:
            return f"音高无效：{pitch}，范围应为[0, 127]。"
        if velocity < 0 or velocity > 127:
            return f"力度无效：{velocity}，范围应为[0, 127]。"
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                return "该项目项不是MIDI类型。"
            reaper.MIDI_InsertNote(take, False, False, start_ppq, start_ppq + duration_ppq, 0, pitch, velocity, False)
            update_arrange()
            return f"成功在MIDI项目项中插入音符，音高{pitch}，力度{velocity}。"
        except Exception as e:
            return f"插入MIDI音符失败：{e}"

    @mcp.tool()
    def reaper_get_midi_notes(track_name: str = "", item_index: int = 0) -> list[dict]:
        """
        获取MIDI项目项中的所有音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
        
        Returns:
            音符列表
        """
        track = get_track_by_name(track_name)
        if track is None:
            return [{"error": f"没有找到音轨「{track_name}」。"}]
        if item_index < 0 or item_index >= len(track.items):
            return [{"error": f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"}]
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                return [{"error": "该项目项不是MIDI类型。"}]
            notes = []
            retval, num_notes = reaper.MIDI_CountEvts(take)
            for i in range(num_notes):
                retval2, selected, muted, start_ppq, end_ppq, chan, pitch, vel = reaper.MIDI_GetNote(take, i)
                notes.append({
                    "index": i,
                    "pitch": pitch,
                    "start_ppq": start_ppq,
                    "end_ppq": end_ppq,
                    "duration_ppq": end_ppq - start_ppq,
                    "velocity": vel,
                    "channel": chan,
                    "selected": bool(selected),
                    "muted": bool(muted)
                })
            return notes
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_set_midi_note_velocity(track_name: str = "", item_index: int = 0, note_index: int = 0, velocity: int = 100) -> str:
        """
        设置MIDI音符力度。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            note_index: 音符索引（从0开始）
            velocity: 力度（0-127）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        if velocity < 0 or velocity > 127:
            return f"力度无效：{velocity}，范围应为[0, 127]。"
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                return "该项目项不是MIDI类型。"
            retval, num_notes = reaper.MIDI_CountEvts(take)
            if note_index < 0 or note_index >= num_notes:
                return f"音符索引无效：{note_index}，范围应为[0, {num_notes-1}]。"
            retval2, selected, muted, start_ppq, end_ppq, chan, pitch, _ = reaper.MIDI_GetNote(take, note_index)
            reaper.MIDI_SetNote(take, note_index, selected, muted, start_ppq, end_ppq, chan, pitch, velocity, False)
            update_arrange()
            return f"成功设置音符力度为{velocity}。"
        except Exception as e:
            return f"设置MIDI音符力度失败：{e}"

    @mcp.tool()
    def reaper_delete_midi_note(track_name: str = "", item_index: int = 0, note_index: int = 0) -> str:
        """
        删除MIDI音符。
        
        Args:
            track_name: 音轨名称
            item_index: 项目项索引（从0开始）
            note_index: 音符索引（从0开始）
        
        Returns:
            操作结果消息
        """
        track = get_track_by_name(track_name)
        if track is None:
            return f"没有找到音轨「{track_name}」。"
        if item_index < 0 or item_index >= len(track.items):
            return f"项目项索引无效：{item_index}，范围应为[0, {len(track.items)-1}]。"
        try:
            from reapy import reascript_api as reaper
            item = track.items[item_index]
            take = item.takes[0]
            if not reaper.TakeIsMIDI(take):
                return "该项目项不是MIDI类型。"
            retval, num_notes = reaper.MIDI_CountEvts(take)
            if note_index < 0 or note_index >= num_notes:
                return f"音符索引无效：{note_index}，范围应为[0, {num_notes-1}]。"
            reaper.MIDI_DeleteNote(take, note_index)
            update_arrange()
            return f"成功删除音符。"
        except Exception as e:
            return f"删除MIDI音符失败：{e}"