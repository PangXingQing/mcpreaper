"""
清宫朝政 配乐创作 - 最终方案
1. 清理所有测试轨道
2. 生成7个标准MIDI文件
3. 创建干净的REAPER工程轨道结构
4. 记录reapy限制
"""
import os, sys, struct

os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()
print(f'Project: {proj.name}')

# ============================================================
# STEP 1: Clean up - remove all tracks
# ============================================================
print("\n=== Cleaning up project ===")
tracks = list(proj.tracks)
print(f"Removing {len(tracks)} tracks...")

# 选择所有轨道并删除
reaper.Main_OnCommand(40296, 0)  # Select all tracks
reaper.Main_OnCommand(40005, 0)  # Remove tracks

remaining = list(proj.tracks)
print(f"Remaining tracks: {len(remaining)}")

# 清理标记（尽量）
try:
    rv, _, nm, nr = reaper.CountProjectMarkers(proj, 0, 0)
    print(f"Markers: {nm}, Regions: {nr}")
except:
    pass

# ============================================================
# STEP 2: Create tracks for the film score
# ============================================================
print("\n=== Creating tracks ===")
track_config = [
    ("编钟 Bells",     -3.0),
    ("弦乐 Strings",   -6.0),
    ("笛子 Flute",     -4.0),
    ("古筝 Koto",      -5.0),
    ("大鼓 Drums",     -4.0),
    ("大提琴 Cello",   -5.0),
    ("合唱 Choir",     -8.0),
]

tracks_created = []
for idx, (name, vol_db) in enumerate(track_config):
    track = proj.add_track(idx, name=name)
    linear_vol = 10 ** (vol_db / 20.0)
    try:
        track.volume = linear_vol
    except:
        pass
    tracks_created.append(track)
    print(f"  Created: {name}")

# ============================================================
# STEP 3: Generate MIDI files
# ============================================================
print("\n=== Generating MIDI files ===")

BPM = 78
PPQ = 960

def bar_to_tick(bar, beat=0):
    return int(((bar - 1) * 4 + beat) * PPQ)

def dur_tick(beats):
    return int(beats * PPQ)

# D minor pentatonic
D1, G1, A1, C2 = 26, 31, 33, 36
D2, E2, G2, A2, B2, C3 = 38, 40, 43, 45, 47, 48
D3, E3, F3, G3, A3, B3, C4 = 50, 52, 53, 55, 57, 59, 60
D4, E4, F4, G4, A4, B4, C5 = 62, 64, 65, 67, 69, 71, 72
D5, F5, G5, A5, C6 = 74, 77, 79, 81, 84
D6 = 86

Q, H, W, E, DQ, DH = dur_tick(1), dur_tick(2), dur_tick(4), dur_tick(0.5), dur_tick(1.5), dur_tick(3)

def write_var_len(value):
    buf = bytearray()
    buf.append(value & 0x7F)
    value >>= 7
    while value:
        buf.append(0x80 | (value & 0x7F))
        value >>= 7
    buf.reverse()
    return bytes(buf)

def create_midi_file(tempo_bpm, ppq, track_name, channel, program, notes):
    tempo_us = int(60_000_000 / tempo_bpm)
    header = b'MThd' + struct.pack('>IHHH', 6, 0, 1, ppq)
    
    track_data = bytearray()
    name_bytes = track_name.encode('ascii', 'replace')
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x03')
    track_data.extend(write_var_len(len(name_bytes)))
    track_data.extend(name_bytes)
    
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x51\x03')
    track_data.extend(struct.pack('>I', tempo_us)[1:])
    
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x58\x04\x04\x02\x18\x08')
    
    track_data.extend(write_var_len(0))
    track_data.extend(bytes([0xC0 | channel, program]))
    
    sorted_notes = sorted(notes, key=lambda n: (n[1], n[0]))
    events = []
    for pitch, start, duration, velocity in sorted_notes:
        vel = max(1, min(127, velocity))
        events.append((start, 'on', pitch, vel))
        events.append((start + duration, 'off', pitch, 0))
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))
    
    last_tick = 0
    for tick, evt_type, pitch, vel in events:
        delta = tick - last_tick
        last_tick = tick
        track_data.extend(write_var_len(delta))
        if evt_type == 'on':
            track_data.extend(bytes([0x90 | channel, pitch, vel]))
        else:
            track_data.extend(bytes([0x80 | channel, pitch, 0]))
    
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x2F\x00')
    track_chunk = b'MTrk' + struct.pack('>I', len(track_data)) + bytes(track_data)
    return header + track_chunk

# Build note data (same composition)
bells = []
bell_theme = [(D4, Q), (G4, Q), (A4, Q), (D4, H)]
bell_theme2 = [(D5, Q), (C5, Q), (D5, Q), (A4, H)]
for bar in range(1, 5):
    for beat, (p, d) in enumerate(bell_theme):
        bells.append([p, bar_to_tick(bar, beat), d, 90])
for bar in range(5, 9):
    for beat, (p, d) in enumerate(bell_theme2):
        bells.append([p, bar_to_tick(bar, beat), d, 80])
for bar in range(10, 30, 2):
    bells.append([D4, bar_to_tick(bar, 0), H, 85])
    bells.append([A4, bar_to_tick(bar, 2), H, 85])
for bar in range(31, 48):
    for beat, (p, d) in enumerate(bell_theme):
        bells.append([p, bar_to_tick(bar, beat), d, 100])
for bar in range(49, 58, 2):
    vel = 90 - (bar-49)*10
    bells.append([D4, bar_to_tick(bar, 0), W, vel])
    if bar % 4 == 0:
        bells.append([G4, bar_to_tick(bar, 2), DQ, vel])
bells.append([D4, bar_to_tick(58, 0), W, 100])
bells.append([D4, bar_to_tick(58, 0), dur_tick(8), 60])

strings = []
for bar in range(1, 9):
    pos = bar_to_tick(bar, 0)
    for p in [D3, F3, A3]:
        strings.append([p, pos, W, 50])
chords_a = [([D3, F3, A3], 4), ([A2, C4, A3], 2), ([G2, D3, G3], 2), ([D3, F3, A3], 2)]
bar = 10
for cnotes, n_bars in chords_a:
    for b in range(n_bars):
        pos = bar_to_tick(bar + b, 0)
        for p in cnotes:
            strings.append([p, pos, W, 60])
    bar += n_bars
chords_b = [([D3, F3, A3, D4], 2), ([A2, C4, A3, E4], 2), ([G2, D3, G3, B3], 2), ([C3, G3, C4, E4], 2), ([D3, F3, A3, D4], 2)]
bar = 20
for cnotes, n_bars in chords_b:
    for b in range(n_bars):
        pos = bar_to_tick(bar + b, 0)
        for p in cnotes:
            strings.append([p, pos, W, 70])
    bar += n_bars
for bar in range(31, 48):
    pos = bar_to_tick(bar, 0)
    if bar % 4 == 2: chord = [G2, D3, G3, B3, D4]
    elif bar % 4 == 0: chord = [A2, C4, A3, E4]
    else: chord = [D3, F3, A3, D4, F4]
    for p in chord:
        strings.append([p, pos, W, 85])
for bar in range(49, 58):
    vel = 80 - (bar-49)*8
    pos = bar_to_tick(bar, 0)
    for p in [D3, F3, A3]:
        strings.append([p, pos, W, max(vel, 20)])

flute = []
flute.append([A4, bar_to_tick(8, 0), DH, 70])
flute.append([G4, bar_to_tick(8, 3), Q, 70])
flute.append([D5, bar_to_tick(9, 0), W, 80])
theme_a = [(G4, DQ), (A4, E), (D5, Q), (D5, E), (C5, E), (A4, DQ), (G4, E),
           (F4, DQ), (G4, E), (C5, Q), (A4, E), (G4, DQ), (D4, E), (F4, Q), (G4, Q)]
bar, beat = 10, 0
for p, d in theme_a:
    pos = bar_to_tick(bar, beat)
    ad = min(d, dur_tick(4 - beat))
    flute.append([p, pos, ad, 75])
    beat += ad / PPQ
    while beat >= 4: beat -= 4; bar += 1
theme_b = [(D5, Q), (C5, Q), (A4, H), (G4, Q), (A4, Q), (D5, DQ), (C5, E),
           (A4, H), (G4, H), (D5, Q), (A4, Q), (D5, Q), (F5, Q), (G5, H), (F5, E), (D5, E), (C5, Q)]
bar, beat = 20, 0
for p, d in theme_b:
    pos = bar_to_tick(bar, beat)
    ad = min(d, dur_tick(4 - beat))
    flute.append([p, pos, ad, 80])
    beat += ad / PPQ
    while beat >= 4: beat -= 4; bar += 1
climax = [(D5, H), (F5, H), (G5, H), (A5, DQ), (G5, E), (F5, Q),
          (D5, H), (A5, DQ), (G5, E), (F5, Q), (D5, DQ),
          (D6, Q), (C6, Q), (A5, H), (G5, DQ), (F5, E), (D5, Q), (F5, Q),
          (G5, H), (A5, H), (D6, DQ), (C6, E), (A5, Q), (G5, Q), (D5, W)]
bar, beat = 31, 0
for p, d in climax:
    pos = bar_to_tick(bar, beat)
    ad = min(d, dur_tick(4 - beat))
    flute.append([p, pos, ad, 95])
    beat += ad / PPQ
    while beat >= 4: beat -= 4; bar += 1
coda = [(D5, W), (A4, H), (G4, H), (F4, W), (D4, W), (D4, DH)]
bar, beat = 49, 0
for p, d in coda:
    pos = bar_to_tick(bar, beat)
    ad = min(d, dur_tick(4 - beat))
    vel = 80 - (bar-49)*7
    flute.append([p, pos, ad, max(vel, 10)])
    beat += ad / PPQ
    while beat >= 4: beat -= 4; bar += 1

koto = []
for bar in [1, 3, 5, 7, 9]:
    koto.append([D4, bar_to_tick(bar, 0), Q, 60])
    koto.append([A3, bar_to_tick(bar, 1), Q, 60])
    koto.append([G3, bar_to_tick(bar, 2), Q, 60])
    koto.append([D3, bar_to_tick(bar, 3), Q, 60])
dm_arp = [(D4, E), (F4, E), (A4, E), (D5, E)] * 2
am_arp = [(A3, E), (C4, E), (E4, E), (A4, E)] * 2
g_arp = [(G3, E), (B3, E), (D4, E), (G4, E)] * 2
c_arp = [(C4, E), (E4, E), (G4, E), (C5, E)] * 2
pat = [dm_arp]*4 + [am_arp]*2 + [g_arp]*2 + [dm_arp]*2
for bi, arp in enumerate(pat):
    bar = bi + 10
    for beat, (p, d) in enumerate(arp):
        koto.append([p, bar_to_tick(bar, beat*0.5), d, 65])
pat2 = [dm_arp]*2 + [c_arp]*2 + [g_arp]*2 + [dm_arp]*4
for bi, arp in enumerate(pat2):
    bar = bi + 20
    for beat, (p, d) in enumerate(arp):
        koto.append([p, bar_to_tick(bar, beat*0.5), d, 75])
for bar in range(31, 48):
    if bar % 2 == 0:
        arp = [(D4, E), (F4, E), (A4, E), (D5, E), (F5, E), (D5, E), (A4, E), (F4, E)]
    elif bar % 4 == 1:
        arp = [(A3, E), (C4, E), (E4, E), (A4, E), (C5, E), (A4, E), (E4, E), (C4, E)]
    else:
        arp = [(G3, E), (B3, E), (D4, E), (G4, E), (B4, E), (G4, E), (D4, E), (B3, E)]
    for beat, (p, d) in enumerate(arp):
        koto.append([p, bar_to_tick(bar, beat*0.5), d, 85])
for bar in range(49, 58):
    vel = 70 - (bar-49)*5
    koto.append([D4, bar_to_tick(bar, 0), Q, vel])
    koto.append([A3, bar_to_tick(bar, 1), Q, vel])
    if bar % 2 == 0:
        koto.append([F4, bar_to_tick(bar, 2), Q, vel])

drums = []
BD, CR, WH, WL, SN = 36, 49, 76, 77, 38
for bar in [1, 3, 5, 7]:
    drums.append([WH, bar_to_tick(bar, 0), E, 80])
    drums.append([WL, bar_to_tick(bar, 2), E, 80])
drums.append([BD, bar_to_tick(9, 0), Q, 100])
drums.append([CR, bar_to_tick(9, 0), E, 90])
for bar in range(10, 20):
    drums.append([WL, bar_to_tick(bar, 0), E, 60])
    drums.append([WH, bar_to_tick(bar, 2), E, 60])
    if bar % 4 == 0:
        drums.append([BD, bar_to_tick(bar, 0), Q, 70])
for bar in range(20, 30):
    drums.append([BD, bar_to_tick(bar, 0), Q, 80])
    drums.append([WL, bar_to_tick(bar, 1), E, 70])
    drums.append([WH, bar_to_tick(bar, 2), E, 70])
    if bar % 2 == 0:
        drums.append([SN, bar_to_tick(bar, 3), E, 60])
for beat in range(8):
    drums.append([BD, bar_to_tick(30, beat*0.5), E, 90+beat*5])
drums.append([CR, bar_to_tick(31, 0), E, 100])
for bar in range(31, 48):
    drums.append([BD, bar_to_tick(bar, 0), Q, 100])
    drums.append([BD, bar_to_tick(bar, 2), Q, 90])
    if bar % 2 == 0:
        drums.append([SN, bar_to_tick(bar, 1), E, 70])
    if bar % 4 == 0:
        drums.append([CR, bar_to_tick(bar, 0), E, 90])
for bar in range(49, 55):
    vel = 80 - (bar-49)*15
    drums.append([BD, bar_to_tick(bar, 0), Q, max(vel, 20)])
    if bar % 2 == 0:
        drums.append([WL, bar_to_tick(bar, 2), E, max(vel-10, 10)])
drums.append([BD, bar_to_tick(56, 0), Q, 80])
drums.append([CR, bar_to_tick(56, 0), E, 70])

cello = []
for bar in range(1, 9):
    cello.append([D2, bar_to_tick(bar, 0), W, 55])
cello.append([D2, bar_to_tick(9, 0), H, 60])
bass1 = [(D2, 4), (A1, 2), (G1, 2), (D2, 2)]
bar = 10
for p, nb in bass1:
    for b in range(nb):
        cello.append([p, bar_to_tick(bar+b, 0), W, 70])
    bar += nb
bass2 = [(D2, 2), (A1, 2), (G1, 2), (C2, 2), (D2, 2)]
bar = 20
for p, nb in bass2:
    for b in range(nb):
        cello.append([p, bar_to_tick(bar+b, 0), W, 80])
    bar += nb
for bar in range(31, 48):
    if bar % 2 == 0:
        cello.append([D2, bar_to_tick(bar, 0), H, 90])
        cello.append([A1, bar_to_tick(bar, 2), H, 85])
    elif bar % 4 == 1:
        cello.append([G1, bar_to_tick(bar, 0), DH, 90])
        cello.append([A1, bar_to_tick(bar, 3), Q, 85])
    else:
        cello.append([C2, bar_to_tick(bar, 0), H, 85])
        cello.append([D2, bar_to_tick(bar, 2), H, 90])
for bar in range(49, 58):
    vel = 75 - (bar-49)*7
    cello.append([D2, bar_to_tick(bar, 0), W, max(vel, 15)])

choir = []
for bar in range(20, 30, 2):
    choir.append([A4, bar_to_tick(bar, 0), DH, 50])
    choir.append([D5, bar_to_tick(bar, 0), DH, 50])
for bar in range(31, 48):
    vel = 70 if bar < 40 else 85
    chord = [D4, F4, A4] if bar % 2 == 0 else [G4, B4, D5]
    for p in chord:
        choir.append([p, bar_to_tick(bar, 0), W, vel])
for bar in range(49, 56, 2):
    vel = 60 - (bar-49)*8
    choir.append([D4, bar_to_tick(bar, 0), W, vel])
    choir.append([A4, bar_to_tick(bar, 0), W, vel])

# Generate MIDI files
output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ReaperProject')
os.makedirs(output_dir, exist_ok=True)

configs = [
    ("01_Bells.mid",     bells,   0,  14,  "编钟 Bells"),
    ("02_Strings.mid",   strings, 1,  48,  "弦乐 Strings"),
    ("03_Flute.mid",     flute,   2,  73,  "笛子 Flute"),
    ("04_Koto.mid",      koto,    3,  107, "古筝 Koto"),
    ("05_Drums.mid",     drums,   9,   0,  "大鼓 Drums"),
    ("06_Cello.mid",     cello,   4,  42,  "大提琴 Cello"),
    ("07_Choir.mid",     choir,   5,  52,  "合唱 Choir"),
]

total_notes = 0
for filename, notes, ch, prog, label in configs:
    midi_data = create_midi_file(BPM, PPQ, label, ch, prog, notes)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(midi_data)
    total_notes += len(notes)
    print(f"  {filename}: {len(notes)} notes, {len(midi_data)} bytes")

print(f"\nTotal: {total_notes} notes across {len(configs)} MIDI files")
print(f"Output: {output_dir}")

# ============================================================
# STEP 4: Set project info and save
# ============================================================
print("\n=== Configuring project ===")
try:
    reaper.SetCurrentBPM(proj, BPM, False)
except:
    pass
print(f"  BPM = {BPM}")

proj.save()
print("Project saved!")

print(f"\n{'=' * 60}")
print("完成！")
print(f"  - 7 条音轨已创建在REAPER工程中")
print(f"  - {total_notes} 个MIDI音符已生成为7个标准MIDI文件")
print(f"  - MIDI文件位置: {output_dir}")
print(f"")
print(f"  使用方法:")
print(f"  1. 在REAPER中，将每个.MID文件拖入对应的音轨")
print(f"  2. MIDI文件已包含正确的Program Change（乐器音色）")
print(f"  3. 确保每条音轨的MIDI硬件输出指向系统默认音源")
print(f"{'=' * 60}")
