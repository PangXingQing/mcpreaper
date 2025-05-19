# 项目运行与说明
## 配置Reapy库
ReaScript是Reaper官方脚本，Reapy是ReaScript的Python扩展

Reapy需要安装为全局的Python库，库名称为python-reapy

**配置Reapy库**
1. 安装全局版本的Reapy库
2. 在Reaper的Preference中，找到ReaScript选项，配置Python信息，并启用Python：“Enable Pthon for use with ReaScript"
![在Reaper中启用Python支持](/article/reaper_python_setting.png)  
3. 在Reaper的Preference中，找到Control/OSC/web选项，配置web信息，端口号为2307
![在Reaper中启用Reapy监听端口](/article/reaper_reapy_server_setting.png)
4. 在Reaper的Action中，选择Load-Action，并从Reapy库中选择activate_reapy_server.py文件，运行改脚本启动Reapy在Reaper中的Server
![在Reaper中启用Reapy服务器](/article/reapy_reaper_server.png)

## 配置MCP库
本文使用VS Code作为MCP Host，其他Host使用方法同理

MCP Server使用的虚拟环境为uv

**MCP Server 配置信息**
```JSON
"mcp": {
        "inputs": [],
        "servers": {
            "pxqmr": {
                "command": "uv",
                "args": [
                    "--directory",
                    "C:\\Users\\PXQ\\Desktop\\mcpreaper\\pxqmr", **这里替换成你的运行位置**
                    "run",
                    "main.py"
                ]
            }
        }
    }
```
4. 打开Copilot，选择Agent模式，就会看到加载了两个MCP工具。
![Copilot](/article/agent_mode.png)

# 在运行前，务必替换pxqmr/main.py和resource/description.txt中的绝对地址内容

## 文件夹说明
article: 文档中使用的图片

pxqmr: MCP Server本体，main.py是MCP Tools的实现代码

resource：测试用音频，a-g都是同样的声音

testpy: 开发过程中的一些实验代码，Jupyter Notebook中是Reapy的测试代码

## 运行示例
![运行示例](/article/full_processing.png)
![导入效果](/article/after_import.png)


## 工具列表
| 函数名 | 功能概述 | 参数示例 |
|---------|----------|------------|
| `mcp_server_init_get_audio_description` | 获取音频描述文件信息 | - |
| `reaper_get_current_project` | 获取当前REAPER项目信息 | - |
| `reaper_add_track` | 创建新音轨 | `track_name="Guitar"` |
| `reaper_select_track` | 选择指定音轨 | `track_name="Drums"` |
| `reaper_get_all_tracksName` | 获取所有音轨名称列表 | - |
| `reaper_get_all_takeinfo_by_trakename` | 获取指定音轨的所有Take信息 | `track_name="Vocals"` |
| `reaper_insert_audio_into_track_at` | 在指定时间点导入音频到音轨 | `track_name="Bass", file_path="...", insert_at_time_position=10.5` |
| `reaper_set_mediaTrack_vol` | 设置音轨音量(线性值) | `track_name="Piano", volume=1.0` (0~4) |
| `reaper_set_mediaTrack_vol_bydB` | 设置音轨音量(分贝值) | `track_name="Master", volume=0.0` (-100~12dB) |