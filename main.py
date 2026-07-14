import os
from typing import Any
from mcp.server.fastmcp import FastMCP
from tools import (
    register_track_tools,
    register_item_tools,
    register_playback_tools,
    register_fx_tools,
    register_marker_tools,
    register_midi_tools,
    register_project_tools
)

mcp = FastMCP("pxqmr")

file_info_list = None

WAV_DIR = os.path.join(os.path.dirname(__file__), "WAV")
RES_DES_PATH = os.path.join(WAV_DIR, "description.txt")

@mcp.tool()
def reaper_get_audio_description() -> Any:
    """
    获取音频描述文件信息。
    
    Returns:
        音频描述信息列表
    """
    global file_info_list
    if file_info_list is None or file_info_list == []:
        file_info_list = []
        try:
            if not os.path.exists(RES_DES_PATH):
                return {"error": f"描述文件不存在：{RES_DES_PATH}"}
            with open(RES_DES_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split("$$$")
                        if len(parts) == 2:
                            file_info_list.append({
                                'description': parts[0],
                                'file_path': os.path.join(WAV_DIR, parts[1])
                            })
            return file_info_list
        except Exception as e:
            return {"error": f"读取音频描述文件失败：{e}"}
    return file_info_list

@mcp.tool()
def reaper_list_audio_files() -> list[dict]:
    """
    列出所有可用的音频文件。
    
    Returns:
        音频文件列表
    """
    try:
        if not os.path.exists(WAV_DIR):
            return [{"error": f"WAV目录不存在：{WAV_DIR}"}]
        audio_files = []
        for filename in os.listdir(WAV_DIR):
            if filename.lower().endswith(('.wav', '.mp3', '.flac', '.ogg')):
                file_path = os.path.join(WAV_DIR, filename)
                audio_files.append({
                    'filename': filename,
                    'file_path': file_path
                })
        return audio_files
    except Exception as e:
        return [{"error": str(e)}]

register_track_tools(mcp)
register_item_tools(mcp)
register_playback_tools(mcp)
register_fx_tools(mcp)
register_marker_tools(mcp)
register_midi_tools(mcp)
register_project_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')