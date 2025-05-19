import os
from typing import Any

import reapy.reascripts
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP server
mcp = FastMCP("pxqmr")
file_info_list = None
project = None

# 这里替换成你的运行位置
RES_DES_PATH = "C:\\Users\\PXQ\\Desktop\\mcpreaper\\WAV\\description.txt"

def helper_reaper_get_current_project() -> tuple[bool, str]:
    global project
    if project is None:
        try:
            import reapy
            project = reapy.Project()
            return (True, f"当前Reaper项目名称为：{project.name}，路径为：{project.path}。")
        except Exception as e:
            return (False, f"无法打开REAPER工程，请检查REAPER是否打开，以及是否开启了reapy server。\r\n详细错误：{e}")
    return (True, f"当前Reaper项目名称为：{project.name}，路径为：{project.path}。")

def helper_reaper_get_takeinfo_by_trackname_or_time(track_name = "", take_name = "", time_position: float = 0.0) -> []:
    takes_info = []
    success, message = helper_reaper_get_current_project()
    if not success:
        return takes_info
    track = project._get_track_by_name(track_name)
    if track is None:
        return takes_info
    
    try:
        time_position = float(time_position)  # Ensure the time position is a float
    except ValueError:
        return takes_info
    
    import reapy
    from reapy import reascript_api as reaper
    takes_info = []
    for item in track.items:
            for take in item.takes:
                if item.position == time_position or take.name == take_name:
                    takes_info.append(take)
    return takes_info

@mcp.tool()
def mcp_server_init_get_audio_description() -> dict[str, str] | None:
    """
    _summary_ 考虑到MCP Resource还没有被所有客户端支持，因此将资源描述文件信息的获取转变为MCP Tool的形式。\r\n
    该函数会返回一个字典，包含音频描述信息和文件路径。

    Args:
        None

    Returns:
        dict[str, str] | None: _description_ 已经被格式化过的音频描述信息
    """
    global file_info_list
    if file_info_list is None or file_info_list == []:
        file_info_list = []
        try:
            with open(RES_DES_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # Split by $$$ character
                        parts = line.split("$$$")
                        if len(parts) == 2:
                            # Combine WAV directory path with the file path from description
                            wav_dir = str(RES_DES_PATH).rsplit('\\', 1)[0]
                            file_info_list.append({
                                'description': parts[0],
                                'file_path': os.path.join(wav_dir, parts[1])
                            })
        except Exception as e:
            return f"无法读取音频描述文件，请检查文件路径和格式。当前路径为：{RES_DES_PATH}\r\n详细错误：{e}"
        return file_info_list

@mcp.tool()
def reaper_get_current_project() -> str:
    """
    _summary_ 获取当前Reaper项目的名称和路径。\r\n
    该函数会返回一个字典，包含音频描述信息和文件路径。

    Args:
        None

    Returns:
        dict[str, str] | None: _description_ 已经被格式化过的音频描述信息
    """
    state, message = helper_reaper_get_current_project()
    return message


@mcp.tool()
def reaper_add_track(track_name = "") -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    根据track_name创建一个新的Track，并将其设置为选中状态。\r\n
    Args:
        track_name (str, optional): _description_. 新Track的名称，根据场景创建

    Returns:
        str: _description_ 导入结果
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project.add_track(0, track_name)
    track.make_only_selected_track()
    return f"成功创建音轨{track_name}。"

@mcp.tool()
def reaper_select_track(track_name = "") -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    根据track_name选择一个Track，并将其设置为选中状态。\r\n
    Args:
        track_name (str, optional): _description_. 新Track的名称，根据场景创建

    Returns:
        str: _description_ 导入结果
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project._get_track_by_name(track_name)
    if track is None:
        return f"没有找到音轨{track_name}。"
    track.make_only_selected_track()
    return f"成功选择音轨{track_name}。"

@mcp.tool()
def reaper_get_all_tracksName() -> []:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    获取当前Reaper项目中所有音轨的名称，并返回一个列表。\r\n
    Args:
        None

    Returns:
        []: _description_ 音轨名称列表
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track_names = [track.name for track in project.tracks]
    return track_names
   

@mcp.tool()
def reaper_get_all_takeinfo_by_trakename(track_name = "") -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    获取当前Reaper项目中某个轨道（Track）中所有场（Take）的信息。\r\n
    Args:
        track_name (str, optional): _description_. Track轨道的名称

    Returns:
        str: _description_ 场（Take）信息
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project._get_track_by_name(track_name)
    if track is None:
        return f"没有找到音轨{track_name}。"
    
    import reapy
    takes = helper_reaper_get_takeinfo_by_trackname_or_time(track_name=track_name)
    if takes.count() == 0:
        return f"音轨{track_name}没有找到任何场（Take）。"
    else:
        t = reapy.Take()
        
        take_info = []
        for take in takes:
            
            take_info.append({
                'name': take.name,
                'position': take.item.position,
                'length': take.item.length,
                'volume': take.volume,
                'pan': take.pan,
                'mute': take.mute
            })
        return take_info

@mcp.tool()
def reaper_insert_audio_into_track_at(track_name = "", file_path_obsolute = "", insert_at_time_position: float = 0.0) -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    在Reaper中选择一个Track，并将音频文件导入到指定时间点。
    Args:
        track_name (str, optional): _description_. 新Track的名称，根据场景创建
        file_path_obsolute (str, optional): _description_. Defaults to 导入的音频文件地址，需要是绝对地址.
        insert_at_time_position (float, optional): _description_. 音频在轨道中的时间未知，单位为秒，应为数字.

    Returns:
        str: _description_ 导入结果
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project._get_track_by_name(track_name)
    if track is None:
        return f"没有找到音轨{track_name}。"
    track.make_only_selected_track()
    if not os.path.exists(file_path_obsolute):
        return f"音频文件{file_path_obsolute}不存在，请检查路径是否正确。"
    
    try:
        insert_at_time_position = float(insert_at_time_position)  # Ensure the time position is a float
    except ValueError:
        return f"时间位置参数无效：{insert_at_time_position}，请提供一个有效的数字。"
    
    import reapy
    from reapy import reascript_api as reaper
    reaper.InsertMedia(file_path_obsolute, 0)
    item = track.items[-1]
    item.position = insert_at_time_position
    reaper.UpdateArrange()
    return f"成功创建音轨{track_name}，并导入音频文件{file_path_obsolute}到{insert_at_time_position}秒处。"

@mcp.tool()
def reaper_set_mediaTrack_vol(track_name = "", volume: float = 0.0) -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    设置音轨的音量，首先应当选择对应音轨，随后进行响度设定，0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB, 取值范围为[0, 4]。
    Args:
        track_name (str, optional): _description_. track的名称
        volume (float, optional): _description_. 0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB, 取值范围为[0, 4]。

    Returns:
        str: _description_ 结果
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project._get_track_by_name(track_name)
    if track is None:
        return f"没有找到音轨{track_name}。"

    if volume < 0 or volume > 4:
        return f"音量参数无效：{volume}， 0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB, 取值范围为[0, 4]。"
    
    import reapy
    from reapy import reascript_api as reaper
    track.make_only_selected_track()
    track.set_info_value("D_VOL", volume)
    reaper.UpdateArrange()
    return f"成功设置音轨{track_name}的音量为{volume}。"

@mcp.tool()
def reaper_set_mediaTrack_vol_bydB(track_name = "", volume: float = 0.0) -> str:
    """
    _summary_ 使用前需要确认已经在REAPER中创建并保存项目，同时打开了Reapy Server。\r\n
    设置音轨的音量，首先应当选择对应音轨，随后进行响度设定，取值范围为[-100, +12]dB，小于-100dB时表示-inf。
    Args:
        track_name (str, optional): _description_. track的名称
        volume (float, optional): _description_. 取值范围为[-100, +12]dB，小于-100dB时表示-inf。

    Returns:
        str: _description_ 结果
    """
    success, message = helper_reaper_get_current_project()
    if not success:
        return message
    track = project._get_track_by_name(track_name)
    if track is None:
        return f"没有找到音轨{track_name}。"
    
    import reapy
    from reapy import reascript_api as reaper
    track.make_only_selected_track()
    if volume < -100:
        track.set_info_value("D_VOL", 0)
    elif volume > 12:
        track.set_info_value("D_VOL", 4)
    else:
        track.set_info_value("D_VOL", 10 ** (volume / 20))
    reaper.UpdateArrange()
    
    if volume < -100:
        return f"成功设置音轨{track_name}的音量为-inf。"
    elif volume > 12:
        return f"成功设置音轨{track_name}的音量为+12dB。"
    else:
        return f"成功设置音轨{track_name}的音量为{volume}dB。"

if __name__ == "__main__":
    # 初始化并运行 server
    mcp.run(transport='stdio')