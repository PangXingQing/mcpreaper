"""
通过编辑 REAPER Track State Chunk 为每条 MIDI 轨道添加 MIDI 硬件输出
"""
import os
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()

midi_track_names = [
    "编钟 Bells", "弦乐 Strings", "笛子 Flute",
    "古筝 Koto", "大鼓 Drums", "大提琴 Cello", "合唱 Choir",
]

# 每条音轨对应的 MIDI 通道
channel_map = {
    "编钟 Bells": 1,
    "弦乐 Strings": 2,
    "笛子 Flute": 3,
    "古筝 Koto": 4,
    "大鼓 Drums": 10,
    "大提琴 Cello": 5,
    "合唱 Choir": 6,
}

success = 0
failed = []

for track in list(proj.tracks):
    if track.name not in midi_track_names:
        continue

    try:
        chunk = reaper.GetTrackStateChunk(track, "", 0)
        chunk_str = chunk[2] if len(chunk) > 2 else str(chunk)
        
        # MIDIOUT line format: MIDIOUT <chan> <bus> <flags>
        # <chan> = MIDI channel (0=all)  
        # <bus> = output device index (0 = Microsoft GS Wavetable Synth)
        # <flags> = 0
        chan = channel_map.get(track.name, 0)
        # channel 0 in REAPER means "all", but we specify per track
        # For channel-specific routing: chan 0-based, so ch1=0, ch2=1, etc.
        # But in state chunk, MIDIOUT uses 0=all channels
        # Let's use 0 (all channels) since each track has its own MIDI channel already set via Program Change
        
        midio_line = f"  MIDIOUT 0 0 0\n"
        
        # Check if MIDIOUT already exists
        if "MIDIOUT" in chunk_str:
            print(f"  {track.name}: MIDIOUT already exists, skipping")
            success += 1
            continue
        
        # Insert MIDIOUT before the last line (before the closing >)
        # Find MAINSEND line position or insert before WAK
        lines = chunk_str.split('\n')
        insert_idx = None
        
        # Insert before MAINSEND line
        for i, line in enumerate(lines):
            if line.strip().startswith('MAINSEND'):
                insert_idx = i
                break
        
        if insert_idx is None:
            # Insert before the closing >
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == '>':
                    insert_idx = i
                    break
        
        if insert_idx is not None:
            lines.insert(insert_idx, midio_line.rstrip('\n'))
            new_chunk = '\n'.join(lines)
            
            result = reaper.SetTrackStateChunk(track, new_chunk, False)
            print(f"  {track.name}: MIDIOUT 添加成功 (chan={chan})")
            success += 1
        else:
            print(f"  {track.name}: 无法找到插入位置")
            failed.append(track.name)

    except Exception as e:
        print(f"  {track.name}: 错误 - {e}")
        failed.append(track.name)

print(f"\n成功: {success}/7, 失败: {len(failed)}")
if failed:
    print(f"失败的轨道: {failed}")

# 验证
print("\n=== 验证结果 ===")
for track in list(proj.tracks):
    if track.name in midi_track_names:
        chunk = reaper.GetTrackStateChunk(track, "", 0)
        chunk_str = chunk[2] if len(chunk) > 2 else str(chunk)
        has_midio = "MIDIOUT" in chunk_str
        print(f"  {track.name}: MIDIOUT={'YES' if has_midio else 'NO'}")
