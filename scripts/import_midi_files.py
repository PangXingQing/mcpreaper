"""Import generated MIDI files into REAPER via InsertMedia"""
import os
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()
print(f'Project: {proj.name}')

# Clean all tracks
print(f'Current tracks: {len(list(proj.tracks))}')
reaper.Main_OnCommand(40296, 0)  # Select all
reaper.Main_OnCommand(40005, 0)  # Remove
print(f'After clean: {len(list(proj.tracks))}')

# Import MIDI files
midi_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ReaperProject')
midi_files = [
    '01_Bells.mid',
    '02_Strings.mid',
    '03_Flute.mid',
    '04_Koto.mid',
    '05_Drums.mid',
    '06_Cello.mid',
    '07_Choir.mid',
]

track_names = [
    '编钟 Bells',
    '弦乐 Strings',
    '笛子 Flute',
    '古筝 Koto',
    '大鼓 Drums',
    '大提琴 Cello',
    '合唱 Choir',
]

for i, filename in enumerate(midi_files):
    filepath = os.path.join(midi_dir, filename)
    if not os.path.exists(filepath):
        print(f'MISSING: {filepath}')
        continue
    
    print(f'Importing {filename}...')
    reaper.InsertMedia(filepath, 0)  # mode 0 = add as new track

# Verify
print(f'\nAfter import: {len(list(proj.tracks))} tracks')
total_notes = 0
for t in list(proj.tracks):
    items = list(t.items)
    track_notes = 0
    for item in items:
        if item.takes:
            take = item.takes[0]
            is_midi = reaper.TakeIsMIDI(take)
            nn = reaper.MIDI_CountEvts(take, 0, 0, 0)[2]
            track_notes += nn
            if nn > 0:
                print(f'  {t.name}: isMIDI={is_midi}, {nn} events')
    total_notes += track_notes

print(f'\nTotal MIDI events: {total_notes}')

# Rename tracks
for t in list(proj.tracks):
    name = t.name
    if name.endswith('.mid'):
        base = name[:-4]
        # Map to Chinese names
        name_map = {
            '01_Bells': '编钟 Bells',
            '02_Strings': '弦乐 Strings',
            '03_Flute': '笛子 Flute',
            '04_Koto': '古筝 Koto',
            '05_Drums': '大鼓 Drums',
            '06_Cello': '大提琴 Cello',
            '07_Choir': '合唱 Choir',
        }
        new_name = name_map.get(name, name)
        try:
            t.name = new_name
            print(f'Renamed: {name} -> {new_name}')
        except Exception as e:
            print(f'Rename {name} failed: {e}')

# Set track volumes
volume_map = {
    '编钟 Bells': -3.0,
    '弦乐 Strings': -6.0,
    '笛子 Flute': -4.0,
    '古筝 Koto': -5.0,
    '大鼓 Drums': -4.0,
    '大提琴 Cello': -5.0,
    '合唱 Choir': -8.0,
}
for t in list(proj.tracks):
    if t.name in volume_map:
        linear = 10 ** (volume_map[t.name] / 20.0)
        try:
            t.volume = linear
        except:
            pass

# Set BPM and save
try:
    reaper.SetCurrentBPM(proj, 78, False)
except:
    pass
proj.save()
print('\nProject saved!')
