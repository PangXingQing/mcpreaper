"""Clear all tracks from REAPER project using direct reascript API (bypasses reapy cache)."""
import os, sys
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and clear reapy cache
import reapy
# Force reconnect with correct params
reapy.config.WEB_INTERFACE_PORT = 2307
reapy.reconnect()

project = reapy.Project()
print(f'Project: {project.name}')

# Get tracks via direct API to avoid cache
from reapy import reascript_api as reaper
num_tracks = reaper.CountTracks(0)
print(f'Initial tracks: {num_tracks}')

# Delete from end to avoid index shifting issues
for i in range(num_tracks - 1, -1, -1):
    track = reaper.GetTrack(0, i)
    reaper.DeleteTrack(track)
    print(f'Deleted track index {i}')

num_tracks_after = reaper.CountTracks(0)
print(f'Remaining tracks: {num_tracks_after}')

# Also clear all markers
_, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
total = num_markers + num_regions
print(f'Markers/regions before: {num_markers} markers + {num_regions} regions')
for i in range(total - 1, -1, -1):
    reaper.DeleteProjectMarker(project, i, False)
print('All markers cleared.')

reaper.UpdateArrange()
print('DONE - Project is clean.')
