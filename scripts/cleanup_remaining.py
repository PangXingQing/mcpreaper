import os, sys, json, asyncio
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main as m

async def main():
    r = await m.mcp.call_tool('reaper_get_all_track_names', {})
    names = json.loads(r[0].text).get('data', {}).get('track_names', [])
    print(f'Remaining tracks: {names}')
    for n in names:
        r2 = await m.mcp.call_tool('reaper_delete_track', {'track_name': n})
        ok = json.loads(r2[0].text).get('success')
        print(f'Delete "{n}": {ok}')
    r3 = await m.mcp.call_tool('reaper_get_all_track_names', {})
    final = json.loads(r3[0].text).get('data', {}).get('track_names', [])
    print(f'After cleanup: {final}')

asyncio.run(main())
