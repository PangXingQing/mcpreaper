"""
清宫朝政 配乐创作脚本（直接reapy版）
Imperial Court - Qing Dynasty Film Score
D minor pentatonic, 78 BPM, ~3 minutes, 7 instruments
"""
import os, sys, time

os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()
print(f'Project: {proj.name}')

BPM = 78
PPQ_PER_BEAT = 960
PPQ_PER_BAR = PPQ_PER_BEAT * 4  # 3840

def bar_to_ppq(bar, beat=0):
    """Convert bar.beat to PPQ. bar is 1-indexed."""
    return int(((bar - 1) * 4 + beat) * PPQ_PER_BEAT)

def dur_ppq(beats):
    return int(beats * PPQ_PER_BEAT)

# D minor pentatonic pitches
D1, G1, A1, C2 = 26, 31, 33, 36
D2, E2, G2, A2, B2, C3 = 38, 40, 43, 45, 47, 48
D3, E3, F3, G3, A3, B3, C4 = 50, 52, 53, 55, 57, 59, 60
D4, E4, F4, G4, A4, B4, C5 = 62, 64, 65, 67, 69, 71, 72
D5, F5, G5, A5, C6 = 74, 77, 79, 81, 84
D6 = 86

Q  = dur_ppq(1)
H  = dur_ppq(2)
W  = dur_ppq(4)
E  = dur_ppq(0.5)
DQ = dur_ppq(1.5)
DH = dur_ppq(3)

def insert_notes_to_track(track, item_index, channel, notes, label):
    """Insert notes into a MIDI item. Returns count."""
    if not notes:
        return 0
    items = list(track.items)
    if item_index >= len(items):
        print(f"  ERROR [{label}]: item_index {item_index} >= {len(items)}")
        return 0
    item = items[item_index]
    if not item.takes:
        print(f"  ERROR [{label}]: no take")
        return 0
    take = item.takes[0]
    count = 0
    errors = 0
    for i, note_data in enumerate(notes):
        try:
            pitch, start_ppq, dur, velocity = note_data
            if dur <= 0:
                continue
            reaper.MIDI_InsertNote(take, False, False,
                                   start_ppq, start_ppq + dur,
                                   channel, pitch, velocity, False)
            count += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  WARN [{label}]: note {i}: {e}")
    print(f"  [{label}]: {count} notes, {errors} errors")
    return count

def set_instrument(track, item_index, channel, program):
    """Set GM instrument via Program Change."""
    items = list(track.items)
    if item_index >= len(items):
        return False
    item = items[item_index]
    if not item.takes:
        return False
    take = item.takes[0]
    reaper.MIDI_InsertCC(take, False, False, 0, 0xC0 | (channel & 0xF), channel, program, 0)
    return True

# ============================================================
# STEP 1: Project setup
# ============================================================
print("\n=== Setting up project ===")
try:
    reaper.SetCurrentBPM(proj, BPM, False)
except:
    pass
try:
    reaper.SetProjectTimeSignature2(proj, 0, 4, 4, BPM)
except:
    pass
print(f"  BPM={BPM}, Time Signature=4/4")

# ============================================================
# STEP 2: Create tracks and MIDI items
# ============================================================
print("\n=== Creating tracks ===")
track_configs = [
    ("编钟 Bells",     0, 14),    # Tubular Bells
    ("弦乐 Strings",   1, 48),    # String Ensemble 1
    ("笛子 Flute",     2, 73),    # Flute
    ("古筝 Koto",      3, 107),   # Koto
    ("大鼓 Drums",     9, 0),     # Channel 10 drums
    ("大提琴 Cello",   4, 42),    # Cello
    ("合唱 Choir",     5, 52),    # Choir Aahs
]

tracks = {}
duration = 185.0

for idx, (name, channel, program) in enumerate(track_configs):
    track = proj.add_track(len(list(proj.tracks)), name=name)
    tracks[name] = (track, channel)
    track.add_midi_item(0, duration)
    set_instrument(track, 0, channel, program)
    gm_names = {14:"Tubular Bells", 42:"Cello", 48:"String Ensemble 1", 
                52:"Choir Aahs", 73:"Flute", 107:"Koto", 0:"Drums"}
    inst = gm_names.get(program, f"Program {program}")
    print(f"  Created: {name} ({inst}, ch={channel})")

# ============================================================
# STEP 3: Compose each instrument
# ============================================================
print("\n=== Composing ===")
total_notes = 0

# --- 编钟 Bells (ch 0) ---
bells_notes = []
# Intro
bell_theme = [(D4, Q), (G4, Q), (A4, Q), (D4, H)]
bell_theme2 = [(D5, Q), (C5, Q), (D5, Q), (A4, H)]
for bar in range(1, 5):
    for beat, (pitch, dur) in enumerate(bell_theme):
        bells_notes.append([pitch, bar_to_ppq(bar, beat), dur, 90])
for bar in range(5, 9):
    for beat, (pitch, dur) in enumerate(bell_theme2):
        bells_notes.append([pitch, bar_to_ppq(bar, beat), dur, 80])
# Sparse
for bar in range(10, 30, 2):
    bells_notes.append([D4, bar_to_ppq(bar, 0), H, 85])
    bells_notes.append([A4, bar_to_ppq(bar, 2), H, 85])
# Climax
for bar in range(31, 48):
    for beat, (pitch, dur) in enumerate(bell_theme):
        bells_notes.append([pitch, bar_to_ppq(bar, beat), dur, 100])
# Coda
for bar in range(49, 58, 2):
    vel = 90 - (bar - 49) * 10
    bells_notes.append([D4, bar_to_ppq(bar, 0), W, vel])
    if bar % 4 == 0:
        bells_notes.append([G4, bar_to_ppq(bar, 2), DQ, vel])
bells_notes.append([D4, bar_to_ppq(58, 0), W, 100])
bells_notes.append([D4, bar_to_ppq(58, 0), dur_ppq(8), 60])

total_notes += insert_notes_to_track(tracks["编钟 Bells"][0], 0, 0, bells_notes, "编钟")

# --- 弦乐 Strings (ch 1) ---
strings_notes = []
# Intro pad
for bar in range(1, 9):
    pos = bar_to_ppq(bar, 0)
    for p in [D3, F3, A3]:
        strings_notes.append([p, pos, W, 50])
# Development A
chords_a = [
    ([D3, F3, A3], 4), ([A2, C4, A3], 2), ([G2, D3, G3], 2), ([D3, F3, A3], 2),
]
bar = 10
for chord_notes, n_bars in chords_a:
    for b in range(n_bars):
        pos = bar_to_ppq(bar + b, 0)
        for p in chord_notes:
            strings_notes.append([p, pos, W, 60])
    bar += n_bars
# Development B
chords_b = [
    ([D3, F3, A3, D4], 2), ([A2, C4, A3, E4], 2),
    ([G2, D3, G3, B3], 2), ([C3, G3, C4, E4], 2),
    ([D3, F3, A3, D4], 2),
]
bar = 20
for chord_notes, n_bars in chords_b:
    for b in range(n_bars):
        pos = bar_to_ppq(bar + b, 0)
        for p in chord_notes:
            strings_notes.append([p, pos, W, 70])
    bar += n_bars
# Climax
for bar in range(31, 48):
    pos = bar_to_ppq(bar, 0)
    if bar % 4 == 2:
        chord = [G2, D3, G3, B3, D4]
    elif bar % 4 == 0:
        chord = [A2, C4, A3, E4]
    else:
        chord = [D3, F3, A3, D4, F4]
    for p in chord:
        strings_notes.append([p, pos, W, 85])
# Coda
for bar in range(49, 58):
    vel = 80 - (bar - 49) * 8
    pos = bar_to_ppq(bar, 0)
    for p in [D3, F3, A3]:
        strings_notes.append([p, pos, W, max(vel, 20)])

total_notes += insert_notes_to_track(tracks["弦乐 Strings"][0], 0, 1, strings_notes, "弦乐")

# --- 大提琴 Cello (ch 4) ---
cello_notes = []
# Intro
for bar in range(1, 9):
    cello_notes.append([D2, bar_to_ppq(bar, 0), W, 55])
cello_notes.append([D2, bar_to_ppq(9, 0), H, 60])
# Development
bass_line = [(D2, 4), (A1, 2), (G1, 2), (D2, 2)]
bar = 10
for pitch, n_bars in bass_line:
    for b in range(n_bars):
        cello_notes.append([pitch, bar_to_ppq(bar + b, 0), W, 70])
    bar += n_bars
bass_line2 = [(D2, 2), (A1, 2), (G1, 2), (C2, 2), (D2, 2)]
bar = 20
for pitch, n_bars in bass_line2:
    for b in range(n_bars):
        cello_notes.append([pitch, bar_to_ppq(bar + b, 0), W, 80])
    bar += n_bars
# Climax
for bar in range(31, 48):
    if bar % 2 == 0:
        cello_notes.append([D2, bar_to_ppq(bar, 0), H, 90])
        cello_notes.append([A1, bar_to_ppq(bar, 2), H, 85])
    elif bar % 4 == 1:
        cello_notes.append([G1, bar_to_ppq(bar, 0), DH, 90])
        cello_notes.append([A1, bar_to_ppq(bar, 3), Q, 85])
    else:
        cello_notes.append([C2, bar_to_ppq(bar, 0), H, 85])
        cello_notes.append([D2, bar_to_ppq(bar, 2), H, 90])
# Coda
for bar in range(49, 58):
    vel = 75 - (bar - 49) * 7
    cello_notes.append([D2, bar_to_ppq(bar, 0), W, max(vel, 15)])

total_notes += insert_notes_to_track(tracks["大提琴 Cello"][0], 0, 4, cello_notes, "大提琴")

# --- 笛子 Flute (ch 2) ---
flute_notes = []
# Intro tease
flute_notes.append([A4, bar_to_ppq(8, 0), DH, 70])
flute_notes.append([G4, bar_to_ppq(8, 3), Q, 70])
flute_notes.append([D5, bar_to_ppq(9, 0), W, 80])
# Theme A
theme_a = [
    (G4, DQ), (A4, E), (D5, Q), (D5, E), (C5, E), (A4, DQ), (G4, E),
    (F4, DQ), (G4, E), (C5, Q), (A4, E), (G4, DQ), (D4, E), (F4, Q), (G4, Q),
]
bar, beat = 10, 0
for pitch, dur in theme_a:
    pos = bar_to_ppq(bar, beat)
    actual_dur = min(dur, dur_ppq(4 - beat))
    flute_notes.append([pitch, pos, actual_dur, 75])
    beat += actual_dur / PPQ_PER_BEAT
    while beat >= 4:
        beat -= 4
        bar += 1
# Theme B
theme_b = [
    (D5, Q), (C5, Q), (A4, H), 
    (G4, Q), (A4, Q), (D5, DQ), (C5, E),
    (A4, H), (G4, H),
    (D5, Q), (A4, Q), (D5, Q), (F5, Q),
    (G5, H), (F5, E), (D5, E), (C5, Q),
]
bar, beat = 20, 0
for pitch, dur in theme_b:
    pos = bar_to_ppq(bar, beat)
    actual_dur = min(dur, dur_ppq(4 - beat))
    flute_notes.append([pitch, pos, actual_dur, 80])
    beat += actual_dur / PPQ_PER_BEAT
    while beat >= 4:
        beat -= 4
        bar += 1
# Climax
climax_melody = [
    (D5, H), (F5, H), (G5, H), (A5, DQ), (G5, E), (F5, Q),
    (D5, H), (A5, DQ), (G5, E), (F5, Q), (D5, DQ),
    (D6, Q), (C6, Q), (A5, H), (G5, DQ), (F5, E), (D5, Q), (F5, Q),
    (G5, H), (A5, H), (D6, DQ), (C6, E), (A5, Q), (G5, Q),
    (D5, W),
]
bar, beat = 31, 0
for pitch, dur in climax_melody:
    pos = bar_to_ppq(bar, beat)
    actual_dur = min(dur, dur_ppq(4 - beat))
    flute_notes.append([pitch, pos, actual_dur, 95])
    beat += actual_dur / PPQ_PER_BEAT
    while beat >= 4:
        beat -= 4
        bar += 1
# Coda
coda = [
    (D5, W), (A4, H), (G4, H), (F4, W), (D4, W), (D4, DH),
]
bar, beat = 49, 0
for pitch, dur in coda:
    pos = bar_to_ppq(bar, beat)
    actual_dur = min(dur, dur_ppq(4 - beat))
    vel = 80 - (bar - 49) * 7
    flute_notes.append([pitch, pos, actual_dur, max(vel, 10)])
    beat += actual_dur / PPQ_PER_BEAT
    while beat >= 4:
        beat -= 4
        bar += 1

total_notes += insert_notes_to_track(tracks["笛子 Flute"][0], 0, 2, flute_notes, "笛子")

# --- 古筝 Koto (ch 3) ---
koto_notes = []
# Intro
for bar in [1, 3, 5, 7, 9]:
    koto_notes.append([D4, bar_to_ppq(bar, 0), Q, 60])
    koto_notes.append([A3, bar_to_ppq(bar, 1), Q, 60])
    koto_notes.append([G3, bar_to_ppq(bar, 2), Q, 60])
    koto_notes.append([D3, bar_to_ppq(bar, 3), Q, 60])
# Development arpeggios
dm_arp = [(D4, E), (F4, E), (A4, E), (D5, E)] * 2
am_arp = [(A3, E), (C4, E), (E4, E), (A4, E)] * 2
g_arp  = [(G3, E), (B3, E), (D4, E), (G4, E)] * 2
c_arp  = [(C4, E), (E4, E), (G4, E), (C5, E)] * 2
pattern_sequence = [dm_arp] * 4 + [am_arp] * 2 + [g_arp] * 2 + [dm_arp] * 2
for bar_idx, arp in enumerate(pattern_sequence):
    bar = bar_idx + 10
    for beat, (pitch, dur) in enumerate(arp):
        koto_notes.append([pitch, bar_to_ppq(bar, beat * 0.5), dur, 65])
pattern_sequence2 = [dm_arp] * 2 + [c_arp] * 2 + [g_arp] * 2 + [dm_arp] * 4
for bar_idx, arp in enumerate(pattern_sequence2):
    bar = bar_idx + 20
    for beat, (pitch, dur) in enumerate(arp):
        koto_notes.append([pitch, bar_to_ppq(bar, beat * 0.5), dur, 75])
# Climax
for bar in range(31, 48):
    if bar % 2 == 0:
        arp = [(D4, E), (F4, E), (A4, E), (D5, E), (F5, E), (D5, E), (A4, E), (F4, E)]
    elif bar % 4 == 1:
        arp = [(A3, E), (C4, E), (E4, E), (A4, E), (C5, E), (A4, E), (E4, E), (C4, E)]
    else:
        arp = [(G3, E), (B3, E), (D4, E), (G4, E), (B4, E), (G4, E), (D4, E), (B3, E)]
    for beat, (pitch, dur) in enumerate(arp):
        koto_notes.append([pitch, bar_to_ppq(bar, beat * 0.5), dur, 85])
# Coda
for bar in range(49, 58):
    vel = 70 - (bar - 49) * 5
    koto_notes.append([D4, bar_to_ppq(bar, 0), Q, vel])
    koto_notes.append([A3, bar_to_ppq(bar, 1), Q, vel])
    if bar % 2 == 0:
        koto_notes.append([F4, bar_to_ppq(bar, 2), Q, vel])

total_notes += insert_notes_to_track(tracks["古筝 Koto"][0], 0, 3, koto_notes, "古筝")

# --- 大鼓 Drums (ch 9) ---
drums_notes = []
BD, CRASH, WOOD_H, WOOD_L, SNARE = 36, 49, 76, 77, 38
# Intro
for bar in [1, 3, 5, 7]:
    drums_notes.append([WOOD_H, bar_to_ppq(bar, 0), E, 80])
    drums_notes.append([WOOD_L, bar_to_ppq(bar, 2), E, 80])
drums_notes.append([BD, bar_to_ppq(9, 0), Q, 100])
drums_notes.append([CRASH, bar_to_ppq(9, 0), E, 90])
# Dev A
for bar in range(10, 20):
    drums_notes.append([WOOD_L, bar_to_ppq(bar, 0), E, 60])
    drums_notes.append([WOOD_H, bar_to_ppq(bar, 2), E, 60])
    if bar % 4 == 0:
        drums_notes.append([BD, bar_to_ppq(bar, 0), Q, 70])
# Dev B
for bar in range(20, 30):
    drums_notes.append([BD, bar_to_ppq(bar, 0), Q, 80])
    drums_notes.append([WOOD_L, bar_to_ppq(bar, 1), E, 70])
    drums_notes.append([WOOD_H, bar_to_ppq(bar, 2), E, 70])
    if bar % 2 == 0:
        drums_notes.append([SNARE, bar_to_ppq(bar, 3), E, 60])
# Build up
for beat in range(8):
    drums_notes.append([BD, bar_to_ppq(30, beat * 0.5), E, 90 + beat * 5])
drums_notes.append([CRASH, bar_to_ppq(31, 0), E, 100])
# Climax
for bar in range(31, 48):
    drums_notes.append([BD, bar_to_ppq(bar, 0), Q, 100])
    drums_notes.append([BD, bar_to_ppq(bar, 2), Q, 90])
    if bar % 2 == 0:
        drums_notes.append([SNARE, bar_to_ppq(bar, 1), E, 70])
    if bar % 4 == 0:
        drums_notes.append([CRASH, bar_to_ppq(bar, 0), E, 90])
# Resolution
for bar in range(49, 55):
    vel = 80 - (bar - 49) * 15
    drums_notes.append([BD, bar_to_ppq(bar, 0), Q, max(vel, 20)])
    if bar % 2 == 0:
        drums_notes.append([WOOD_L, bar_to_ppq(bar, 2), E, max(vel - 10, 10)])
drums_notes.append([BD, bar_to_ppq(56, 0), Q, 80])
drums_notes.append([CRASH, bar_to_ppq(56, 0), E, 70])

total_notes += insert_notes_to_track(tracks["大鼓 Drums"][0], 0, 9, drums_notes, "大鼓")

# --- 合唱 Choir (ch 5) ---
choir_notes = []
for bar in range(20, 30, 2):
    choir_notes.append([A4, bar_to_ppq(bar, 0), DH, 50])
    choir_notes.append([D5, bar_to_ppq(bar, 0), DH, 50])
for bar in range(31, 48):
    vel = 70 if bar < 40 else 85
    chord = [D4, F4, A4] if bar % 2 == 0 else [G4, B4, D5]
    for p in chord:
        choir_notes.append([p, bar_to_ppq(bar, 0), W, vel])
for bar in range(49, 56, 2):
    vel = 60 - (bar - 49) * 8
    choir_notes.append([D4, bar_to_ppq(bar, 0), W, vel])
    choir_notes.append([A4, bar_to_ppq(bar, 0), W, vel])

total_notes += insert_notes_to_track(tracks["合唱 Choir"][0], 0, 5, choir_notes, "合唱")

# ============================================================
# STEP 4: Volume balance
# ============================================================
print("\n=== Volume balance ===")
volume_settings = [
    ("编钟 Bells", -3.0),
    ("弦乐 Strings", -6.0),
    ("笛子 Flute", -4.0),
    ("古筝 Koto", -5.0),
    ("大鼓 Drums", -4.0),
    ("大提琴 Cello", -5.0),
    ("合唱 Choir", -8.0),
]
for name, db in volume_settings:
    track, _ = tracks[name]
    # reapy track volume uses a 0-1 scale; convert from dB
    # linear_vol = 10^(db/20)
    linear_vol = 10 ** (db / 20.0)
    try:
        track.volume = linear_vol
    except:
        from reapy import reascript_api as reaper
        reaper.SetMediaTrackInfo_Value(track, "D_VOL", linear_vol)
    print(f"  {name}: {db}dB")

# ============================================================
# STEP 5: Save
# ============================================================
print("\n=== Saving ===")
proj.save()

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'=' * 60}")
print(f"配乐创作完成！")
print(f"  7 tracks: 编钟/弦乐/笛子/古筝/大鼓/大提琴/合唱")
print(f"  总计: {total_notes} MIDI音符")
print(f"  BPM: {BPM}, Key: D minor pentatonic")
print(f"  时长: ~185秒 (~3分钟)")
print(f"{'=' * 60}")
