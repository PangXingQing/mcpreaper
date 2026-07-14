# MCP Reaper (mcpreaper)

一个基于 Model Context Protocol (MCP) 的 Reaper 音频编辑器控制接口，允许大语言模型 (LLM) 通过工具调用完整操作 Reaper 的所有功能。

## 功能特性

- **音轨管理**: 创建、删除、重命名、选择音轨，设置音量、声相、静音、独奏、录音准备状态
- **媒体项目**: 导入音频、移动、调整大小、分割、删除项目项，设置项目项音量和声相
- **播放控制**: 播放、停止、暂停、录音、循环播放、设置播放位置
- **FX插件**: 添加、移除、启用/禁用FX插件，设置插件参数
- **标记管理**: 创建、删除、重命名标记和区域
- **MIDI编辑**: 创建MIDI项目项，插入、修改、删除MIDI音符
- **项目管理**: 保存项目、设置BPM/速度、撤销/重做、音频归一化

## 安装要求

- Python 3.11+
- REAPER 音频编辑器
- reapy Python库
- mcp Python库

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
pip install mcp[cli] python-reapy
```

### 5. 配置 Reaper

确保 Reaper 已启用 ReaScript 远程控制：

1. 打开 Reaper
2. 进入 `Options` → `Preferences` → `Control/OSC/web`
3. 选择 `ReaScript` 选项卡
4. 勾选 `Allow external script control`
5. 确保 `Script execution` 设置为 `Allow all`

## 使用方法

### 启动 MCP 服务器

```bash
python main.py
```

服务器将通过 stdio 协议启动，等待 LLM 客户端连接。

### 在 LLM 中使用

MCP 服务器提供以下工具供 LLM 调用：

#### 音轨操作
- `reaper_add_track(track_name)` - 创建音轨
- `reaper_delete_track(track_name)` - 删除音轨
- `reaper_rename_track(track_name, new_name)` - 重命名音轨
- `reaper_select_track(track_name)` - 选择音轨
- `reaper_get_all_tracks()` - 获取所有音轨信息
- `reaper_get_all_track_names()` - 获取所有音轨名称
- `reaper_get_track_info(track_name)` - 获取指定音轨信息
- `reaper_set_track_volume(track_name, volume)` - 设置音轨音量（线性值）
- `reaper_set_track_volume_db(track_name, volume_db)` - 设置音轨音量（分贝值）
- `reaper_set_track_pan(track_name, pan)` - 设置音轨声相
- `reaper_set_track_mute(track_name, mute)` - 设置音轨静音
- `reaper_set_track_solo(track_name, solo)` - 设置音轨独奏
- `reaper_set_track_rec_arm(track_name, rec_arm)` - 设置录音准备

#### 媒体项目操作
- `reaper_insert_audio_to_track(track_name, file_path, position)` - 导入音频到音轨
- `reaper_get_track_items(track_name)` - 获取音轨的所有项目项
- `reaper_move_item(track_name, item_index, new_position)` - 移动项目项
- `reaper_resize_item(track_name, item_index, new_length)` - 调整项目项长度
- `reaper_delete_item(track_name, item_index)` - 删除项目项
- `reaper_split_item(track_name, item_index, split_position)` - 分割项目项
- `reaper_set_item_volume(track_name, item_index, volume)` - 设置项目项音量
- `reaper_set_item_pan(track_name, item_index, pan)` - 设置项目项声相

#### 播放控制
- `reaper_play()` - 开始播放
- `reaper_stop()` - 停止播放
- `reaper_pause()` - 暂停播放
- `reaper_toggle_play()` - 切换播放/暂停
- `reaper_record()` - 开始录音
- `reaper_go_to_start()` - 移动到项目开头
- `reaper_go_to_end()` - 移动到项目末尾
- `reaper_set_play_position(time)` - 设置播放位置
- `reaper_get_play_position()` - 获取播放位置和状态
- `reaper_set_loop_range(start_time, end_time)` - 设置循环范围
- `reaper_toggle_loop()` - 切换循环模式

#### FX插件操作
- `reaper_add_fx_to_track(track_name, fx_name)` - 添加FX插件
- `reaper_remove_fx_from_track(track_name, fx_index)` - 移除FX插件
- `reaper_get_track_fx_list(track_name)` - 获取FX插件列表
- `reaper_toggle_fx(track_name, fx_index)` - 切换FX启用状态
- `reaper_set_fx_param(track_name, fx_index, param_index, value)` - 设置FX参数
- `reaper_get_fx_params(track_name, fx_index)` - 获取FX参数信息
- `reaper_bypass_all_fx(track_name, bypass)` - 旁路所有FX

#### 标记操作
- `reaper_add_marker(name, position)` - 添加标记
- `reaper_delete_marker(name)` - 删除标记
- `reaper_rename_marker(old_name, new_name)` - 重命名标记
- `reaper_get_all_markers()` - 获取所有标记
- `reaper_go_to_marker(name)` - 跳转到标记位置

#### MIDI操作
- `reaper_insert_midi_item(track_name, position, length)` - 插入MIDI项目项
- `reaper_add_midi_note(track_name, item_index, pitch, start_time, end_time, velocity)` - 添加MIDI音符
- `reaper_set_midi_note_velocity(track_name, item_index, note_index, velocity)` - 设置MIDI音符力度
- `reaper_delete_midi_note(track_name, item_index, note_index)` - 删除MIDI音符
- `reaper_get_midi_notes(track_name, item_index)` - 获取MIDI音符列表

#### 项目操作
- `reaper_save_project()` - 保存项目
- `reaper_save_project_as(file_path)` - 另存项目
- `reaper_set_project_bpm(bpm)` - 设置项目BPM
- `reaper_get_project_bpm()` - 获取项目BPM
- `reaper_undo()` - 撤销操作
- `reaper_redo()` - 重做操作
- `reaper_calculate_normalization(track_name)` - 计算音频归一化
- `reaper_normalize_audio(track_name, target_db)` - 归一化音频

#### 音频文件管理
- `reaper_get_audio_description()` - 获取音频描述信息
- `reaper_list_audio_files()` - 列出可用音频文件

## 项目结构

```
mcpreaper/
├── main.py                 # MCP服务器入口
├── tools/
│   ├── __init__.py
│   ├── track_tools.py      # 音轨操作工具
│   ├── item_tools.py       # 媒体项目操作工具
│   ├── playback_tools.py   # 播放控制工具
│   ├── fx_tools.py         # FX插件操作工具
│   ├── marker_tools.py     # 标记操作工具
│   ├── midi_tools.py       # MIDI操作工具
│   └── project_tools.py    # 项目管理工具
├── utils/
│   ├── __init__.py
│   └── reaper_client.py    # Reaper客户端工具类
└── .gitignore
```

## 注意事项

1. 使用前请确保 Reaper 已启动并运行
2. 所有操作都会影响当前打开的 Reaper 项目
3. 建议在使用前保存项目，以防意外操作
4. ReaScript API 需要 Reaper 运行时环境支持

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！