"""
清宫朝政 配乐创作 - 通过生成.MID文件导入REAPER
绕过reapy web interface的MIDI item创建bug
"""
import os, sys, struct, tempfile, time

os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()
print(f'Project: {proj.name}')

BPM = 78
PPQ = 960
TOTAL_BARS = 60  # ~185 seconds at 78 BPM

def bar_to_tick(bar, beat=0):
    """Convert bar.beat (1-indexed) to MIDI ticks."""
    return int(((bar - 1) * 4 + beat) * PPQ)

def dur_tick(beats):
    return int(beats * PPQ)

# D minor pentatonic pitches
D1, G1, A1, C2 = 26, 31, 33, 36
D2, E2, G2, A2, B2, C3 = 38, 40, 43, 45, 47, 48
D3, E3, F3, G3, A3, B3, C4 = 50, 52, 53, 55, 57, 59, 60
D4, E4, F4, G4, A4, B4, C5 = 62, 64, 65, 67, 69, 71, 72
D5, F5, G5, A5, C6 = 74, 77, 79, 81, 84
D6 = 86

Q, H, W, E, DQ, DH = dur_tick(1), dur_tick(2), dur_tick(4), dur_tick(0.5), dur_tick(1.5), dur_tick(3)

def write_var_len(value):
    """Write MIDI variable-length value."""
    buf = bytearray()
    buf.append(value & 0x7F)
    value >>= 7
    while value:
        buf.append(0x80 | (value & 0x7F))
        value >>= 7
    buf.reverse()
    return bytes(buf)

def create_midi_file(tempo_bpm, ppq, track_name, channel, program, notes):
    """
    Create a Standard MIDI File (format 0) in memory.
    notes: list of [pitch, start_tick, duration_tick, velocity]
    Returns bytes of the .mid file.
    """
    tempo_us = int(60_000_000 / tempo_bpm)
    
    # Header chunk
    header = b'MThd' + struct.pack('>IHHH', 6, 0, 1, ppq)
    
    # Track chunk data
    track_data = bytearray()
    
    # Track name meta event
    name_bytes = track_name.encode('ascii', 'replace')
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x03')
    track_data.extend(write_var_len(len(name_bytes)))
    track_data.extend(name_bytes)
    
    # Tempo meta event
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x51\x03')
    track_data.extend(struct.pack('>I', tempo_us)[1:])  # 3 bytes
    
    # Time signature meta event (4/4)
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x58\x04\x04\x02\x18\x08')
    
    # Program Change
    track_data.extend(write_var_len(0))
    track_data.extend(bytes([0xC0 | channel, program]))
    
    # Sort notes by start time, then by pitch
    sorted_notes = sorted(notes, key=lambda n: (n[1], n[0]))
    
    # Generate note-on and note-off events
    events = []
    for pitch, start, duration, velocity in sorted_notes:
        vel = max(1, min(127, velocity))
        events.append((start, 'on', pitch, vel))
        events.append((start + duration, 'off', pitch, 0))
    
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))  # off before on at same time
    
    last_tick = 0
    for tick, evt_type, pitch, vel in events:
        delta = tick - last_tick
        last_tick = tick
        
        track_data.extend(write_var_len(delta))
        if evt_type == 'on':
            track_data.extend(bytes([0x90 | channel, pitch, vel]))
        else:
            track_data.extend(bytes([0x80 | channel, pitch, 0]))
    
    # End of track
    track_data.extend(write_var_len(0))
    track_data.extend(b'\xFF\x2F\x00')
    
    # Track chunk
    track_chunk = b'MTrk' + struct.pack('>I', len(track_data)) + bytes(track_data)
    
    return header + track_chunk


# ============================================================
# COMPOSITION DATA (same as before)
# ============================================================

# --- 编钟 Bells (ch 0, program 14: Tubular Bells) ---
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

# --- 弦乐 Strings (ch 1, program 48: String Ensemble 1) ---
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
    if bar % 4 == 2:
        chord = [G2, D3, G3, B3, D4]
    elif bar % 4 == 0:
        chord = [A2, C4, A3, E4]
    else:
        chord = [D3, F3, A3, D4, F4]
    for p in chord:
        strings.append([p, pos, W, 85])
for bar in range(49, 58):
    vel = 80 - (bar-49)*8
    pos = bar_to_tick(bar, 0)
    for p in [D3, F3, A3]:
        strings.append([p, pos, W, max(vel, 20)])

# --- 笛子 Flute (ch 2, program 73: Flute) ---
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

# --- 古筝 Koto (ch 3, program 107: Koto) ---
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

# --- 大鼓 Drums (ch 9, GM percussion) ---
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

# --- 大提琴 Cello (ch 4, program 42: Cello) ---
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

# --- 合唱 Choir (ch 5, program 52: Choir Aahs) ---
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

# ============================================================
# CREATE MIDI FILES AND INSERT
# ============================================================

configs = [
    ("编钟 Bells",     bells,   0,  14),
    ("弦乐 Strings",   strings, 1,  48),
    ("笛子 Flute",     flute,   2,  73),
    ("古筝 Koto",      koto,    3,  107),
    ("大鼓 Drums",     drums,   9,   0),
    ("大提琴 Cello",   cello,   4,  42),
    ("合唱 Choir",     choir,   5,  52),
]

temp_dir = tempfile.mkdtemp()
print(f"Temp dir: {temp_dir}")
total_notes = 0

for track_name, notes, channel, program in configs:
    total_notes += len(notes)
    midi_data = create_midi_file(BPM, PPQ, track_name, channel, program, notes)
    filepath = os.path.join(temp_dir, f"{track_name}.mid")
    with open(filepath, 'wb') as f:
        f.write(midi_data)
    print(f"  Created {track_name}: {len(notes)} notes, {len(midi_data)} bytes")

print(f"\nTotal composition: {total_notes} notes across {len(configs)} tracks")

# ============================================================
# INSERT INTO REAPER
# ============================================================
print("\n=== Inserting into REAPER ===")

for track_name, notes, channel, program in configs:
    filepath = os.path.join(temp_dir, f"{track_name}.mid")
    
    # 尝试用 InsertMedia 插入
    try:
        reaper.InsertMedia(proj, filepath, 0)  # mode 0 = add to project
        print(f"  Inserted: {track_name}")
    except Exception as e:
        print(f"  InsertMedia failed for {track_name}: {e}")
        continue

# 检查插入后的轨道
tracks_now = list(proj.tracks)
print(f"\nTracks after insert: {len(tracks_now)}")
for t in tracks_now:
    items = list(t.items)
    print(f"  {t.name}: {len(items)} items")

# ============================================================
# RENAME TRACKS (InsertMedia creates tracks with filename)
# ============================================================
print("\n=== Renaming tracks ===")
# InsertMedia可能在末尾添加轨道，文件名作为轨道名
# 也可能在当前选中轨道后添加
# 需要找到对应轨道并重命名

# 查找最后创建的轨道
all_tracks = list(proj.tracks)
midi_ext = [t for t in all_tracks if t.name.endswith('.mid')]
print(f"Tracks with .mid names: {len(midi_ext)}")
for t in midi_ext:
    print(f"  Found: {t.name}")

# 尝试重命名
for t in all_tracks:
    if t.name.endswith('.mid'):
        base = t.name[:-4]  # remove .mid
        try:
            t.name = base
            print(f"  Renamed: {t.name}")
        except Exception as e:
            print(f"  Rename error: {e}")

# ============================================================
# SET BPM AND SAVE
# ============================================================
print("\n=== Configuring project ===")
try:
    reaper.SetCurrentBPM(proj, BPM, False)
except:
    pass
print(f"  BPM = {BPM}")

proj.save()
print("Project saved!")

# ============================================================
# VERIFY
# ============================================================
print("\n=== Verification ===")
reapy.reconnect()
proj2 = reapy.Project()
verify_tracks = list(proj2.tracks)
print(f"Tracks: {len(verify_tracks)}")
total_notes_verify = 0
for t in verify_tracks:
    items = list(t.items)
    track_notes = 0
    for item in items:
        if item.takes:
            take = item.takes[0]
            rv, _, nn, _, _ = reaper.MIDI_CountEvts(take, 0, 0, 0)
            track_notes += nn
    print(f"  {t.name}: {len(items)} items, {track_notes} notes")
    total_notes_verify += track_notes

print(f"\nTotal notes in REAPER: {total_notes_verify}")
print("Done!")
