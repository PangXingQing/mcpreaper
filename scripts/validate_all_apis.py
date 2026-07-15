"""
Comprehensive MCP API validation test.
Tests every MCP tool against REAPER at 192.168.1.8:2307.
"""
import os, sys, json, asyncio, traceback

os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as mcp_main

passed = 0
failed = 0
errors = []

async def test(name, category, fn):
    global passed, failed
    try:
        result = await fn()
        if isinstance(result, dict):
            if result.get('success'):
                passed += 1
                print(f'  PASS [{category}] {name}')
                return True
            else:
                err = result.get('error', '?')
                print(f'  FAIL [{category}] {name}: {err[:100]}')
                failed += 1
                errors.append((f'[{category}] {name}', result))
                return False
        else:
            passed += 1
            print(f'  PASS [{category}] {name}')
            return True
    except Exception as e:
        failed += 1
        print(f'  ERROR [{category}] {name}: {e}')
        errors.append((f'[{category}] {name}', str(e)))
        return False

async def test_expected_fail(name, category, fn):
    """Test that expects success=False (error handling test)"""
    global passed, failed
    try:
        result = await fn()
        if isinstance(result, dict) and not result.get('success'):
            passed += 1
            print(f'  PASS [{category}] {name} (correctly rejected)')
            return True
        else:
            failed += 1
            print(f'  FAIL [{category}] {name}: should have been rejected')
            errors.append((f'[{category}] {name}', 'Expected rejection'))
            return False
    except Exception as e:
        failed += 1
        print(f'  ERROR [{category}] {name}: {e}')
        errors.append((f'[{category}] {name}', str(e)))
        return False

async def call(name, **kwargs):
    """Call MCP tool and return parsed result."""
    r = await mcp_main.mcp.call_tool(name, kwargs if kwargs else {})
    return json.loads(r[0].text)

async def run_all_tests():
    global passed, failed, errors
    
    print('=' * 70)
    print('MCP API Comprehensive Validation Test')
    print('=' * 70)
    
    # ============ 1. PROJECT TOOLS ============
    print('\n--- 1. Project Tools ---')
    
    await test('reaper_get_project_info', 'project',
               lambda: call('reaper_get_project_info'))
    
    await test('reaper_get_project_bpm', 'project',
               lambda: call('reaper_get_project_bpm'))
    
    await test('reaper_set_project_bpm (90)', 'project',
               lambda: call('reaper_set_project_bpm', bpm=90.0))
    
    await test('reaper_set_project_bpm (120)', 'project',
               lambda: call('reaper_set_project_bpm', bpm=120.0))
    
    await test_expected_fail('reaper_set_project_bpm (invalid)', 'project',
               lambda: call('reaper_set_project_bpm', bpm=500))
    
    await test('reaper_set_project_time_signature (4/4)', 'project',
               lambda: call('reaper_set_project_time_signature', numerator=4, denominator=4))
    
    await test('reaper_set_project_time_signature (3/4)', 'project',
               lambda: call('reaper_set_project_time_signature', numerator=3, denominator=4))
    
    await test('reaper_save_project', 'project',
               lambda: call('reaper_save_project'))
    
    await test('reaper_calculate_normalization', 'project',
               lambda: call('reaper_calculate_normalization', track_name='__MCP_TEST__'))

    # ============ 2. TRACK TOOLS ============
    print('\n--- 2. Track Tools ---')
    
    await test('reaper_add_track (Bass)', 'track',
               lambda: call('reaper_add_track', track_name='Bass'))
    
    await test('reaper_add_track (Melody)', 'track',
               lambda: call('reaper_add_track', track_name='Melody'))
    
    await test('reaper_add_track (Drums)', 'track',
               lambda: call('reaper_add_track', track_name='Drums'))
    
    await test('reaper_add_track (Strings)', 'track',
               lambda: call('reaper_add_track', track_name='Strings'))
    
    await test_expected_fail('reaper_add_track (empty)', 'track',
               lambda: call('reaper_add_track', track_name=''))
    
    await test('reaper_get_all_tracks', 'track',
               lambda: call('reaper_get_all_tracks'))
    
    await test('reaper_get_all_track_names', 'track',
               lambda: call('reaper_get_all_track_names'))
    
    await test('reaper_get_track_info (Bass)', 'track',
               lambda: call('reaper_get_track_info', track_name='Bass'))
    
    await test('reaper_select_track (Bass)', 'track',
               lambda: call('reaper_select_track', track_name='Bass'))
    
    await test_expected_fail('reaper_select_track (nonexistent)', 'track',
               lambda: call('reaper_select_track', track_name='__nonexistent__'))
    
    await test('reaper_rename_track', 'track',
               lambda: call('reaper_rename_track', track_name='Bass', new_name='Bass_renamed'))
    
    await test('reaper_rename_track (back)', 'track',
               lambda: call('reaper_rename_track', track_name='Bass_renamed', new_name='Bass'))
    
    await test('reaper_set_track_volume', 'track',
               lambda: call('reaper_set_track_volume', track_name='Bass', volume=0.8))
    
    await test_expected_fail('reaper_set_track_volume (invalid)', 'track',
               lambda: call('reaper_set_track_volume', track_name='__nonexistent__', volume=1.0))
    
    await test('reaper_set_track_volume_db', 'track',
               lambda: call('reaper_set_track_volume_db', track_name='Bass', volume_db=-6.0))
    
    await test('reaper_set_track_pan', 'track',
               lambda: call('reaper_set_track_pan', track_name='Bass', pan=0.3))
    
    await test('reaper_set_track_mute (True)', 'track',
               lambda: call('reaper_set_track_mute', track_name='Bass', mute=True))
    
    await test('reaper_set_track_mute (False)', 'track',
               lambda: call('reaper_set_track_mute', track_name='Bass', mute=False))
    
    await test('reaper_set_track_solo (True)', 'track',
               lambda: call('reaper_set_track_solo', track_name='Bass', solo=True))
    
    await test('reaper_set_track_solo (False)', 'track',
               lambda: call('reaper_set_track_solo', track_name='Bass', solo=False))
    
    await test('reaper_set_track_rec_arm (True)', 'track',
               lambda: call('reaper_set_track_rec_arm', track_name='Bass', rec_arm=True))
    
    await test('reaper_set_track_rec_arm (False)', 'track',
               lambda: call('reaper_set_track_rec_arm', track_name='Bass', rec_arm=False))

    # ============ 3. MIDI TOOLS ============
    print('\n--- 3. MIDI Tools ---')
    
    await test('reaper_create_midi_item (Melody)', 'midi',
               lambda: call('reaper_create_midi_item', track_name='Melody', start_time=0, length=10.0))
    
    await test('reaper_create_midi_item (Bass)', 'midi',
               lambda: call('reaper_create_midi_item', track_name='Bass', start_time=0, length=10.0))
    
    await test('reaper_insert_midi_note', 'midi',
               lambda: call('reaper_insert_midi_note', track_name='Melody', item_index=0, pitch=60, start_ppq=0, duration_ppq=480, velocity=100))
    
    await test('reaper_insert_midi_note (2nd note)', 'midi',
               lambda: call('reaper_insert_midi_note', track_name='Melody', item_index=0, pitch=64, start_ppq=480, duration_ppq=480, velocity=90))
    
    await test('reaper_insert_midi_note (3rd note)', 'midi',
               lambda: call('reaper_insert_midi_note', track_name='Melody', item_index=0, pitch=67, start_ppq=960, duration_ppq=480, velocity=80))
    
    await test('reaper_get_midi_notes', 'midi',
               lambda: call('reaper_get_midi_notes', track_name='Melody', item_index=0))
    
    await test('reaper_set_midi_note_velocity', 'midi',
               lambda: call('reaper_set_midi_note_velocity', track_name='Melody', item_index=0, note_index=0, velocity=110))
    
    await test('reaper_get_midi_notes (after velocity change)', 'midi',
               lambda: call('reaper_get_midi_notes', track_name='Melody', item_index=0))
    
    await test_expected_fail('reaper_create_midi_item (bad track)', 'midi',
               lambda: call('reaper_create_midi_item', track_name='__nonexistent__', start_time=0, length=1.0))
    
    await test_expected_fail('reaper_insert_midi_note (bad pitch)', 'midi',
               lambda: call('reaper_insert_midi_note', track_name='Melody', item_index=0, pitch=200, start_ppq=0, duration_ppq=480, velocity=100))
    
    await test_expected_fail('reaper_insert_midi_note (bad velocity)', 'midi',
               lambda: call('reaper_insert_midi_note', track_name='Melody', item_index=0, pitch=60, start_ppq=0, duration_ppq=480, velocity=200))

    # ============ 4. MIDI EXT TOOLS ============
    print('\n--- 4. MIDI Ext Tools ---')
    
    await test('reaper_insert_midi_cc', 'midi_ext',
               lambda: call('reaper_insert_midi_cc', track_name='Melody', item_index=0, cc_number=7, position_ppq=0, value=100, channel=0))
    
    await test('reaper_get_midi_cc_events', 'midi_ext',
               lambda: call('reaper_get_midi_cc_events', track_name='Melody', item_index=0))
    
    await test('reaper_insert_midi_text_event', 'midi_ext',
               lambda: call('reaper_insert_midi_text_event', track_name='Melody', item_index=0, position_ppq=0, text='Test Marker', event_type=3))
    
    await test('reaper_get_midi_text_events', 'midi_ext',
               lambda: call('reaper_get_midi_text_events', track_name='Melody', item_index=0))
    
    await test('reaper_get_midi_item_info', 'midi_ext',
               lambda: call('reaper_get_midi_item_info', track_name='Melody', item_index=0))
    
    await test('reaper_quantize_midi_notes', 'midi_ext',
               lambda: call('reaper_quantize_midi_notes', track_name='Melody', item_index=0, grid_div=16, strength=100))
    
    await test('reaper_transpose_midi_notes (+2)', 'midi_ext',
               lambda: call('reaper_transpose_midi_notes', track_name='Melody', item_index=0, semitones=2))
    
    await test('reaper_transpose_midi_notes (-2)', 'midi_ext',
               lambda: call('reaper_transpose_midi_notes', track_name='Melody', item_index=0, semitones=-2))

    # ============ 5. MARKER TOOLS ============
    print('\n--- 5. Marker Tools ---')
    
    await test('reaper_add_marker', 'marker',
               lambda: call('reaper_add_marker', time=1.0, marker_name='TestMarker'))
    
    await test('reaper_add_region', 'marker',
               lambda: call('reaper_add_region', start_time=0.0, end_time=2.0, region_name='TestRegion'))
    
    await test('reaper_get_all_markers', 'marker',
               lambda: call('reaper_get_all_markers'))
    
    await test('reaper_go_to_marker', 'marker',
               lambda: call('reaper_go_to_marker', index=1))
    
    await test('reaper_rename_marker', 'marker',
               lambda: call('reaper_rename_marker', index=0, new_name='RenamedMarker'))
    
    await test('reaper_rename_marker (back)', 'marker',
               lambda: call('reaper_rename_marker', index=0, new_name='TestMarker'))

    # ============ 6. ITEM TOOLS ============
    print('\n--- 6. Item Tools ---')
    
    await test('reaper_get_track_items (Melody)', 'item',
               lambda: call('reaper_get_track_items', track_name='Melody'))
    
    await test('reaper_move_item', 'item',
               lambda: call('reaper_move_item', track_name='Melody', item_index=0, new_position=1.0))
    
    await test('reaper_move_item (back)', 'item',
               lambda: call('reaper_move_item', track_name='Melody', item_index=0, new_position=0.0))
    
    await test('reaper_resize_item', 'item',
               lambda: call('reaper_resize_item', track_name='Melody', item_index=0, new_length=8.0))
    
    await test('reaper_set_item_volume', 'item',
               lambda: call('reaper_set_item_volume', track_name='Melody', item_index=0, volume=1.0))
    
    await test('reaper_set_item_pan', 'item',
               lambda: call('reaper_set_item_pan', track_name='Melody', item_index=0, pan=0.0))

    # ============ 7. PLAYBACK TOOLS ============
    print('\n--- 7. Playback Tools ---')
    
    await test('reaper_get_play_position', 'playback',
               lambda: call('reaper_get_play_position'))
    
    await test('reaper_go_to_start', 'playback',
               lambda: call('reaper_go_to_start'))
    
    await test('reaper_go_to_end', 'playback',
               lambda: call('reaper_go_to_end'))
    
    await test('reaper_set_play_position', 'playback',
               lambda: call('reaper_set_play_position', time=5.0))

    # ============ 8. FX TOOLS ============
    print('\n--- 8. FX Tools ---')
    
    await test('reaper_add_fx_to_track (ReaEQ)', 'fx',
               lambda: call('reaper_add_fx_to_track', track_name='Melody', fx_name='ReaEQ'))
    
    await test('reaper_get_track_fx_list', 'fx',
               lambda: call('reaper_get_track_fx_list', track_name='Melody'))
    
    await test('reaper_toggle_fx', 'fx',
               lambda: call('reaper_toggle_fx', track_name='Melody', fx_index=0))
    
    await test('reaper_toggle_fx (back)', 'fx',
               lambda: call('reaper_toggle_fx', track_name='Melody', fx_index=0))
    
    await test('reaper_get_fx_params', 'fx',
               lambda: call('reaper_get_fx_params', track_name='Melody', fx_index=0))
    
    await test('reaper_set_fx_param', 'fx',
               lambda: call('reaper_set_fx_param', track_name='Melody', fx_index=0, param_index=0, value=0.5))
    
    await test('reaper_bypass_all_fx', 'fx',
               lambda: call('reaper_bypass_all_fx', track_name='Melody', bypass=True))
    
    await test('reaper_bypass_all_fx (restore)', 'fx',
               lambda: call('reaper_bypass_all_fx', track_name='Melody', bypass=False))

    # ============ 9. EQ TOOLS ============
    print('\n--- 9. EQ Tools ---')
    
    await test('reaper_add_reaeq', 'eq',
               lambda: call('reaper_add_reaeq', track_name='Bass'))
    
    await test('reaper_set_reaeq_band', 'eq',
               lambda: call('reaper_set_reaeq_band', track_name='Bass', band_index=0, freq_hz=80, gain_db=-3.0, q_factor=1.0, filter_type=1))
    
    await test('reaper_get_reaeq_band', 'eq',
               lambda: call('reaper_get_reaeq_band', track_name='Bass', band_index=0))
    
    await test('reaper_apply_eq_preset', 'eq',
               lambda: call('reaper_apply_eq_preset', track_name='Bass', preset_name='Bass Cut'))
    
    await test('reaper_add_reacomp', 'eq',
               lambda: call('reaper_add_reacomp', track_name='Bass'))
    
    await test('reaper_set_reacomp_params', 'eq',
               lambda: call('reaper_set_reacomp_params', track_name='Bass', threshold_db=-18, ratio=4.0, attack_ms=10, release_ms=100, knee_db=3))
    
    await test('reaper_add_reafir', 'eq',
               lambda: call('reaper_add_reafir', track_name='Bass'))

    # ============ 10. ENVELOPE TOOLS ============
    print('\n--- 10. Envelope Tools ---')
    
    await test('reaper_get_track_envelopes', 'envelope',
               lambda: call('reaper_get_track_envelopes', track_name='Melody'))
    
    # Envelopes may be empty for MIDI tracks, skip if no envelopes
    env_result = await call('reaper_get_track_envelopes', track_name='Melody')
    envs = env_result.get('data', {}).get('envelopes', [])
    if envs:
        await test('reaper_add_envelope_point', 'envelope',
                   lambda: call('reaper_add_envelope_point', track_name='Melody', envelope_index=0, time=1.0, value=0.5, shape=0))
        
        await test('reaper_get_envelope_points', 'envelope',
                   lambda: call('reaper_get_envelope_points', track_name='Melody', envelope_index=0))
        
        await test('reaper_get_envelope_value_at_time', 'envelope',
                   lambda: call('reaper_get_envelope_value_at_time', track_name='Melody', envelope_index=0, time=1.0))
        
        await test('reaper_clear_envelope_points', 'envelope',
                   lambda: call('reaper_clear_envelope_points', track_name='Melody', envelope_index=0))
    else:
        print('  SKIP envelope tests (no envelopes available)')

    # ============ 11. SEND TOOLS ============
    print('\n--- 11. Send Tools ---')
    
    await test('reaper_create_track_send', 'send',
               lambda: call('reaper_create_track_send', source_track_name='Melody', destination_track_name='Bass'))
    
    await test('reaper_get_track_sends', 'send',
               lambda: call('reaper_get_track_sends', track_name='Melody'))
    
    await test('reaper_set_send_volume', 'send',
               lambda: call('reaper_set_send_volume', track_name='Melody', send_index=0, volume=0.7))
    
    await test('reaper_set_send_pan', 'send',
               lambda: call('reaper_set_send_pan', track_name='Melody', send_index=0, pan=0.0))
    
    await test('reaper_get_track_receives', 'send',
               lambda: call('reaper_get_track_receives', track_name='Bass'))

    # ============ 12. GENERATE TOOLS ============
    print('\n--- 12. Generate Tools ---')
    
    await test('reaper_generate_sine_wave', 'generate',
               lambda: call('reaper_generate_sine_wave', frequency=440, duration=0.5, amplitude=0.3))
    
    await test('reaper_generate_square_wave', 'generate',
               lambda: call('reaper_generate_square_wave', frequency=220, duration=0.5, amplitude=0.2))
    
    await test('reaper_generate_triangle_wave', 'generate',
               lambda: call('reaper_generate_triangle_wave', frequency=330, duration=0.5, amplitude=0.2))
    
    await test('reaper_generate_sawtooth_wave', 'generate',
               lambda: call('reaper_generate_sawtooth_wave', frequency=110, duration=0.5, amplitude=0.2))
    
    await test('reaper_generate_noise (white)', 'generate',
               lambda: call('reaper_generate_noise', duration=0.3, amplitude=0.1, noise_type='white'))
    
    await test('reaper_generate_chord (C major)', 'generate',
               lambda: call('reaper_generate_chord', chord_notes=[261.63, 329.63, 392.0], duration=0.5, amplitude=0.2))

    # ============ 13. AUDIO TOOLS (if audio items exist) ============
    print('\n--- 13. Audio Tools ---')
    
    # Get tracks that have audio items
    all_tracks = await call('reaper_get_all_tracks')
    audio_tracks = [t for t in all_tracks.get('data', {}).get('tracks', []) if t['num_items'] > 0 and t['name'] not in ('Melody', 'Bass', 'Drums', 'Strings')]
    
    if audio_tracks:
        test_track = audio_tracks[0]['name']
        print(f'  Testing audio tools on track: {test_track}')
        
        items = await call('reaper_get_track_items', track_name=test_track)
        audio_items = items.get('data', {}).get('items', [])
        if audio_items:
            await test('reaper_get_audio_item_info', 'audio',
                       lambda: call('reaper_get_audio_item_info', track_name=test_track, item_index=0))
            
            await test('reaper_fade_audio_item', 'audio',
                       lambda: call('reaper_fade_audio_item', track_name=test_track, item_index=0, fade_in_length=0.1, fade_out_length=0.1))
            
            await test('reaper_normalize_audio_item', 'audio',
                       lambda: call('reaper_normalize_audio_item', track_name=test_track, item_index=0, target_db=-1.0))
    else:
        print('  SKIP audio tools (no audio items in test tracks)')

    # ============ 14. RENDER TOOLS (non-destructive) ============
    print('\n--- 14. Render Tools ---')
    
    await test('reaper_get_render_settings', 'render',
               lambda: call('reaper_get_render_settings'))
    
    await test('reaper_set_render_settings', 'render',
               lambda: call('reaper_set_render_settings', sample_rate=44100, bit_depth=24))

    # ============ 15. FILM TOOLS (non-destructive) ============
    print('\n--- 15. Film Tools ---')
    
    await test('reaper_get_video_info', 'film',
               lambda: call('reaper_get_video_info'))
    
    await test('reaper_set_frame_rate', 'film',
               lambda: call('reaper_set_frame_rate', frame_rate=24.0))
    
    await test('reaper_set_timecode_format', 'film',
               lambda: call('reaper_set_timecode_format', format_type='SMPTE'))
    
    await test('reaper_set_start_timecode', 'film',
               lambda: call('reaper_set_start_timecode', hours=1, minutes=0, seconds=0, frames=0))
    
    await test('reaper_set_start_timecode (reset)', 'film',
               lambda: call('reaper_set_start_timecode', hours=0, minutes=0, seconds=0, frames=0))
    
    await test('reaper_set_sync_reference', 'film',
               lambda: call('reaper_set_sync_reference', mode='Internal'))
    
    await test('reaper_insert_cue_marker', 'film',
               lambda: call('reaper_insert_cue_marker', time=5.0, cue_name='CUE_A', color=0))

    # ============ 16. MAIN TOOLS ============
    print('\n--- 16. Main Tools ---')
    
    await test('reaper_get_audio_description', 'main',
               lambda: call('reaper_get_audio_description'))
    
    await test('reaper_list_audio_files', 'main',
               lambda: call('reaper_list_audio_files'))

    # ============ 17. ITEM OPERATIONS ============
    print('\n--- 17. Item Operations ---')
    
    await test('reaper_copy_item', 'item',
               lambda: call('reaper_copy_item', track_name='Melody', item_index=0, new_position=5.0))
    
    await test('reaper_split_item', 'item',
               lambda: call('reaper_split_item', track_name='Melody', item_index=1, split_position=2.0))
    
    await test('reaper_delete_item (copy)', 'item',
               lambda: call('reaper_delete_item', track_name='Melody', item_index=1))

    # ============ 18. DELETE MIDI NOTE ============
    print('\n--- 18. Delete MIDI Note ---')
    
    await test('reaper_delete_midi_note', 'midi',
               lambda: call('reaper_delete_midi_note', track_name='Melody', item_index=0, note_index=0))

    # ============ 19. MARKER CLEANUP ============
    print('\n--- 19. Cleanup Markers ---')
    
    markers_result = await call('reaper_get_all_markers')
    markers = markers_result.get('data', {}).get('markers', [])
    for i in range(len(markers) - 1, -1, -1):
        await call('reaper_delete_marker', index=i)
    
    await test('reaper_get_all_markers (after cleanup)', 'marker',
               lambda: call('reaper_get_all_markers'))

    # ============ 20. DELETE TEST TRACKS ============
    print('\n--- 20. Cleanup Tracks ---')
    
    cleanup_names = ['Melody', 'Bass', 'Drums', 'Strings']
    for name in cleanup_names:
        r = await call('reaper_delete_track', track_name=name)
        print(f'  Delete {name}: {r.get("success")}')
    
    # Get remaining track names
    remaining = await call('reaper_get_all_track_names')
    names = remaining.get('data', {}).get('track_names', [])
    print(f'  Remaining tracks: {names}')

    # ============ FINAL REPORT ============
    print('\n' + '=' * 70)
    total = passed + failed
    print(f'RESULTS: {passed}/{total} PASSED ({100*passed/total:.1f}%)')
    if errors:
        print(f'\nFAILURES ({len(errors)}):')
        for name, detail in errors:
            print(f'  - {name}')
            if isinstance(detail, dict):
                print(f'    error: {detail.get("error", "?")}')
                print(f'    detail: {detail.get("detail", "?")}')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(run_all_tests())
