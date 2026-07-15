"""Clean project and re-compose the film score."""
import os, sys
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import reapy
reapy.config.WEB_INTERFACE_PORT = 2307
reapy.reconnect()

from reapy import reascript_api as reaper

project = reapy.Project()
print(f'Cleaning project: {project.name}')

# Delete all tracks
num = reaper.CountTracks(0)
print(f'Tracks: {num}')
for i in range(num - 1, -1, -1):
    reaper.DeleteTrack(reaper.GetTrack(0, i))
print(f'Tracks after: {reaper.CountTracks(0)}')

# Delete all markers
_, _, nm, nr = reaper.CountProjectMarkers(project, 0, 0)
total = nm + nr
print(f'Markers: {total}')
for i in range(total - 1, -1, -1):
    reaper.DeleteProjectMarker(project, i, False)
_, _, nm2, nr2 = reaper.CountProjectMarkers(project, 0, 0)
print(f'Markers after: {nm2 + nr2}')

reaper.UpdateArrange()
print('Clean! Now running composition...')
