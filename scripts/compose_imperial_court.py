"""
清宫朝政 配乐创作脚本
Imperial Court - Qing Dynasty Film Score
D minor pentatonic, 78 BPM, 180 seconds
"""
import os, sys, json, asyncio, time

os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as mcp

BPM = 78
PPQ_PER_BEAT = 960
PPQ_PER_BAR = PPQ_PER_BEAT * 4  # 3840

def bar_to_ppq(bar, beat=0):
    """Convert bar.beat to PPQ. bar is 1-indexed."""
    return int(((bar - 1) * 4 + beat) * PPQ_PER_BEAT)

def dur_ppq(beats):
    """Convert duration in beats to PPQ."""
    return int(beats * PPQ_PER_BEAT)

# D minor pentatonic scale notes
# D4=62, F4=65, G4=67, A4=69, C5=72, D5=74, F5=77, G5=79, A5=81, C6=84
# D3=50, F3=53, G3=55, A3=57, C4=60
D1, G1, A1, C2 = 26, 31, 33, 36
D2, E2, G2, A2, B2, C3 = 38, 40, 43, 45, 47, 48
D3, E3, F3, G3, A3, B3, C4 = 50, 52, 53, 55, 57, 59, 60
D4, E4, F4, G4, A4, B4, C5 = 62, 64, 65, 67, 69, 71, 72
D5, F5, G5, A5, C6 = 74, 77, 79, 81, 84
D6 = 86

Q  = dur_ppq(1)    # quarter note
H  = dur_ppq(2)    # half note
W  = dur_ppq(4)    # whole note
E  = dur_ppq(0.5)  # eighth
DQ = dur_ppq(1.5)  # dotted quarter
DH = dur_ppq(3)    # dotted half
EH = dur_ppq(0.25) # sixteenth

async def call(name, **kwargs):
    r = await mcp.mcp.call_tool(name, kwargs if kwargs else {})
    return json.loads(r[0].text)

async def setup_project():
    print("Setting up project...")
    await call('reaper_set_project_bpm', bpm=BPM)
    await call('reaper_set_project_time_signature', numerator=4, denominator=4)
    await call('reaper_set_frame_rate', frame_rate=24.0)
    print("  Project configured: 78 BPM, 4/4, 24fps")

async def create_tracks():
    """Create all instrument tracks."""
    print("Creating tracks...")
    tracks = [
        ("编钟 Bells", "Bells"),
        ("弦乐 Strings", "Strings"),
        ("笛子 Flute", "Flute"),
        ("古筝 Koto", "Koto"),
        ("大鼓 Drums", "Drums"),
        ("大提琴 Cello", "Cello"),
        ("合唱 Choir", "Choir"),
    ]
    for display_name, _ in tracks:
        r = await call('reaper_add_track', track_name=display_name)
        print(f"  Created: {display_name} - {r.get('success')}")
    
    # Create MIDI items (3 minutes = 180 seconds)
    duration = 185.0
    for display_name, _ in tracks:
        r = await call('reaper_create_midi_item', track_name=display_name, start_time=0, length=duration)
        if not r.get('success'):
            print(f"  WARNING: Failed to create MIDI item on {display_name}")
        else:
            print(f"  MIDI item created: {display_name}")

async def set_instruments():
    """Set GM instruments for each track."""
    print("Setting instruments...")
    
    instruments = [
        ("编钟 Bells", 0, 14),      # Tubular Bells
        ("弦乐 Strings", 1, 48),     # String Ensemble 1
        ("笛子 Flute", 2, 73),       # Flute
        ("古筝 Koto", 3, 107),       # Koto
        ("大鼓 Drums", 9, 0),        # Channel 10 (9) = Drums
        ("大提琴 Cello", 4, 42),     # Cello
        ("合唱 Choir", 5, 52),       # Choir Aahs
    ]
    
    for track_name, channel, program in instruments:
        r = await call('reaper_set_midi_instrument', 
                       track_name=track_name, item_index=0, 
                       channel=channel, program=program)
        print(f"  {track_name}: {r.get('success')}")

async def compose_bells():
    """编钟 - ceremonial bells, playing the main harmony rhythm."""
    print("Composing 编钟 Bells...")
    track = "编钟 Bells"
    
    notes = []
    
    # Intro - solo bells (bars 1-9)
    # Bell toll pattern: D4, G4, A4, D4
    bell_theme = [(D4, Q), (G4, Q), (A4, Q), (D4, H)]  # 1 bar
    bell_theme2 = [(D5, Q), (C5, Q), (D5, Q), (A4, H)]
    
    for bar in range(1, 5):
        for beat, (pitch, dur) in enumerate(bell_theme):
            pos = bar_to_ppq(bar, beat)
            notes.append([pitch, pos, dur, 90])
    
    for bar in range(5, 9):
        for beat, (pitch, dur) in enumerate(bell_theme2):
            pos = bar_to_ppq(bar, beat)
            notes.append([pitch, pos, dur, 80])
    
    # Development - sparse bells
    for bar in range(10, 30, 2):
        notes.append([D4, bar_to_ppq(bar, 0), H, 85])
        notes.append([A4, bar_to_ppq(bar, 2), H, 85])
    
    # Climax - full bell pattern (bars 31-48)
    for bar in range(31, 48):
        for beat, (pitch, dur) in enumerate(bell_theme):
            pos = bar_to_ppq(bar, beat)
            notes.append([pitch, pos, dur, 100])
    
    # Coda - fading bells
    for bar in range(49, 58, 2):
        vel = 90 - (bar - 49) * 10
        notes.append([D4, bar_to_ppq(bar, 0), W, vel])
        if bar % 4 == 0:
            notes.append([G4, bar_to_ppq(bar, 2), DQ, vel])
    
    # Final bell toll
    notes.append([D4, bar_to_ppq(58, 0), W, 100])
    notes.append([D4, bar_to_ppq(58, 0), dur_ppq(8), 60])  # long sustain
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=0, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_strings():
    """弦乐 - string ensemble pads for harmonic foundation."""
    print("Composing 弦乐 Strings...")
    track = "弦乐 Strings"
    
    notes = []
    
    # Intro pad (bars 1-9): Dm chord sustained
    # D minor: D3, F3, A3
    for bar in range(1, 9):
        pos = bar_to_ppq(bar, 0)
        notes.append([D3, pos, W, 50])
        notes.append([F3, pos, W, 50])
        notes.append([A3, pos, W, 50])
    
    # Development A (bars 10-19): Chord progression
    # Dm: D3-F3-A3, Am: A2-C3-E3, G: G2-B2-D3, C: C3-E3-G3
    chords_a = [
        ([D3, F3, A3], 4),  # Dm - 4 bars
        ([A2, C4, A3], 2),  # Am - 2 bars
        ([G2, D3, G3], 2),  # G - 2 bars
        ([D3, F3, A3], 2),  # Dm - 2 bars
    ]
    bar = 10
    for chord_notes, n_bars in chords_a:
        for b in range(n_bars):
            pos = bar_to_ppq(bar + b, 0)
            for pitch in chord_notes:
                notes.append([pitch, pos, W, 60])
        bar += n_bars
    
    # Development B (bars 20-30): Richer harmony
    chords_b = [
        ([D3, F3, A3, D4], 2),  # Dm
        ([A2, C4, A3, E4], 2),  # Am
        ([G2, D3, G3, B3], 2),  # G
        ([C3, G3, C4, E4], 2),  # C
        ([D3, F3, A3, D4], 2),  # Dm
    ]
    bar = 20
    for chord_notes, n_bars in chords_b:
        for b in range(n_bars):
            pos = bar_to_ppq(bar + b, 0)
            for pitch in chord_notes:
                notes.append([pitch, pos, W, 70])
        bar += n_bars
    
    # Climax (bars 31-48): Full strings
    climax_chord = [D3, F3, A3, D4, F4]
    for bar in range(31, 48):
        pos = bar_to_ppq(bar, 0)
        chord = climax_chord
        if bar % 4 == 2:
            chord = [G2, D3, G3, B3, D4]
        elif bar % 4 == 0:
            chord = [A2, C4, A3, E4]
        for pitch in chord:
            notes.append([pitch, pos, W, 85])
    
    # Resolution (bars 49-58): Diminuendo
    for bar in range(49, 58):
        vel = 80 - (bar - 49) * 8
        pos = bar_to_ppq(bar, 0)
        for pitch in [D3, F3, A3]:
            notes.append([pitch, pos, W, max(vel, 20)])
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=1, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_flute():
    """笛子 - main melody (flute)."""
    print("Composing 笛子 Flute...")
    track = "笛子 Flute"
    
    notes = []
    
    # Intro: silence, then a simple melody tease (bars 8-9)
    notes.append([A4, bar_to_ppq(8, 0), DH, 70])
    notes.append([G4, bar_to_ppq(8, 3), Q, 70])
    notes.append([D5, bar_to_ppq(9, 0), W, 80])
    
    # Theme A (bars 10-19): Main melody
    # Melody: G4-A4-D5-D5-C5-A4-G4 | F4-G4-C5-A4-G4-D4-F4 |
    theme_a = [
        (G4, DQ), (A4, E), (D5, Q), (D5, E), (C5, E), (A4, DQ), (G4, E), (rest := True),
        (F4, DQ), (G4, E), (C5, Q), (A4, E), (G4, DQ), (D4, E), (F4, Q), (G4, Q),
    ]
    bar = 10
    beat = 0
    for item in theme_a:
        if item is True:
            beat += 1
            if beat >= 4:
                beat = 0
                bar += 1
            continue
        pitch, dur = item
        pos = bar_to_ppq(bar, beat)
        actual_dur = min(dur, dur_ppq(4 - beat))
        notes.append([pitch, pos, actual_dur, 75])
        beat += (actual_dur / PPQ_PER_BEAT)
        while beat >= 4:
            beat -= 4
            bar += 1
    
    # Theme B (bars 20-30): Variation
    theme_b = [
        (D5, Q), (C5, Q), (A4, H), 
        (rest := True), (rest := True), (rest := True), (rest := True),
        (G4, Q), (A4, Q), (D5, DQ), (C5, E), 
        (A4, H), (G4, H),
        (rest := True), (rest := True), (rest := True), (rest := True), 
        (D5, Q), (A4, Q), (D5, Q), (F5, Q),
        (G5, H), (F5, E), (D5, E), (C5, Q),
    ]
    bar = 20
    beat = 0
    for item in theme_b:
        if item is True:
            beat += 1
            if beat >= 4:
                beat = 0
                bar += 1
            continue
        pitch, dur = item
        pos = bar_to_ppq(bar, beat)
        actual_dur = min(dur, dur_ppq(4 - beat))
        notes.append([pitch, pos, actual_dur, 80])
        beat += (actual_dur / PPQ_PER_BEAT)
        while beat >= 4:
            beat -= 4
            bar += 1
    
    # Climax (bars 31-48): Peak melody
    climax_melody = [
        # Bars 31-34: Soaring
        (D5, H), (F5, H), (G5, H), (A5, DQ), (G5, E), (F5, Q),
        (rest := True),
        # Bars 35-38: Emotional peak
        (D5, H), (A5, DQ), (G5, E), (F5, Q), (D5, DQ), (rest := True), (rest := True),
        # Bars 39-42: Variation
        (D6, Q), (C6, Q), (A5, H), (G5, DQ), (F5, E), (D5, Q), (F5, Q),
        # Bars 43-46
        (G5, H), (A5, H), (D6, DQ), (C6, E), (A5, Q), (G5, Q),
        # Bars 47-48: Hold
        (D5, W), (rest := True), (rest := True), (rest := True),
    ]
    bar = 31
    beat = 0
    for item in climax_melody:
        if item is True:
            beat += 1
            if beat >= 4:
                beat = 0
                bar += 1
            continue
        pitch, dur = item
        pos = bar_to_ppq(bar, beat)
        actual_dur = min(dur, dur_ppq(4 - beat))
        notes.append([pitch, pos, actual_dur, 95])
        beat += (actual_dur / PPQ_PER_BEAT)
        while beat >= 4:
            beat -= 4
            bar += 1
    
    # Resolution (bars 49-58): Gentle coda
    coda = [
        (D5, W), (rest := True), (rest := True), (rest := True),
        (A4, H), (G4, H), (F4, W), (rest := True), (rest := True), (rest := True),
        (D4, W), (rest := True), (rest := True), (rest := True),
        (D4, DH), (rest := True),
    ]
    bar = 49
    beat = 0
    for item in coda:
        if item is True:
            beat += 1
            if beat >= 4:
                beat = 0
                bar += 1
            continue
        pitch, dur = item
        pos = bar_to_ppq(bar, beat)
        actual_dur = min(dur, dur_ppq(4 - beat))
        notes.append([pitch, pos, actual_dur, 80 - (bar - 49) * 7])
        beat += (actual_dur / PPQ_PER_BEAT)
        while beat >= 4:
            beat -= 4
            bar += 1
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=2, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_koto():
    """古筝 - plucked accompaniment, arpeggios."""
    print("Composing 古筝 Koto...")
    track = "古筝 Koto"
    
    notes = []
    
    # Intro: sparse plucks (bars 1-9)
    for bar in [1, 3, 5, 7, 9]:
        notes.append([D4, bar_to_ppq(bar, 0), Q, 60])
        notes.append([A3, bar_to_ppq(bar, 1), Q, 60])
        notes.append([G3, bar_to_ppq(bar, 2), Q, 60])
        notes.append([D3, bar_to_ppq(bar, 3), Q, 60])
    
    # Development: arpeggio patterns
    dm_arp = [(D4, E), (F4, E), (A4, E), (D5, E)] * 2  # 1 bar of arp
    am_arp = [(A3, E), (C4, E), (E4, E), (A4, E)] * 2
    g_arp  = [(G3, E), (B3, E), (D4, E), (G4, E)] * 2
    c_arp  = [(C4, E), (E4, E), (G4, E), (C5, E)] * 2
    
    pattern_sequence = [dm_arp] * 4 + [am_arp] * 2 + [g_arp] * 2 + [dm_arp] * 2
    for bar_idx, arp in enumerate(pattern_sequence):
        bar = bar_idx + 10
        for beat, (pitch, dur) in enumerate(arp):
            pos = bar_to_ppq(bar, beat * 0.5)
            notes.append([pitch, pos, dur, 65])
    
    pattern_sequence2 = [dm_arp] * 2 + [c_arp] * 2 + [g_arp] * 2 + [dm_arp] * 4
    for bar_idx, arp in enumerate(pattern_sequence2):
        bar = bar_idx + 20
        for beat, (pitch, dur) in enumerate(arp):
            pos = bar_to_ppq(bar, beat * 0.5)
            notes.append([pitch, pos, dur, 75])
    
    # Climax: strong arpeggios
    for bar in range(31, 48):
        if bar % 2 == 0:
            arp = [(D4, E), (F4, E), (A4, E), (D5, E), (F5, E), (D5, E), (A4, E), (F4, E)]
        elif bar % 4 == 1:
            arp = [(A3, E), (C4, E), (E4, E), (A4, E), (C5, E), (A4, E), (E4, E), (C4, E)]
        else:
            arp = [(G3, E), (B3, E), (D4, E), (G4, E), (B4, E), (G4, E), (D4, E), (B3, E)]
        for beat, (pitch, dur) in enumerate(arp):
            pos = bar_to_ppq(bar, beat * 0.5)
            notes.append([pitch, pos, dur, 85])
    
    # Coda: gentle plucks
    for bar in range(49, 58):
        vel = 70 - (bar - 49) * 5
        notes.append([D4, bar_to_ppq(bar, 0), Q, vel])
        notes.append([A3, bar_to_ppq(bar, 1), Q, vel])
        if bar % 2 == 0:
            notes.append([F4, bar_to_ppq(bar, 2), Q, vel])
            
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=3, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_drums():
    """大鼓 - ceremonial percussion, GM drum map."""
    print("Composing 大鼓 Drums...")
    track = "大鼓 Drums"
    
    BD = 36       # Bass Drum (大鼓)
    CRASH = 49    # Crash Cymbal (大镲)
    WOOD_H = 76   # High Wood Block (木鱼高)
    WOOD_L = 77   # Low Wood Block (木鱼低)
    SNARE = 38    # Snare
    RIDE = 51     # Ride Cymbal
    
    notes = []
    
    # Intro: very sparse - ceremony feel
    for bar in [1, 3, 5, 7]:
        notes.append([WOOD_H, bar_to_ppq(bar, 0), E, 80])
        notes.append([WOOD_L, bar_to_ppq(bar, 2), E, 80])
    notes.append([BD, bar_to_ppq(9, 0), Q, 100])  # Big drum at end of intro
    notes.append([CRASH, bar_to_ppq(9, 0), E, 90])
    
    # Development A: gentle pulse
    for bar in range(10, 20):
        notes.append([WOOD_L, bar_to_ppq(bar, 0), E, 60])
        notes.append([WOOD_H, bar_to_ppq(bar, 2), E, 60])
        if bar % 4 == 0:
            notes.append([BD, bar_to_ppq(bar, 0), Q, 70])
    
    # Development B: stronger
    for bar in range(20, 30):
        notes.append([BD, bar_to_ppq(bar, 0), Q, 80])
        notes.append([WOOD_L, bar_to_ppq(bar, 1), E, 70])
        notes.append([WOOD_H, bar_to_ppq(bar, 2), E, 70])
        if bar % 2 == 0:
            notes.append([SNARE, bar_to_ppq(bar, 3), E, 60])
    
    # Build up (bars 30-31)
    for beat in range(8):
        notes.append([BD, bar_to_ppq(30, beat * 0.5), E, 90 + beat * 5])
    notes.append([CRASH, bar_to_ppq(31, 0), E, 100])
    
    # Climax: full percussion
    for bar in range(31, 48):
        notes.append([BD, bar_to_ppq(bar, 0), Q, 100])
        notes.append([BD, bar_to_ppq(bar, 2), Q, 90])
        if bar % 2 == 0:
            notes.append([SNARE, bar_to_ppq(bar, 1), E, 70])
        if bar % 4 == 0:
            notes.append([CRASH, bar_to_ppq(bar, 0), E, 90])
    
    # Resolution: fade percussion
    for bar in range(49, 55):
        vel = 80 - (bar - 49) * 15
        notes.append([BD, bar_to_ppq(bar, 0), Q, max(vel, 20)])
        if bar % 2 == 0:
            notes.append([WOOD_L, bar_to_ppq(bar, 2), E, max(vel - 10, 10)])
    
    # Final
    notes.append([BD, bar_to_ppq(56, 0), Q, 80])
    notes.append([CRASH, bar_to_ppq(56, 0), E, 70])
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=9, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_cello():
    """大提琴 - bass foundation."""
    print("Composing 大提琴 Cello...")
    track = "大提琴 Cello"
    
    notes = []
    
    # Simple bass line following the chord progression
    # Intro: hold D
    for bar in range(1, 9):
        notes.append([D2, bar_to_ppq(bar, 0), W, 55])
    notes.append([D2, bar_to_ppq(9, 0), H, 60])
    
    # Development: root notes of chords
    bass_line = [
        (D2, 4), (A1, 2), (G1, 2), (D2, 2),  # bars 10-19
    ]
    bar = 10
    for pitch, n_bars in bass_line:
        for b in range(n_bars):
            notes.append([pitch, bar_to_ppq(bar + b, 0), W, 70])
        bar += n_bars
    
    bass_line2 = [
        (D2, 2), (A1, 2), (G1, 2), (C2, 2), (D2, 2),  # bars 20-29
    ]
    bar = 20
    for pitch, n_bars in bass_line2:
        for b in range(n_bars):
            notes.append([pitch, bar_to_ppq(bar + b, 0), W, 80])
        bar += n_bars
    
    # Climax: moving bass
    for bar in range(31, 48):
        if bar % 2 == 0:
            notes.append([D2, bar_to_ppq(bar, 0), H, 90])
            notes.append([A1, bar_to_ppq(bar, 2), H, 85])
        elif bar % 4 == 1:
            notes.append([G1, bar_to_ppq(bar, 0), DH, 90])
            notes.append([A1, bar_to_ppq(bar, 3), Q, 85])
        else:
            notes.append([C2, bar_to_ppq(bar, 0), H, 85])
            notes.append([D2, bar_to_ppq(bar, 2), H, 90])
    
    # Coda
    for bar in range(49, 58):
        vel = 75 - (bar - 49) * 7
        notes.append([D2, bar_to_ppq(bar, 0), W, max(vel, 15)])
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=4, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def compose_choir():
    """合唱 - ambient choir pads."""
    print("Composing 合唱 Choir...")
    track = "合唱 Choir"
    
    notes = []
    
    # Choir enters in development B, stays through climax
    # Bars 20-30: Soft choir
    for bar in range(20, 30, 2):
        notes.append([A4, bar_to_ppq(bar, 0), DH, 50])
        notes.append([D5, bar_to_ppq(bar, 0), DH, 50])
    
    # Climax: Full choir power
    for bar in range(31, 48):
        vel = 70 if bar < 40 else 85
        # Long "ah" chord
        chord = [D4, F4, A4] if bar % 2 == 0 else [G4, B4, D5]
        for pitch in chord:
            notes.append([pitch, bar_to_ppq(bar, 0), W, vel])
    
    # Resolution: fade
    for bar in range(49, 56, 2):
        vel = 60 - (bar - 49) * 8
        notes.append([D4, bar_to_ppq(bar, 0), W, vel])
        notes.append([A4, bar_to_ppq(bar, 0), W, vel])
    
    r = await call('reaper_insert_midi_notes_batch', track_name=track, item_index=0, channel=5, notes=notes)
    print(f"  {r['data']['inserted_count']} notes inserted, errors: {len(r['data']['errors'])}")

async def set_volumes():
    """Balance track volumes."""
    print("Setting track volumes...")
    settings = [
        ("编钟 Bells", -3.0),
        ("弦乐 Strings", -6.0),
        ("笛子 Flute", -4.0),
        ("古筝 Koto", -5.0),
        ("大鼓 Drums", -4.0),
        ("大提琴 Cello", -5.0),
        ("合唱 Choir", -8.0),
    ]
    for track_name, db in settings:
        await call('reaper_set_track_volume_db', track_name=track_name, volume_db=db)
    print("  Volumes set")

async def add_markers():
    """Add section markers for the score."""
    print("Adding section markers...")
    # time_sec = (bar - 1) * 4 * 60 / BPM
    sections = [
        (0, "前奏 - 朝钟 Intro"),
        (9 * 4 * 60 / BPM, "主题A - 晨曦 Theme A"),
        (19 * 4 * 60 / BPM, "主题B - 御殿 Theme B"),
        (30 * 4 * 60 / BPM, "高潮 - 朝政 Climax"),
        (48 * 4 * 60 / BPM, "尾声 - 余韵 Coda"),
    ]
    for time_sec, name in sections:
        await call('reaper_add_marker', time=time_sec, marker_name=name)
    print("  Markers added")

async def main():
    print("=" * 60)
    print("清宫朝政 配乐创作 - Imperial Court Film Score")
    print("=" * 60)
    
    t0 = time.time()
    
    await setup_project()
    await create_tracks()
    await set_instruments()
    
    print("\n--- Composing Parts ---")
    await compose_bells()
    await compose_strings()
    await compose_cello()
    await compose_flute()
    await compose_koto()
    await compose_drums()
    await compose_choir()
    
    await set_volumes()
    await add_markers()
    
    # Save
    await call('reaper_save_project')
    
    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"配乐创作完成！总耗时: {elapsed:.1f}秒")
    print(f"项目已保存到 REAPER 工程中")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    asyncio.run(main())
