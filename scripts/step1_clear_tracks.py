import os, sys, json, asyncio

# Set connection params
os.environ["REAPER_WEB_HOST"] = "192.168.1.8"
os.environ["REAPER_WEB_PORT"] = "2307"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as mcp_main

async def main():
    # 1. Test connection
    r = await mcp_main.mcp.call_tool('reaper_get_project_info', {})
    text = r[0].text
    result = json.loads(text)
    print('CONNECTED:', result.get('success'))
    print('Project:', json.dumps(result.get('data', {}), indent=2, ensure_ascii=False))
    
    # 2. Get all tracks
    r = await mcp_main.mcp.call_tool('reaper_get_all_tracks', {})
    text = r[0].text
    result = json.loads(text)
    tracks = result.get('data', {}).get('tracks', [])
    print(f'\nTrack count: {len(tracks)}')
    for t in tracks:
        print(f'  - {t["name"]}')
    
    # 3. Delete all tracks
    for t in tracks:
        name = t['name']
        r = await mcp_main.mcp.call_tool('reaper_delete_track', {'track_name': name})
        text = r[0].text
        result = json.loads(text)
        print(f'Deleted "{name}": {result.get("success")}')
    
    # 4. Verify empty
    r = await mcp_main.mcp.call_tool('reaper_get_all_tracks', {})
    text = r[0].text
    result = json.loads(text)
    remaining = result.get('data', {}).get('tracks', [])
    print(f'\nRemaining tracks: {len(remaining)}')
    
    # 5. Also clear markers
    r = await mcp_main.mcp.call_tool('reaper_get_all_markers', {})
    text = r[0].text
    result = json.loads(text)
    markers = result.get('data', {}).get('markers', [])
    print(f'\nMarker count: {len(markers)}')
    for i in range(len(markers) - 1, -1, -1):
        r = await mcp_main.mcp.call_tool('reaper_delete_marker', {'index': i})
        text = r[0].text
        result = json.loads(text)
        print(f'Deleted marker {i}: {result.get("success")}')
    
    print('\n=== CLEANUP DONE ===')

asyncio.run(main())
