# MCP Reaper (mcpreaper)

**Version 2.0**

一个基于 Model Context Protocol (MCP) 的 Reaper 音频编辑器控制接口，允许大语言模型 (LLM) 通过工具调用完整操作 Reaper 的所有功能。

---

## 目录

- [功能特性](#功能特性)
- [安装要求](#安装要求)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [工具分类与详细说明](#工具分类与详细说明)
- [错误处理机制](#错误处理机制)
- [使用示例](#使用示例)
- [项目结构](#项目结构)
- [测试脚本](#测试脚本)
- [LLM客户端配置教程](#llm客户端配置教程)
- [故障排除](#故障排除)
- [许可证](#许可证)

---

## 功能特性

### 核心功能
- **音轨管理**: 创建、删除、重命名、选择音轨，设置音量、声相、静音、独奏、录音准备状态
- **媒体项目**: 导入音频、移动、调整大小、分割、删除项目项，设置项目项音量和声相
- **播放控制**: 播放、停止、暂停、录音、循环播放、设置播放位置
- **FX插件**: 添加、移除、启用/禁用FX插件，设置插件参数

### 高级功能
- **标记管理**: 创建、删除、重命名标记和区域
- **MIDI编辑**: 创建MIDI项目项，插入、修改、删除MIDI音符，处理CC事件和文本事件
- **项目管理**: 保存项目、设置BPM/速度、撤销/重做、音频归一化
- **自动化包络**: 添加、删除、获取包络控制点，设置曲线形状
- **轨道发送**: 创建、删除、设置发送音量和声相，查看发送和接收信息
- **渲染导出**: 渲染项目、设置渲染参数、渲染选定音轨、批量渲染分轨
- **音频处理**: 录音、归一化、淡入淡出、音高调整、拉伸、移除静音
- **EQ/DSP处理**: ReaEQ参数控制、压缩器设置、FIR滤波器、EQ预设
- **影视声音制作**: 视频导入、时间码同步、ADR/拟音/音效音轨组创建、批量渲染
- **波形生成**: 正弦波、方波、三角波、锯齿波、白/粉/棕噪音、和弦生成

---

## 安装要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.11+ | 推荐使用最新稳定版本 |
| REAPER | 6.0+ | 音频编辑器，必须已安装 |
| reapy | latest | Python库，用于控制Reaper |
| mcp | latest | Model Context Protocol SDK |

---

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/PangXingQing/mcpreaper.git
cd mcpreaper
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

### 3. 激活虚拟环境

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. 安装依赖

```bash
pip install mcp[cli] python-reapy numpy scipy matplotlib
```

### 5. 配置 Reaper

确保 Reaper 已启用 ReaScript 远程控制：

1. 打开 Reaper
2. 进入 `Options` → `Preferences` → `Control/OSC/web`
3. 选择 `ReaScript` 选项卡
4. 勾选 `Allow external script control`
5. 确保 `Script execution` 设置为 `Allow all`

### 6. 验证安装

```bash
python main.py --help
```

---

## 使用方法

### 启动 MCP 服务器

```bash
python main.py
```

服务器将通过 stdio 协议启动，等待 LLM 客户端连接。

### 在 LLM 中使用

MCP 服务器提供以下工具供 LLM 调用。所有工具返回统一格式的响应：

**成功响应:**
```json
{
  "success": true,
  "message": "操作成功描述",
  "data": { ... }
}
```

**错误响应:**
```json
{
  "success": false,
  "error_type": "错误类型",
  "error": "错误消息",
  "detail": "详细信息",
  "suggestion": "解决建议"
}
```

---

## 工具分类与详细说明

### 音轨操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_add_track` | `track_name: str` | 创建音轨 |
| `reaper_delete_track` | `track_name: str` | 删除音轨 |
| `reaper_rename_track` | `track_name: str, new_name: str` | 重命名音轨 |
| `reaper_select_track` | `track_name: str` | 选择音轨 |
| `reaper_get_all_tracks` | 无 | 获取所有音轨信息 |
| `reaper_get_all_track_names` | 无 | 获取所有音轨名称 |
| `reaper_get_track_info` | `track_name: str` | 获取指定音轨信息 |
| `reaper_set_track_volume` | `track_name: str, volume: float` | 设置音轨音量（线性值 0-1） |
| `reaper_set_track_volume_db` | `track_name: str, volume_db: float` | 设置音轨音量（分贝值） |
| `reaper_set_track_pan` | `track_name: str, pan: float` | 设置音轨声相（-1到1） |
| `reaper_set_track_mute` | `track_name: str, mute: bool` | 设置音轨静音 |
| `reaper_set_track_solo` | `track_name: str, solo: bool` | 设置音轨独奏 |
| `reaper_set_track_rec_arm` | `track_name: str, rec_arm: bool` | 设置录音准备 |

### 媒体项目操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_insert_audio_to_track` | `track_name: str, file_path: str, position: float` | 导入音频到音轨 |
| `reaper_get_track_items` | `track_name: str` | 获取音轨的所有项目项 |
| `reaper_move_item` | `track_name: str, item_index: int, new_position: float` | 移动项目项 |
| `reaper_resize_item` | `track_name: str, item_index: int, new_length: float` | 调整项目项长度 |
| `reaper_delete_item` | `track_name: str, item_index: int` | 删除项目项 |
| `reaper_split_item` | `track_name: str, item_index: int, split_position: float` | 分割项目项 |
| `reaper_set_item_volume` | `track_name: str, item_index: int, volume: float` | 设置项目项音量 |
| `reaper_set_item_pan` | `track_name: str, item_index: int, pan: float` | 设置项目项声相 |

### 播放控制

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_play` | 无 | 开始播放 |
| `reaper_stop` | 无 | 停止播放 |
| `reaper_pause` | 无 | 暂停播放 |
| `reaper_toggle_play` | 无 | 切换播放/暂停 |
| `reaper_record` | 无 | 开始录音 |
| `reaper_go_to_start` | 无 | 移动到项目开头 |
| `reaper_go_to_end` | 无 | 移动到项目末尾 |
| `reaper_set_play_position` | `time: float` | 设置播放位置（秒） |
| `reaper_get_play_position` | 无 | 获取播放位置和状态 |
| `reaper_set_loop_range` | `start_time: float, end_time: float` | 设置循环范围 |
| `reaper_toggle_loop` | 无 | 切换循环模式 |

### FX插件操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_add_fx_to_track` | `track_name: str, fx_name: str` | 添加FX插件 |
| `reaper_remove_fx_from_track` | `track_name: str, fx_index: int` | 移除FX插件 |
| `reaper_get_track_fx_list` | `track_name: str` | 获取FX插件列表 |
| `reaper_toggle_fx` | `track_name: str, fx_index: int` | 切换FX启用状态 |
| `reaper_set_fx_param` | `track_name: str, fx_index: int, param_index: int, value: float` | 设置FX参数 |
| `reaper_get_fx_params` | `track_name: str, fx_index: int` | 获取FX参数信息 |
| `reaper_bypass_all_fx` | `track_name: str, bypass: bool` | 旁路所有FX |

### 标记操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_add_marker` | `name: str, position: float` | 添加标记 |
| `reaper_delete_marker` | `name: str` | 删除标记 |
| `reaper_rename_marker` | `old_name: str, new_name: str` | 重命名标记 |
| `reaper_get_all_markers` | 无 | 获取所有标记 |
| `reaper_go_to_marker` | `name: str` | 跳转到标记位置 |

### MIDI操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_insert_midi_item` | `track_name: str, position: float, length: float` | 插入MIDI项目项 |
| `reaper_add_midi_note` | `track_name: str, item_index: int, pitch: int, start_time: float, end_time: float, velocity: int` | 添加MIDI音符 |
| `reaper_set_midi_note_velocity` | `track_name: str, item_index: int, note_index: int, velocity: int` | 设置MIDI音符力度 |
| `reaper_delete_midi_note` | `track_name: str, item_index: int, note_index: int` | 删除MIDI音符 |
| `reaper_get_midi_notes` | `track_name: str, item_index: int` | 获取MIDI音符列表 |

### 项目操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_save_project` | 无 | 保存项目 |
| `reaper_save_project_as` | `file_path: str` | 另存项目 |
| `reaper_set_project_bpm` | `bpm: float` | 设置项目BPM |
| `reaper_get_project_bpm` | 无 | 获取项目BPM |
| `reaper_undo` | 无 | 撤销操作 |
| `reaper_redo` | 无 | 重做操作 |
| `reaper_calculate_normalization` | `track_name: str` | 计算音频归一化 |
| `reaper_normalize_audio` | `track_name: str, target_db: float` | 归一化音频 |

### 自动化包络操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_get_track_envelopes` | `track_name: str` | 获取音轨的所有包络信息 |
| `reaper_add_envelope_point` | `track_name: str, envelope_index: int, time: float, value: float, shape: int` | 在包络上添加控制点 |
| `reaper_delete_envelope_point` | `track_name: str, envelope_index: int, point_index: int` | 删除包络控制点 |
| `reaper_get_envelope_points` | `track_name: str, envelope_index: int` | 获取包络的所有控制点 |
| `reaper_get_envelope_value_at_time` | `track_name: str, envelope_index: int, time: float` | 获取包络在指定时间点的值 |
| `reaper_clear_envelope_points` | `track_name: str, envelope_index: int` | 清空包络的所有控制点 |

### 轨道发送操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_create_track_send` | `source_track_name: str, destination_track_name: str` | 在两个音轨之间创建发送 |
| `reaper_delete_track_send` | `track_name: str, send_index: int` | 删除音轨的指定发送 |
| `reaper_get_track_sends` | `track_name: str` | 获取音轨的所有发送信息 |
| `reaper_set_send_volume` | `track_name: str, send_index: int, volume: float` | 设置发送音量 |
| `reaper_set_send_pan` | `track_name: str, send_index: int, pan: float` | 设置发送声相 |
| `reaper_get_track_receives` | `track_name: str` | 获取音轨的所有接收信息 |

### 渲染导出操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_render_project` | `output_path: str, render_mode: int` | 渲染项目 |
| `reaper_render_selected_tracks` | `output_path: str, track_names: list` | 渲染选定的音轨 |
| `reaper_get_render_settings` | 无 | 获取当前渲染设置 |
| `reaper_set_render_settings` | `sample_rate: int, bit_depth: int` | 设置渲染参数 |
| `reaper_render_item_as_new_take` | `track_name: str, item_index: int` | 将媒体项渲染为新的take |
| `reaper_create_render_marker_region` | `start_time: float, end_time: float, name: str` | 创建渲染区域标记 |

### MIDI扩展操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_insert_midi_cc` | `track_name: str, item_index: int, cc_number: int, position_ppq: int, value: int, channel: int` | 插入CC事件 |
| `reaper_get_midi_cc_events` | `track_name: str, item_index: int` | 获取所有CC事件 |
| `reaper_insert_midi_text_event` | `track_name: str, item_index: int, position_ppq: int, text: str, event_type: str` | 插入文本事件 |
| `reaper_get_midi_text_events` | `track_name: str, item_index: int` | 获取所有文本事件 |
| `reaper_quantize_midi_notes` | `track_name: str, item_index: int, grid_div: int, strength: float` | 量化MIDI音符 |
| `reaper_transpose_midi_notes` | `track_name: str, item_index: int, semitones: int` | 移调MIDI音符 |
| `reaper_get_midi_item_info` | `track_name: str, item_index: int` | 获取MIDI项目项的详细信息 |

### 音频处理操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_record_on_track` | `track_name: str` | 在指定音轨上开始录音 |
| `reaper_stop_recording` | 无 | 停止录音 |
| `reaper_normalize_audio_item` | `track_name: str, item_index: int, target_db: float` | 归一化音频项目项 |
| `reaper_fade_audio_item` | `track_name: str, item_index: int, fade_in_length: float, fade_out_length: float` | 设置淡入淡出 |
| `reaper_stretch_audio_item` | `track_name: str, item_index: int, new_length: float` | 拉伸音频项目项 |
| `reaper_change_audio_pitch` | `track_name: str, item_index: int, semitones: int` | 改变音频项目项的音高 |
| `reaper_get_audio_item_info` | `track_name: str, item_index: int` | 获取音频项目项的详细信息 |
| `reaper_remove_audio_silence` | `track_name: str, item_index: int, threshold_db: float` | 移除静音部分 |
| `reaper_insert_audio_crossfade` | `track_name: str, item_index1: int, item_index2: int` | 插入交叉淡化 |
| `reaper_apply_audio_processing` | `track_name: str, item_index: int, action_name: str` | 应用处理动作 |

### EQ/DSP处理操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_add_reaeq` | `track_name: str` | 为音轨添加ReaEQ插件 |
| `reaper_set_reaeq_band` | `track_name: str, band_index: int, freq_hz: float, gain_db: float, q_factor: float, filter_type: str` | 设置ReaEQ频段参数 |
| `reaper_get_reaeq_band` | `track_name: str, band_index: int` | 获取ReaEQ频段参数 |
| `reaper_reset_reaeq` | `track_name: str` | 重置ReaEQ所有频段参数 |
| `reaper_apply_eq_preset` | `track_name: str, preset_name: str` | 应用EQ预设 |
| `reaper_add_reacomp` | `track_name: str` | 为音轨添加ReaComp压缩器 |
| `reaper_set_reacomp_params` | `track_name: str, threshold_db: float, ratio: float, attack_ms: float, release_ms: float, knee_db: float` | 设置ReaComp参数 |
| `reaper_add_reafir` | `track_name: str` | 为音轨添加ReaFIR均衡器 |

### 影视声音制作操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_import_video` | `file_path: str` | 导入视频文件到项目 |
| `reaper_set_timecode_format` | `format_type: str` | 设置时间码格式 |
| `reaper_set_frame_rate` | `frame_rate: float` | 设置项目帧率 |
| `reaper_set_start_timecode` | `hours: int, minutes: int, seconds: int, frames: int` | 设置项目开始时间码 |
| `reaper_set_sync_reference` | `mode: str` | 设置同步参考模式 |
| `reaper_batch_render_tracks` | `output_dir: str, track_names: list, format: str` | 批量渲染多个音轨 |
| `reaper_render_stems` | `output_dir: str, stem_type: str` | 渲染分轨（Stems） |
| `reaper_create_adr_track` | `prefix: str, count: int` | 创建ADR音轨组 |
| `reaper_create_foley_tracks` | 无 | 创建标准拟音音轨组 |
| `reaper_create_sound_effects_tracks` | 无 | 创建标准音效音轨组 |
| `reaper_get_video_info` | 无 | 获取视频信息 |
| `reaper_insert_cue_marker` | `time: float, name: str, color: str` | 插入提示标记 |
| `reaper_export_session_info` | `file_path: str` | 导出会话信息 |

### 波形生成操作

| 工具名称 | 参数 | 说明 |
|---------|------|------|
| `reaper_generate_sine_wave` | `frequency: float, duration: float, sample_rate: int, amplitude: float` | 生成正弦波 |
| `reaper_generate_square_wave` | `frequency: float, duration: float, sample_rate: int, amplitude: float` | 生成方波 |
| `reaper_generate_triangle_wave` | `frequency: float, duration: float, sample_rate: int, amplitude: float` | 生成三角波 |
| `reaper_generate_sawtooth_wave` | `frequency: float, duration: float, sample_rate: int, amplitude: float` | 生成锯齿波 |
| `reaper_generate_noise` | `duration: float, sample_rate: int, amplitude: float, noise_type: str` | 生成噪音（白/粉/棕） |
| `reaper_generate_chord` | `chord_notes: list, duration: float, sample_rate: int, amplitude: float` | 生成和弦 |

---

## 错误处理机制

### 错误类型说明

当操作失败时，工具会返回详细的错误信息，帮助用户诊断问题：

| 错误类型 | 说明 | 典型场景 |
|---------|------|---------|
| `ReaperConnectionError` | 无法连接到Reaper | Reaper未启动、未启用外部脚本控制 |
| `TrackNotFoundError` | 未找到指定音轨 | 音轨名称拼写错误、音轨不存在 |
| `ItemNotFoundError` | 未找到项目项 | 项目项索引超出范围 |
| `FXNotFoundError` | 未找到FX插件 | 插件未安装、索引错误 |
| `InvalidParameterError` | 参数无效 | 参数值超出范围、类型错误 |
| `ReaperFileNotFoundError` | 文件不存在 | 文件路径错误、文件被删除 |
| `OperationFailedError` | 操作失败 | 执行过程中发生未知错误 |

### 错误响应示例

```json
{
  "success": false,
  "error_type": "TrackNotFoundError",
  "error": "未找到音轨「Vocals」",
  "detail": "当前项目中不存在名为「Vocals」的音轨",
  "suggestion": "可用音轨列表：['Track 1', 'Track 2', 'Drums']"
}
```

---

## 使用示例

### 示例1：创建音轨并导入音频

```python
# 创建音轨
reaper_add_track("Vocals")

# 设置音量
reaper_set_track_volume_db("Vocals", -3.0)

# 导入音频
reaper_insert_audio_to_track("Vocals", "C:/audio/vocal_recording.wav", 0.0)
```

### 示例2：应用EQ处理

```python
# 添加ReaEQ插件
reaper_add_reaeq("Vocals")

# 设置频段参数
reaper_set_reaeq_band("Vocals", 0, 100, -3.0, 1.0, "lowcut")  # 低频切除
reaper_set_reaeq_band("Vocals", 1, 2500, 3.0, 1.5, "peak")   # 中频提升
reaper_set_reaeq_band("Vocals", 2, 8000, 2.0, 1.0, "highshelf")  # 高频提升
```

### 示例3：生成波形并处理

```python
# 生成正弦波
reaper_generate_sine_wave(440.0, 2.0, 44100, 0.5)

# 添加压缩器
reaper_add_reacomp("Track 1")
reaper_set_reacomp_params("Track 1", -18.0, 4.0, 10.0, 100.0, 3.0)
```

---

## 项目结构

```
mcpreaper/
├── main.py                 # MCP服务器入口
├── test_dsp_workflow.py    # DSP工作流测试脚本
├── tools/
│   ├── __init__.py
│   ├── track_tools.py      # 音轨操作工具
│   ├── item_tools.py       # 媒体项目操作工具
│   ├── playback_tools.py   # 播放控制工具
│   ├── fx_tools.py         # FX插件操作工具
│   ├── marker_tools.py     # 标记操作工具
│   ├── midi_tools.py       # MIDI基础操作工具
│   ├── project_tools.py    # 项目管理工具
│   ├── envelope_tools.py   # 自动化包络工具
│   ├── send_tools.py       # 轨道发送工具
│   ├── render_tools.py     # 渲染导出工具
│   ├── midi_ext_tools.py   # MIDI扩展操作工具
│   ├── audio_tools.py      # 音频处理工具
│   ├── eq_tools.py         # EQ/DSP处理工具
│   ├── film_tools.py       # 影视声音制作工具
│   └── generate_tools.py   # 波形生成工具
├── utils/
│   ├── __init__.py
│   ├── reaper_client.py    # Reaper客户端工具类
│   └── error_handler.py    # 统一错误处理模块
├── WAV/                    # 生成的WAV文件目录（自动创建）
├── plots/                  # 测试生成的图表目录（自动创建）
└── .gitignore
```

---

## 测试脚本

### DSP工作流测试

运行 `test_dsp_workflow.py` 可以在本地验证波形生成和EQ处理功能，无需启动Reaper：

```bash
python test_dsp_workflow.py
```

该脚本会：
1. 生成各种波形（正弦波、方波、三角波、锯齿波、噪音）
2. 应用多种DSP处理（低通/高通/带通滤波、Peak EQ、Shelf EQ）
3. 生成波形图和频谱图
4. 生成测试报告

---

## LLM客户端配置教程

以下是在各主流LLM客户端中配置本MCP服务的详细步骤，所有配置方法均来自官方文档。

### 前置条件

1. 确保已完成本项目的安装步骤
2. 确保Reaper已启动并启用外部脚本控制
3. 确保已激活虚拟环境

### 1. CherryStudio

官方文档：https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp

**方法一：图形化界面配置**

1. 打开 CherryStudio
2. 点击左下角 **「设置」**
3. 进入 **「MCP 服务器」** 选项卡
4. 点击右上角 **「添加」** → 选择 **「从 JSON 导入」**
5. 粘贴以下 JSON 配置：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

6. 将 `C:/path/to/mcpreaper/main.py` 替换为你的实际路径（使用正斜杠）
7. 点击 **「确定」**
8. 点击开关启用服务器

**方法二：使用虚拟环境**

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["-m", "venv", ".venv", "&&", "python", "main.py"],
      "env": {},
      "cwd": "C:/path/to/mcpreaper"
    }
  }
}
```

**使用方式**：在聊天界面底部点击 MCP 按钮，选中 `mcpreaper` 服务。

**验证配置**：

- **界面验证**：配置后服务器状态显示绿色 ✅，展开可看到加载的工具列表
- **命令行测试**（启动前先验证Python路径）：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在聊天中输入 `帮我获取Reaper项目中的所有音轨`

---

### 2. WorkBuddy

官方文档：https://cloud.tencent.cn/developer/article/2701462

**方法一：可视化界面配置**

1. 在 CodeBuddy IDE 侧边栏的对话面板右上角，点击 `CodeBuddy Settings` 齿轮图标
2. 在设置界面中，切换到 **MCP** 标签页
3. 点击右侧的 `Add MCP` 按钮
4. 粘贴以下 JSON 配置：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {},
      "description": "Reaper音频编辑器控制MCP服务"
    }
  }
}
```

5. 点击 `Try to Run` 按钮验证配置

**方法二：手动编辑配置文件**

配置文件路径：`~/.workbuddy/mcp.json`（Windows：`C:\Users\你的用户名\.workbuddy\mcp.json`）

```json
{
  "mcpServers": {
    "mcpreaper": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

**验证配置**：

- **界面验证**：点击 `Try to Run` 按钮，看到绿灯亮起表示配置成功
- **命令行测试**：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在聊天中输入 `帮我获取Reaper项目中的所有音轨`

---

### 3. TRAE IDE

官方文档：https://docs.trae.ai/ide/add-mcp-servers

**方法一：从MCP市场添加**

1. 在 IDE 模式界面中，点击右上角的 **设置** 图标
2. 在左侧导航栏中，选择 **MCP**
3. 点击 **添加** → **从市场添加**
4. 在市场中搜索并找到 mcpreaper（若已发布）

**方法二：手动配置**

1. 点击 **添加** → **手动添加**
2. 填入以下 JSON 配置：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

**方法三：项目级配置**

在项目根目录下创建 `.trae/mcp.json`：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["${workspaceFolder}/main.py"],
      "env": {}
    }
  }
}
```

**验证配置**：

- **界面验证**：MCP 列表中服务器状态显示绿色 ✅
- **命令行测试**：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在 AI 对话中输入 `帮我获取Reaper项目中的所有音轨`
- **项目级验证**：确保已在 **设置 > MCP** 中打开 **启用项目级 MCP** 开关

---

### 4. Claude Code

官方文档：https://code.claude.com/docs/en/mcp-quickstart

**方法一：CLI命令配置**

在终端中运行：

```bash
claude mcp add mcpreaper -- python C:/path/to/mcpreaper/main.py
```

**方法二：编辑配置文件**

配置文件路径：`~/.claude.json`（项目级）或 `~/.claude/config.json`（全局）

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

**方法三：HTTP服务器模式**

如果你的MCP服务通过HTTP暴露（需修改main.py支持HTTP）：

```bash
claude mcp add --transport http mcpreaper http://localhost:8000/mcp
```

**验证配置**：

- **CLI验证**：
  ```bash
  claude mcp list
  ```
- **命令行测试**（启动前先验证Python路径）：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在 Claude Code 聊天中输入 `帮我获取Reaper项目中的所有音轨`
- **配置文件验证**：检查配置是否正确写入
  ```bash
  # Windows
  type %USERPROFILE%\.claude.json
  # macOS/Linux
  cat ~/.claude.json
  ```

---

### 5. VS Code

官方文档：https://code.visualstudio.com/docs/copilot/customization/mcp-servers

**方法一：使用Continue扩展**

1. 安装 Continue 扩展：https://marketplace.visualstudio.com/items?itemName=Continue.continue
2. 编辑 Continue 配置文件 `~/.continue/config.yaml`：

```yaml
mcpServers:
  - name: mcpreaper
    command: python
    args:
      - C:/path/to/mcpreaper/main.py
```

**方法二：使用VS Code内置MCP配置**

1. 打开命令面板（Ctrl+Shift+P）
2. 运行 `MCP: Open User Configuration`
3. 在 `mcp.json` 文件中添加：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

**方法三：项目级配置**

在 `.vscode/mcp.json` 中添加配置：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["${workspaceFolder}/main.py"],
      "env": {}
    }
  }
}
```

**验证配置**：

- **Continue扩展验证**：打开 Continue 对话，输入 `/tools` 查看工具列表
- **VS Code内置验证**：打开命令面板（Ctrl+Shift+P），运行 `MCP: List Servers`
- **命令行测试**：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在 AI 对话中输入 `帮我获取Reaper项目中的所有音轨`

---

### 6. Chat Box

官方文档：https://docs.chatboxai.app/guides/mcp.md

**方法一：图形化界面配置**

1. 打开 Chat Box
2. 进入 **设置 - MCP** 页面
3. 点击 **「添加服务器」**
4. 手动配置：
   - 名称：`mcpreaper`
   - 命令：`python`
   - 参数：`C:/path/to/mcpreaper/main.py`

**方法二：一键安装链接**

生成一键安装链接：

1. 创建配置JSON：

```json
{
  "name": "mcpreaper",
  "command": "python",
  "args": ["C:/path/to/mcpreaper/main.py"],
  "env": {}
}
```

2. 使用 base64 编码配置
3. 生成链接：`chatbox://mcp/install?server=BASE64_ENCODED_CONFIG`

**验证配置**：

- **界面验证**：在 **设置 - MCP** 页面查看服务器状态，显示绿色表示正常
- **命令行测试**：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在聊天中输入 `帮我获取Reaper项目中的所有音轨`

---

### 7. Codex CLI

官方文档：https://codex.danielvaughan.com/2026/05/19/codex-cli-mcp-server-management-cli-commands-oauth-streamable-http-production-patterns/

**方法一：CLI命令配置**

```bash
codex mcp add mcpreaper -- python C:/path/to/mcpreaper/main.py
```

**方法二：编辑config.toml**

配置文件路径：`~/.codex/config.toml`

```toml
[mcp_servers.mcpreaper]
command = "python"
args = ["C:/path/to/mcpreaper/main.py"]
enabled = true

[mcp_servers.mcpreaper.env]
# 可选：添加环境变量
```

**方法三：项目级配置**

在项目根目录创建 `.codex/config.toml`：

```toml
[mcp_servers.mcpreaper]
command = "python"
args = ["${workspaceFolder}/main.py"]
enabled = true
cwd = "${workspaceFolder}"
```

**验证配置**：

- **CLI验证**：
  ```bash
  codex mcp list
  ```
- **命令行测试**（启动前先验证Python路径）：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：在 Codex 会话中输入 `帮我获取Reaper项目中的所有音轨`
- **配置文件验证**：检查配置是否正确写入
  ```bash
  # Windows
  type %USERPROFILE%\.codex\config.toml
  # macOS/Linux
  cat ~/.codex/config.toml
  ```

---

### 8. Cursor

官方文档：https://cursor.com/docs/mcp

**方法一：全局配置**

配置文件路径：`~/.cursor/mcp.json`（Windows：`%APPDATA%/Cursor/mcp.json`）

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

**方法二：项目级配置**

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "python",
      "args": ["${workspaceFolder}/main.py"],
      "env": {}
    }
  }
}
```

**方法三：图形化配置**

1. 打开 Cursor Settings
2. 搜索 **MCP**
3. 在 **MCP Tools** 部分点击 **New MCP Server**
4. 粘贴配置并保存

**环境变量支持**：

Cursor 支持配置插值：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "${env:PYTHON_PATH}",
      "args": ["${workspaceFolder}/main.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

**验证配置**：

- **界面验证**：在 **Cursor Settings > Tools & Integrations > MCP Tools** 查看服务器状态，绿色表示正常
- **命令行测试**：
  ```bash
  python C:/path/to/mcpreaper/main.py --help
  ```
- **对话测试**：打开 Cursor 聊天（Ctrl+L），输入 `帮我获取Reaper项目中的所有音轨`
- **配置文件验证**：检查配置文件是否正确写入
  ```bash
  # Windows - 查看全局配置
  type %APPDATA%\Cursor\mcp.json
  # Windows - 查看项目配置
  type .cursor\mcp.json
  
  # macOS/Linux - 查看全局配置
  cat ~/.cursor/mcp.json
  # macOS/Linux - 查看项目配置
  cat .cursor/mcp.json
  ```

---

### 通用配置要点

#### Windows路径注意事项

在JSON配置中，Windows路径有两种写法：
- 使用正斜杠：`C:/path/to/mcpreaper/main.py`
- 使用双反斜杠：`C:\\path\\to\\mcpreaper\\main.py`

#### 虚拟环境激活

如果使用虚拟环境，需要确保使用正确的Python路径：

```json
{
  "mcpServers": {
    "mcpreaper": {
      "command": "C:/path/to/mcpreaper/.venv/Scripts/python.exe",
      "args": ["C:/path/to/mcpreaper/main.py"],
      "env": {}
    }
  }
}
```

#### 配置验证

添加配置后，建议验证服务器是否正常运行：
1. 检查服务器状态指示灯（绿色表示正常）
2. 在对话中尝试调用工具：`帮我获取Reaper项目中的所有音轨`
3. 查看工具列表是否包含所有 `reaper_*` 工具

---

## 故障排除

### 常见问题

**Q: 连接Reaper失败**

A: 请确保：
1. Reaper已启动并运行
2. 已启用外部脚本控制（Options → Preferences → Control/OSC/web → ReaScript）
3. Script execution 设置为 Allow all

**Q: 提示 reapy 模块未找到**

A: 确保已安装 reapy 库：
```bash
pip install python-reapy
```

**Q: 参数无效错误**

A: 检查参数值是否在有效范围内，错误响应中会包含有效值范围提示。

**Q: 音轨未找到**

A: 使用 `reaper_get_all_track_names` 获取当前项目的所有音轨名称，确认音轨名称拼写正确。

**Q: 渲染失败**

A: 检查输出路径是否正确，确保输出目录存在且有写入权限。

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！