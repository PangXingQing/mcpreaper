from typing import Any
from mcp.server.fastmcp import FastMCP
import reapy
from reapy import reascript_api as reaper

# 初始化 FastMCP server
mcp = FastMCP("pxqmr")
description_file = None
project = None

# 这里替换成你的运行位置
RES_DES_PATH = "C:\\Users\\PXQ\\Desktop\\mcpreaper\\resource\\description.txt"


def load_description_file(file_path) -> dict[str, str] | None:
    file_info_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Split by $$$ character
                    parts = line.split("$$$")
                    if len(parts) == 2:
                        file_info_list.append({
                            'description': parts[0],
                            'file_path': parts[1]
                        })
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    return file_info_list

@mcp.tool()
def get_audio_description() -> dict[str, str] | None:
    """
    _summary_ 当用户输入一个视频场景或者需要获取音频与音频描述时
    ，该方法会被调用，并返回资源库中所有的音频描述文件，并且这些数据
    已经被格式化完毕。

    Args:
        None

    Returns:
        dict[str, str] | None: _description_ 已经被格式化过的音频描述信息
    """
    return description_file

@mcp.tool()
def import_audio_into_reaper(track_name = "", file_path_obsolute = "", insert_at_time_position = 0.0) -> str:
    """
    _summary_ 在Reaper中创建一个新的Track，并将音频文件导入到指定时间点。
    Args:
        track_name (str, optional): _description_. 新Track的名称，根据场景创建
        file_path_obsolute (str, optional): _description_. Defaults to 导入的音频文件地址，需要是绝对地址.
        insert_at_time_position (float, optional): _description_. 音频在轨道中的时间未知，单位为秒，应为数字.

    Returns:
        str: _description_ 导入结果
    """
    track = project.add_track(0, track_name)
    track.make_only_selected_track()
    reaper.InsertMedia(file_path_obsolute, 0)
    # item = track.items[0] 
    # item.position = insert_at_time_position
    reaper.UpdateArrange()
    return f"Insert file into track at time in second in REAPER."


if __name__ == "__main__":
    # 初始化并运行 server
    project = reapy.Project()
    description_file = load_description_file(RES_DES_PATH)
    mcp.run(transport='stdio')