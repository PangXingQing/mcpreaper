"""
MIDI 辅助工具。

提供 MIDI 音符名称转换、音高常量、GM 音色库、和弦/音阶定义等。
"""
from typing import Dict, List, Tuple, Optional

# ============================================================
# 音符名称与音高
# ============================================================

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def midi_note_to_name(note: int) -> str:
    """MIDI 音高数字转音符名称（如 60 → C4）。"""
    octave = (note // 12) - 1
    name = NOTE_NAMES[note % 12]
    return f"{name}{octave}"


def name_to_midi_note(name: str) -> int:
    """音符名称转 MIDI 音高数字（如 C4 → 60）。"""
    name = name.strip().upper()
    # 处理如 "C#4" 或 "C4"
    if len(name) >= 3 and name[1] == "#":
        note_part = name[:2]
        octave_str = name[2:]
    else:
        note_part = name[0]
        octave_str = name[1:]

    if note_part not in NOTE_NAMES:
        raise ValueError(f"无效的音符名: {name}")

    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"无效的八度: {octave_str} in {name}")

    note_idx = NOTE_NAMES.index(note_part)
    return (octave + 1) * 12 + note_idx


# 预定义的音高常量（C-1 到 G9）
PITCH_RANGE: Dict[str, int] = {}
for octave in range(-1, 10):
    for note_name in NOTE_NAMES:
        midi_val = (octave + 1) * 12 + NOTE_NAMES.index(note_name)
        if 0 <= midi_val <= 127:
            PITCH_RANGE[f"{note_name}{octave}"] = midi_val


# ============================================================
# GM 音色库（General MIDI Level 1）
# ============================================================

GM_INSTRUMENT_CATEGORIES = {
    "Piano": [(0, "Acoustic Grand Piano"), (1, "Bright Acoustic Piano"), (2, "Electric Grand Piano"),
              (3, "Honky-tonk Piano"), (4, "Rhodes Piano"), (5, "Chorused Piano"),
              (6, "Harpsichord"), (7, "Clavinet")],
    "Chromatic Percussion": [(8, "Celesta"), (9, "Glockenspiel"), (10, "Music Box"),
                              (11, "Vibraphone"), (12, "Marimba"), (13, "Xylophone"),
                              (14, "Tubular Bells"), (15, "Dulcimer")],
    "Organ": [(16, "Drawbar Organ"), (17, "Percussive Organ"), (18, "Rock Organ"),
              (19, "Church Organ"), (20, "Reed Organ"), (21, "Accordion"),
              (22, "Harmonica"), (23, "Tango Accordion")],
    "Guitar": [(24, "Nylon Guitar"), (25, "Steel Guitar"), (26, "Jazz Guitar"),
               (27, "Clean Electric Guitar"), (28, "Muted Electric Guitar"), (29, "Overdriven Guitar"),
               (30, "Distortion Guitar"), (31, "Guitar Harmonics")],
    "Bass": [(32, "Acoustic Bass"), (33, "Finger Bass"), (34, "Pick Bass"),
             (35, "Fretless Bass"), (36, "Slap Bass 1"), (37, "Slap Bass 2"),
             (38, "Synth Bass 1"), (39, "Synth Bass 2")],
    "Strings": [(40, "Violin"), (41, "Viola"), (42, "Cello"),
                (43, "Contrabass"), (44, "Tremolo Strings"), (45, "Pizzicato Strings"),
                (46, "Orchestral Harp"), (47, "Timpani")],
    "Ensemble": [(48, "String Ensemble 1"), (49, "String Ensemble 2"), (50, "Synth Strings 1"),
                 (51, "Synth Strings 2"), (52, "Choir Aahs"), (53, "Voice Oohs"),
                 (54, "Synth Voice"), (55, "Orchestra Hit")],
    "Brass": [(56, "Trumpet"), (57, "Trombone"), (58, "Tuba"),
              (59, "Muted Trumpet"), (60, "French Horn"), (61, "Brass Section"),
              (62, "Synth Brass 1"), (63, "Synth Brass 2")],
    "Reed": [(64, "Soprano Sax"), (65, "Alto Sax"), (66, "Tenor Sax"),
             (67, "Baritone Sax"), (68, "Oboe"), (69, "English Horn"),
             (70, "Bassoon"), (71, "Clarinet")],
    "Pipe": [(72, "Piccolo"), (73, "Flute"), (74, "Recorder"),
             (75, "Pan Flute"), (76, "Bottle Blow"), (77, "Shakuhachi"),
             (78, "Whistle"), (79, "Ocarina")],
    "Synth Lead": [(80, "Lead 1 (square)"), (81, "Lead 2 (sawtooth)"), (82, "Lead 3 (calliope)"),
                   (83, "Lead 4 (chiff)"), (84, "Lead 5 (charang)"), (85, "Lead 6 (voice)"),
                   (86, "Lead 7 (fifths)"), (87, "Lead 8 (bass+lead)")],
    "Synth Pad": [(88, "Pad 1 (new age)"), (89, "Pad 2 (warm)"), (90, "Pad 3 (polysynth)"),
                  (91, "Pad 4 (choir)"), (92, "Pad 5 (bowed)"), (93, "Pad 6 (metallic)"),
                  (94, "Pad 7 (halo)"), (95, "Pad 8 (sweep)")],
    "Synth Effects": [(96, "FX 1 (rain)"), (97, "FX 2 (soundtrack)"), (98, "FX 3 (crystal)"),
                      (99, "FX 4 (atmosphere)"), (100, "FX 5 (brightness)"),
                      (101, "FX 6 (goblins)"), (102, "FX 7 (echoes)"), (103, "FX 8 (sci-fi)")],
    "Ethnic": [(104, "Sitar"), (105, "Banjo"), (106, "Shamisen"),
               (107, "Koto"), (108, "Kalimba"), (109, "Bagpipe"),
               (110, "Fiddle"), (111, "Shanai")],
    "Percussive": [(112, "Tinkle Bell"), (113, "Agogo"), (114, "Steel Drums"),
                   (115, "Woodblock"), (116, "Taiko Drum"), (117, "Melodic Tom"),
                   (118, "Synth Drum"), (119, "Reverse Cymbal")],
    "Sound Effects": [(120, "Guitar Fret Noise"), (121, "Breath Noise"), (122, "Seashore"),
                      (123, "Bird Tweet"), (124, "Telephone Ring"), (125, "Helicopter"),
                      (126, "Applause"), (127, "Gunshot")],
}


def get_gm_instrument_name(program: int) -> str:
    """根据 GM program number 获取音色名称。"""
    if program < 0 or program > 127:
        return f"Unknown ({program})"
    for category, instruments in GM_INSTRUMENT_CATEGORIES.items():
        for prog, name in instruments:
            if prog == program:
                return f"{name} ({category})"
    return f"Unknown ({program})"


def get_gm_category(program: int) -> str:
    """获取音色所属分类。"""
    for category, instruments in GM_INSTRUMENT_CATEGORIES.items():
        for prog, _ in instruments:
            if prog == program:
                return category
    return "Unknown"


def search_gm_instruments(keyword: str) -> List[Tuple[int, str, str]]:
    """按关键词搜索 GM 音色库。"""
    keyword = keyword.lower()
    results = []
    for category, instruments in GM_INSTRUMENT_CATEGORIES.items():
        for prog, name in instruments:
            if keyword in name.lower() or keyword in category.lower():
                results.append((prog, name, category))
    return results


# ============================================================
# GM 鼓组音符映射（通道 10）
# ============================================================

GM_DRUM_NOTES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick",
    38: "Acoustic Snare", 39: "Hand Clap", 40: "Electric Snare",
    41: "Low Floor Tom", 42: "Closed Hi-Hat", 43: "High Floor Tom",
    44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1",
    50: "High Tom", 51: "Ride Cymbal 1", 52: "Chinese Cymbal",
    53: "Ride Bell", 54: "Tambourine", 55: "Splash Cymbal",
    56: "Cowbell", 57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo", 61: "Low Bongo",
    62: "Mute Hi Conga", 63: "Open Hi Conga", 64: "Low Conga",
    65: "High Timbale", 66: "Low Timbale", 67: "High Agogo",
    68: "Low Agogo", 69: "Cabasa", 70: "Maracas",
    71: "Short Whistle", 72: "Long Whistle", 73: "Short Guiro",
    74: "Long Guiro", 75: "Claves", 76: "Hi Wood Block",
    77: "Low Wood Block", 78: "Mute Cuica", 79: "Open Cuica",
    80: "Mute Triangle", 81: "Open Triangle",
}


def get_drum_name(note: int) -> str:
    """获取 GM 鼓组音符对应的打击乐器名称。"""
    return GM_DRUM_NOTES.get(note, f"Note {note}")


# ============================================================
# 音阶与和弦
# ============================================================

SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "whole_tone": [0, 2, 4, 6, 8, 10],
    "chromatic": list(range(12)),
}


CHORD_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "maj9": [0, 4, 7, 11, 14],
    "min9": [0, 3, 7, 10, 14],
}


def get_scale_notes(root: int, scale_type: str) -> List[int]:
    """获取指定根音和音阶类型的音阶音符列表。

    Args:
        root: 根音 MIDI 音高
        scale_type: 音阶类型名（见 SCALE_INTERVALS）

    Returns:
        MIDI 音高列表（跨越一个八度）
    """
    intervals = SCALE_INTERVALS.get(scale_type.lower())
    if intervals is None:
        raise ValueError(f"未知音阶类型: {scale_type}. 可用: {list(SCALE_INTERVALS.keys())}")
    return [root + i for i in intervals]


def get_chord_notes(root: int, chord_type: str) -> List[int]:
    """获取指定根音和和弦类型的和弦音符列表。

    Args:
        root: 根音 MIDI 音高
        chord_type: 和弦类型名（见 CHORD_INTERVALS）

    Returns:
        MIDI 音高列表
    """
    intervals = CHORD_INTERVALS.get(chord_type.lower())
    if intervals is None:
        raise ValueError(f"未知和弦类型: {chord_type}. 可用: {list(CHORD_INTERVALS.keys())}")
    return [root + i for i in intervals]


def transpose_notes(notes: List[int], semitones: int) -> List[int]:
    """将 MIDI 音符列表移调指定半音数。"""
    return [max(0, min(127, n + semitones)) for n in notes]


def clamp_velocity(velocity: int) -> int:
    """确保力度值在 1-127 范围内（0 = 音符关）。"""
    return max(1, min(127, velocity))


# ============================================================
# 时间转换
# ============================================================

PPQ_DEFAULT = 960  # 默认 PPQ (Pulses Per Quarter Note)

def beat_to_ppq(beat: float, ppq: int = PPQ_DEFAULT) -> int:
    """拍号转 PPQ tick。"""
    return int(beat * ppq)


def bar_to_ppq(bar: int, beat: int = 0, ppq: int = PPQ_DEFAULT, beats_per_bar: int = 4) -> int:
    """小节+拍转为 PPQ tick。"""
    return int(((bar - 1) * beats_per_bar + beat) * ppq)


def ppq_to_seconds(ppq: int, bpm: float, ppq: int = PPQ_DEFAULT) -> float:
    """PPQ tick 转时间（秒）。"""
    return (ppq / ppq) * (60 / bpm)


def seconds_to_ppq(seconds: float, bpm: float, ppq: int = PPQ_DEFAULT) -> int:
    """时间（秒）转 PPQ tick。"""
    return int(seconds * bpm / 60 * ppq)


def note_duration_ppq(duration: str, ppq: int = PPQ_DEFAULT) -> int:
    """音符时值名称转 PPQ tick。

    支持：whole, half, quarter, eighth, 16th, 32nd 及附点版本（如 dotted_half）
    """
    base = {
        "whole": 4 * ppq,
        "half": 2 * ppq,
        "quarter": 1 * ppq,
        "eighth": ppq // 2,
        "16th": ppq // 4,
        "32nd": ppq // 8,
    }
    duration = duration.lower().strip()
    if duration.startswith("dotted_"):
        base_key = duration[7:]
        if base_key in base:
            return int(base[base_key] * 1.5)
    if duration in base:
        return base[duration]
    # 尝试解析为数字（以拍为单位）
    try:
        beats = float(duration)
        return int(beats * ppq)
    except ValueError:
        raise ValueError(f"未知音符时值: {duration}")
