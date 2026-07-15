"""清空REAPER工程 - 使用reascript_api"""
import os, sys
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()
print(f'当前工程: {proj.name}')

# 获取轨道
tracks = list(proj.tracks)
print(f'原有轨道数: {len(tracks)}')
for t in tracks:
    print(f'  删除: {t.name}')
    reaper.DeleteTrack(t)

# 验证
remaining = list(proj.tracks)
print(f'删除后轨道数: {len(remaining)}')

print('工程已清空！')
