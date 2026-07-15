"""
为所有 MIDI 轨道设置 MIDI 硬件输出到系统默认音源。
"""
import os
os.environ['REAPER_WEB_HOST'] = '192.168.1.8'
os.environ['REAPER_WEB_PORT'] = '2307'

import reapy
from reapy import reascript_api as reaper

reapy.reconnect()
proj = reapy.Project()

# 需要配置 MIDI 输出的轨道名
midi_track_names = [
    "编钟 Bells",
    "弦乐 Strings",
    "笛子 Flute",
    "古筝 Koto",
    "大鼓 Drums",
    "大提琴 Cello",
    "合唱 Choir",
]

print("=== 尝试通过 reapy API 设置 MIDI 硬件输出 ===\n")

# 先查看当前可用的 MIDI 输出设备
print("检查 REAPER MIDI 输出设备...")
try:
    # GetNumMIDIOutputs 返回可用的 MIDI 输出设备数
    num_outputs = reaper.GetNumMIDIOutputs()
    print(f"可用 MIDI 输出设备数: {num_outputs}")
    for i in range(num_outputs):
        try:
            name = reaper.GetMIDIOutputName(i, "", 256)
            print(f"  [{i}] {name}")
        except Exception as e:
            print(f"  [{i}] 获取名称失败: {e}")
except Exception as e:
    print(f"获取 MIDI 输出设备列表失败: {e}")

print()

# 遍历每条轨道，尝试创建 MIDI Hardware Output
tracks = list(proj.tracks)
for track in tracks:
    if track.name not in midi_track_names:
        continue
    
    print(f"处理轨道: {track.name}")
    
    # 方法1: 用 CreateTrackSend 创建 hardware output (dest = None 表示硬件输出)
    try:
        # CreateTrackSend(track, destination) - destination=None creates hardware output
        send_count = reaper.GetTrackNumSends(track, 1)  # 1 = hardware output category
        print(f"  现有硬件输出数: {send_count}")
        
        if send_count == 0:
            result = reaper.CreateTrackSend(track, None)
            print(f"  CreateTrackSend(result): {result}")
            send_count_new = reaper.GetTrackNumSends(track, 1)
            print(f"  创建后硬件输出数: {send_count_new}")
        
        # 显示当前发送详情
        # 0 = send, 1 = hardware output
        for i in range(reaper.GetTrackNumSends(track, 0)):
            try:
                dest_name = reaper.GetTrackSendInfo_Value(track, 0, i, "P_DESTTRACK")
                print(f"  Send[{i}]: dest_track={dest_name}")
            except:
                pass
        
        for i in range(reaper.GetTrackNumSends(track, 1)):
            try:
                dest_name = reaper.GetTrackSendInfo_Value(track, 1, i, "P_DESTTRACK")
                print(f"  HWOut[{i}]: dest={dest_name}")
            except:
                pass
        
    except Exception as e:
        print(f"  错误: {e}")
    
    print()

print("\n=== 总结 ===")
print("如果自动配置失败，请在 REAPER 界面中手动操作：")
print("1. 点击轨道面板上的 ROUTE 按钮（或右键轨道 → 路由设置）")
print("2. 在 'MIDI Hardware Output' 区域，选择系统默认 MIDI 音源")
print("   - Windows: 选择 Microsoft GS Wavetable Synth")
print("3. 确保 MIDI 输出通道与你的音符通道匹配")
print("   - 编钟 Bells:      通道 1 (GM 14 Tubular Bells)")
print("   - 弦乐 Strings:    通道 2 (GM 48 String Ensemble 1)")
print("   - 笛子 Flute:      通道 3 (GM 73 Flute)")
print("   - 古筝 Koto:       通道 4 (GM 107 Koto)")
print("   - 大鼓 Drums:      通道 10 (GM Drum Kit)")
print("   - 大提琴 Cello:    通道 5 (GM 42 Cello)")
print("   - 合唱 Choir:      通道 6 (GM 52 Choir Aahs)")
