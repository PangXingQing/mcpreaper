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
    register_project_tools,
    register_envelope_tools,
    register_send_tools,
    register_render_tools,
    register_midi_ext_tools,
    register_audio_tools,
    register_eq_tools,
    register_film_tools,
    register_generate_tools
)
from utils import (
    reaper_tool_error_handler,
    format_success_response,
    format_error_response,
    OperationFailedError,
    FileNotFoundError as ReaperFileNotFoundError
)

mcp = FastMCP("pxqmr")

file_info_list = None

WAV_DIR = os.path.join(os.path.dirname(__file__), "WAV")
RES_DES_PATH = os.path.join(WAV_DIR, "description.txt")

@mcp.tool()
@reaper_tool_error_handler
def reaper_get_audio_description() -> dict:
    """
    获取音频描述文件信息。
    
    Returns:
        音频描述信息列表，包含success字段和data数据
    """
    global file_info_list
    if file_info_list is None or file_info_list == []:
        file_info_list = []
        if not os.path.exists(RES_DES_PATH):
            raise ReaperFileNotFoundError(RES_DES_PATH)
        
        try:
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
        except Exception as e:
            raise OperationFailedError("读取音频描述文件", str(e))
    
    return format_success_response(data={"audio_descriptions": file_info_list, "count": len(file_info_list)})

@mcp.tool()
@reaper_tool_error_handler
def reaper_list_audio_files() -> dict:
    """
    列出所有可用的音频文件。
    
    Returns:
        音频文件列表，包含success字段和data数据
    """
    if not os.path.exists(WAV_DIR):
        raise ReaperFileNotFoundError(WAV_DIR)
    
    try:
        audio_files = []
        for filename in os.listdir(WAV_DIR):
            if filename.lower().endswith(('.wav', '.mp3', '.flac', '.ogg')):
                file_path = os.path.join(WAV_DIR, filename)
                audio_files.append({
                    'filename': filename,
                    'file_path': file_path
                })
        return format_success_response(data={"audio_files": audio_files, "count": len(audio_files)})
    except Exception as e:
        raise OperationFailedError("列出音频文件", str(e))

register_track_tools(mcp)
register_item_tools(mcp)
register_playback_tools(mcp)
register_fx_tools(mcp)
register_marker_tools(mcp)
register_midi_tools(mcp)
register_project_tools(mcp)
register_envelope_tools(mcp)
register_send_tools(mcp)
register_render_tools(mcp)
register_midi_ext_tools(mcp)
register_audio_tools(mcp)
register_eq_tools(mcp)
register_film_tools(mcp)
register_generate_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')