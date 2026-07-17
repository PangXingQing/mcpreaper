"""
工程报告与诊断工具。

提供 REAPER 工程的统计、诊断和报告功能。
"""
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TrackStats:
    """单条轨道的统计信息。"""
    name: str = ""
    index: int = 0
    item_count: int = 0
    fx_count: int = 0
    send_count: int = 0
    receive_count: int = 0
    volume_db: float = 0.0
    pan: float = 0.0
    is_muted: bool = False
    is_soloed: bool = False
    is_rec_armed: bool = False
    midi_note_count: int = 0
    midi_cc_count: int = 0
    audio_item_count: int = 0
    envelope_count: int = 0


@dataclass
class ProjectReport:
    """完整的工程报告。"""
    project_name: str = ""
    project_path: str = ""
    bpm: float = 120.0
    time_signature: str = "4/4"
    track_count: int = 0
    total_items: int = 0
    total_fx: int = 0
    total_markers: int = 0
    total_regions: int = 0
    total_midi_notes: int = 0
    total_sends: int = 0
    tracks: List[TrackStats] = field(default_factory=list)
    generated_at: str = ""
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


def generate_project_report() -> Dict[str, Any]:
    """生成当前 REAPER 工程的完整诊断报告。

    Returns:
        结构化工程报告字典
    """
    try:
        from reapy import reascript_api as reaper

        report = ProjectReport()
        report.generated_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # 工程基本信息
        try:
            proj = reaper.EnumProjects(-1, "", 0)  # type: ignore
        except Exception:
            proj = None

        # BPM
        try:
            report.bpm = reaper.Master_GetTempo()
        except Exception:
            report.bpm = 120.0

        # 拍号
        try:
            retval, _, num, denom = reaper.GetProjectTimeSignature2(0, 0, 0)
            if retval:
                report.time_signature = f"{num}/{denom}"
        except Exception:
            pass

        # 轨道分析
        num_tracks = reaper.CountTracks(0)
        report.track_count = num_tracks

        for i in range(num_tracks):
            track = reaper.GetTrack(0, i)
            ts = TrackStats()
            ts.index = i

            # 轨道名
            try:
                retval, name = reaper.GetTrackName(track, "", 256)
                ts.name = name
            except Exception:
                ts.name = f"Track {i + 1}"

            # 状态
            try:
                ts.is_muted = bool(reaper.GetMediaTrackInfo_Value(track, "B_MUTE"))
                ts.is_soloed = bool(reaper.GetMediaTrackInfo_Value(track, "B_SOLO"))
                ts.is_rec_armed = bool(reaper.GetMediaTrackInfo_Value(track, "B_RECARM"))
                ts.volume_db = reaper.GetMediaTrackInfo_Value(track, "D_VOL")
                ts.pan = reaper.GetMediaTrackInfo_Value(track, "D_PAN")
            except Exception:
                pass

            # Item 统计
            try:
                ts.item_count = reaper.CountTrackMediaItems(track)
                report.total_items += ts.item_count
            except Exception:
                pass

            # FX 统计
            try:
                ts.fx_count = reaper.TrackFX_GetCount(track)
                report.total_fx += ts.fx_count
            except Exception:
                pass

            # Send 统计
            try:
                ts.send_count = reaper.GetTrackNumSends(track, 0)
                report.total_sends += ts.send_count
            except Exception:
                pass

            # 包络统计
            try:
                ts.envelope_count = reaper.CountTrackEnvelopes(track)
            except Exception:
                pass

            # MIDI 统计（遍历 item）
            try:
                item_count = reaper.CountTrackMediaItems(track)
                for j in range(item_count):
                    item = reaper.GetTrackMediaItem(track, j)
                    take = reaper.GetMediaItemTake(item, 0)
                    if take:
                        try:
                            _, _, note_count, cc_count, _ = reaper.MIDI_CountEvts(take, 0, 0, 0)
                            ts.midi_note_count += note_count
                            ts.midi_cc_count += cc_count
                            report.total_midi_notes += note_count
                        except Exception:
                            pass
            except Exception:
                pass

            report.tracks.append(ts)

        # 标记/区域统计
        try:
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(0, 0, 0)
            if retval:
                report.total_markers = num_markers
                report.total_regions = num_regions
        except Exception:
            pass

        # 生成警告
        if report.track_count == 0:
            report.warnings.append("工程中没有音轨")
        if report.total_midi_notes == 0 and report.total_items > 0:
            report.warnings.append("有媒体项但未检测到 MIDI 音符（可能为纯音频工程或 MIDI 数据格式未识别）")
        for t in report.tracks:
            if t.is_rec_armed:
                report.warnings.append(f"音轨「{t.name}」处于录音待命状态")
            if t.fx_count == 0 and t.item_count > 0:
                pass  # 没有 FX 属于正常情况

        # 优化建议
        if report.track_count > 20:
            report.suggestions.append("音轨数量较多（>20），建议使用文件夹/分组管理")
        if report.total_fx > 10:
            report.suggestions.append(f"总计 {report.total_fx} 个效果器，注意 CPU 负载")

        return {
            "success": True,
            "project_name": report.project_name,
            "project_path": report.project_path,
            "bpm": report.bpm,
            "time_signature": report.time_signature,
            "track_count": report.track_count,
            "total_items": report.total_items,
            "total_fx": report.total_fx,
            "total_markers": report.total_markers,
            "total_regions": report.total_regions,
            "total_midi_notes": report.total_midi_notes,
            "total_sends": report.total_sends,
            "tracks_detail": [
                {
                    "index": t.index,
                    "name": t.name,
                    "items": t.item_count,
                    "fx": t.fx_count,
                    "sends": t.send_count,
                    "midi_notes": t.midi_note_count,
                    "midi_cc": t.midi_cc_count,
                    "envelopes": t.envelope_count,
                    "volume_db": round(t.volume_db, 1),
                    "pan": round(t.pan, 2),
                    "mute": t.is_muted,
                    "solo": t.is_soloed,
                    "rec_arm": t.is_rec_armed,
                }
                for t in report.tracks
            ],
            "warnings": report.warnings,
            "suggestions": report.suggestions,
            "generated_at": report.generated_at,
        }

    except ImportError:
        return {
            "success": False,
            "error": "reapy 未安装，无法生成工程报告",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"生成报告时出错: {e}",
        }


def estimate_cpu_load(track_info: Dict[str, Any]) -> Dict[str, Any]:
    """基于轨道配置估算 CPU 负载（启发式）。"""
    warnings = []
    score = 0

    # FX 数量影响
    fx_count = track_info.get("total_fx", 0)
    if fx_count > 20:
        score += 3
        warnings.append(f"效果器数量 ({fx_count}) 很高，建议冻结部分轨道")
    elif fx_count > 10:
        score += 1

    # 轨道数量影响
    track_count = track_info.get("track_count", 0)
    if track_count > 30:
        score += 2
    elif track_count > 15:
        score += 1

    # MIDI 轨道 + 复杂合成器
    midi_notes = track_info.get("total_midi_notes", 0)
    if midi_notes > 5000:
        warnings.append("大量 MIDI 音符，检查使用的虚拟乐器数量")

    load_levels = {0: "低", 1: "中低", 2: "中", 3: "中高", 4: "高", 5: "极高"}

    return {
        "load_level": load_levels.get(score, "极高"),
        "score": score,
        "max_score": 5,
        "warnings": warnings,
        "suggestion": (
            "建议使用 冻结/渲染 功能降低 CPU 负载" if score >= 3
            else "当前负载在可接受范围内"
        ),
    }
