"""Final verification of the film score project."""
import os, sys, json, asyncio
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main as m

async def call(name, **kwargs):
    r = await m.mcp.call_tool(name, kwargs if kwargs else {})
    return json.loads(r[0].text)

async def main():
    print("=" * 60)
    print("FINAL VERIFICATION - 清宫朝政配乐项目")
    print("=" * 60)
    
    # 1. Project info
    r = await call('reaper_get_project_info')
    info = r.get('data', {})
    print(f"\nProject: {info.get('name')}")
    print(f"  BPM: {info.get('bpm')}")
    print(f"  Tracks: {info.get('num_tracks')}")
    print(f"  Length: {info.get('length'):.1f}s")
    
    # 2. Tracks
    r = await call('reaper_get_all_tracks')
    tracks = r.get('data', {}).get('tracks', [])
    print(f"\nTracks ({len(tracks)}):")
    for t in tracks:
        print(f"  [{t['name']}] items={t['num_items']} fx={t['num_fx']} vol={t['volume']:.2f}")
    
    # 3. MIDI notes per track
    print(f"\nMIDI Notes per track:")
    total_notes = 0
    for t in tracks:
        if t['num_items'] > 0:
            try:
                r = await call('reaper_get_midi_notes', track_name=t['name'], item_index=0)
                count = r.get('data', {}).get('count', 0)
                if count > 0:
                    notes = r.get('data', {}).get('notes', [])
                    if notes:
                        first = notes[0]
                        last = notes[-1]
                        print(f"  [{t['name']}] {count} notes - first: {first['note_name']}@{first['start_ppq']}, last: {last['note_name']}@{last['start_ppq']}")
                    else:
                        print(f"  [{t['name']}] {count} notes")
                    total_notes += count
                else:
                    # Try MIDI item info
                    r2 = await call('reaper_get_midi_item_info', track_name=t['name'], item_index=0)
                    print(f"  [{t['name']}] item info: {r2.get('data', {})}")
            except Exception as e:
                print(f"  [{t['name']}] Error: {e}")
    
    print(f"\n  TOTAL NOTES: {total_notes}")
    
    # 4. Markers
    r = await call('reaper_get_all_markers')
    markers = r.get('data', {}).get('markers', [])
    print(f"\nMarkers ({len(markers)}):")
    for m in markers:
        print(f"  [{m['position']}s] {m['name']}")
    
    # 5. Check new tools
    print(f"\nNew Tool Verification:")
    r = await call('reaper_set_midi_instrument', track_name='编钟 Bells', item_index=0, channel=0, program=14)
    print(f"  reaper_set_midi_instrument: {r.get('success')}")
    
    r = await call('reaper_insert_midi_notes_batch', track_name='编钟 Bells', item_index=0, channel=0,
                   notes=[[62, 999000, 480, 80]])
    print(f"  reaper_insert_midi_notes_batch: {r.get('success')} - inserted {r.get('data', {}).get('inserted_count', 0)}")
    
    # 6. Check if audio description / file listing works
    r = await call('reaper_list_audio_files')
    print(f"  reaper_list_audio_files: {r.get('success')} - {r.get('data', {}).get('count', 0)} files")
    
    r = await call('reaper_get_audio_description')
    print(f"  reaper_get_audio_description: {r.get('success')}")
    
    print(f"\n{'=' * 60}")
    print(f"VERIFICATION COMPLETE")
    print(f"{'=' * 60}")

asyncio.run(main())
