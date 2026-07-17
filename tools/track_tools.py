from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    get_track_by_name,
    update_arrange,
    reaper_tool_error_handler,
    TrackNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
    get_available_track_names
)

def register_track_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_track(track_name: str = "") -> dict:
        """
        在Reaper中创建新音轨。
        
        Args:
            track_name: 新音轨的名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track = project.add_track(0, track_name)
            track.make_only_selected_track()
            update_arrange()
            return format_success_response(message=f"成功创建音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("创建音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_select_track(track_name: str = "") -> dict:
        """
        选择指定音轨。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.make_only_selected_track()
            update_arrange()
            return format_success_response(message=f"成功选择音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("选择音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_all_tracks() -> dict:
        """
        获取所有音轨信息。
        
        Returns:
            音轨信息字典，包含success字段和tracks数据列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track_info = []
            for track in project.tracks:
                track_info.append({
                    "name": track.name,
                    "volume": track.get_info_value('D_VOL'),
                    "pan": track.get_info_value('D_PAN'),
                    "mute": bool(track.get_info_value('B_MUTE')),
                    "solo": bool(track.get_info_value('I_SOLO')),
                    "rec_arm": bool(track.get_info_value('I_RECARM')),
                    "num_items": len(track.items),
                    "num_fx": len(track.fxs)
                })
            return format_success_response(data={"tracks": track_info, "count": len(track_info)})
        except Exception as e:
            raise OperationFailedError("获取音轨信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_all_track_names() -> dict:
        """
        获取所有音轨名称。
        
        Returns:
            音轨名称列表字典，包含success字段和track_names数据
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            track_names = [track.name for track in project.tracks]
            return format_success_response(data={"track_names": track_names, "count": len(track_names)})
        except Exception as e:
            raise OperationFailedError("获取音轨名称", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_track(track_name: str = "") -> dict:
        """
        删除指定音轨。
        
        Args:
            track_name: 要删除的音轨名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.delete()
            update_arrange()
            return format_success_response(message=f"成功删除音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("删除音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_rename_track(track_name: str = "", new_name: str = "") -> dict:
        """
        重命名音轨。
        
        Args:
            track_name: 当前音轨名称
            new_name: 新名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if not new_name:
            raise InvalidParameterError("new_name", new_name, "请提供有效的新名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            old_name = track.name
            track.name = new_name
            update_arrange()
            return format_success_response(message=f"成功将音轨「{old_name}」重命名为「{new_name}」。")
        except Exception as e:
            raise OperationFailedError("重命名音轨", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_volume(track_name: str = "", volume: float = 1.0) -> dict:
        """
        设置音轨音量（线性值）。
        
        Args:
            track_name: 音轨名称
            volume: 音量值，范围[0, 4]，其中0=-inf, 0.5=-6dB, 1=+0dB, 2=+6dB, 4=+12dB
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if volume < 0 or volume > 4:
            raise InvalidParameterError("volume", volume, "有效值范围：[0, 4]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.set_info_value('D_VOL', volume)
            update_arrange()
            db_value = 20 * (volume ** (1/10)) if volume > 0 else "-inf"
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的音量为{volume}（约{db_value}dB）。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨音量", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_volume_db(track_name: str = "", volume_db: float = 0.0) -> dict:
        """
        设置音轨音量（分贝值）。
        
        Args:
            track_name: 音轨名称
            volume_db: 分贝值，范围[-100, +12]dB
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            if volume_db < -100:
                track.set_info_value('D_VOL', 0)
                display_val = "-inf"
            elif volume_db > 12:
                track.set_info_value('D_VOL', 4)
                display_val = "+12dB"
            else:
                track.set_info_value('D_VOL', 10 ** (volume_db / 20))
                display_val = f"{volume_db}dB"
            update_arrange()
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的音量为{display_val}。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨音量（分贝）", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_pan(track_name: str = "", pan: float = 0.0) -> dict:
        """
        设置音轨声相。
        
        Args:
            track_name: 音轨名称
            pan: 声相值，范围[-1, 1]，-1=左，0=中，1=右
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        if pan < -1 or pan > 1:
            raise InvalidParameterError("pan", pan, "有效值范围：[-1, 1]")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            track.set_info_value('D_PAN', pan)
            update_arrange()
            pan_label = "左" if pan < -0.1 else ("右" if pan > 0.1 else "中")
            return format_success_response(
                message=f"成功设置音轨「{track_name}」的声相为{pan}（{pan_label}）。"
            )
        except Exception as e:
            raise OperationFailedError("设置音轨声相", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_mute(track_name: str = "", mute: bool = False) -> dict:
        """
        设置音轨静音状态。
        
        Args:
            track_name: 音轨名称
            mute: 是否静音
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            if mute:
                track.mute()
            else:
                track.unmute()
            update_arrange()
            status = "静音" if mute else "取消静音"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置音轨静音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_solo(track_name: str = "", solo: bool = False) -> dict:
        """
        设置音轨独奏状态。
        
        Args:
            track_name: 音轨名称
            solo: 是否独奏
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetMediaTrackInfo_Value(track, 'I_SOLO', int(solo))
            update_arrange()
            status = "独奏" if solo else "取消独奏"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置音轨独奏", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_rec_arm(track_name: str = "", rec_arm: bool = False) -> dict:
        """
        设置音轨录音准备状态。
        
        Args:
            track_name: 音轨名称
            rec_arm: 是否启用录音准备
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            from reapy import reascript_api as reaper
            reaper.SetMediaTrackInfo_Value(track, 'I_RECARM', int(rec_arm))
            update_arrange()
            status = "启用录音准备" if rec_arm else "禁用录音准备"
            return format_success_response(message=f"成功{status}音轨「{track_name}」。")
        except Exception as e:
            raise OperationFailedError("设置录音准备", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_info(track_name: str = "") -> dict:
        """
        获取指定音轨的详细信息。
        
        Args:
            track_name: 音轨名称
        
        Returns:
            音轨信息字典，包含success字段和音轨详细信息
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        
        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)
        
        try:
            return format_success_response(data={
                "name": track.name,
                "volume": track.get_info_value('D_VOL'),
                "pan": track.get_info_value('D_PAN'),
                "mute": bool(track.get_info_value('B_MUTE')),
                "solo": bool(track.get_info_value('I_SOLO')),
                "rec_arm": bool(track.get_info_value('I_RECARM')),
                "num_items": len(track.items),
                "num_fx": len(track.fxs)
            })
        except Exception as e:
            raise OperationFailedError("获取音轨详细信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_color(track_name: str = "", color: str = "") -> dict:
        """
        设置音轨颜色。

        支持十六进制颜色码（如 #FF0000 = 红色）或颜色名称（red/green/blue/yellow/purple/orange/pink/cyan/white/black）。

        Args:
            track_name: 音轨名称
            color: 颜色值，如 "#FF0000" 或 "red"。使用 "none" 清除颜色。

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")
        if not color:
            raise InvalidParameterError("color", color, "请提供颜色值，如 '#FF0000' 或 'red'")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        # 颜色名称映射
        color_map = {
            "red": 0xFF0000, "green": 0x00FF00, "blue": 0x0000FF,
            "yellow": 0xFFFF00, "purple": 0x800080, "orange": 0xFFA500,
            "pink": 0xFFC0CB, "cyan": 0x00FFFF, "white": 0xFFFFFF,
            "black": 0x000000, "none": 0,
        }

        try:
            from reapy import reascript_api as reaper
            if color.lower() in color_map:
                color_int = color_map[color.lower()]
            elif color.startswith("#") and len(color) == 7:
                color_int = int(color[1:], 16)
            else:
                raise InvalidParameterError(
                    "color", color,
                    "请使用 #RRGGBB 格式或颜色名称",
                    "例如 '#FF0000' 或 'red'"
                )

            # REAPER 颜色格式: 0xRRGGBB | 0x1000000 表示自定义颜色
            if color_int > 0:
                color_int = color_int | 0x1000000
            reaper.SetTrackColor(track, color_int)
            return format_success_response(
                message=f"音轨「{track_name}」颜色已更新",
                data={"color": color, "color_int": color_int},
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置音轨颜色", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_set_track_group(track_name: str = "", group_name: str = "") -> dict:
        """
        将音轨分配到编组（通过设置音轨的 Group 标志）。

        REAPER 支持对音轨设置 Group 标志（0=无分组，1-64=组号），
        同组的音轨可以联动调整音量等参数。

        Args:
            track_name: 音轨名称
            group_name: 组名或组号。可以使用数字 "1"-"64"，也可以使用 "none" 取消分组。

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            import re
            from reapy import reascript_api as reaper

            if group_name.lower() == "none":
                group_id = 0
            elif re.match(r'^\d+$', group_name):
                group_id = int(group_name)
                if group_id < 0 or group_id > 64:
                    raise InvalidParameterError(
                        "group_name", group_name,
                        "有效组号：[0, 64]，0=无分组"
                    )
            else:
                raise InvalidParameterError(
                    "group_name", group_name,
                    "请使用数字组号（如 '1'）或 'none' 取消分组",
                    "例如 reaper_set_track_group(track_name='鼓组', group_name='1')"
                )

            reaper.SetTrackGroup(track, group_id)
            action = "分配到" + (f"组 {group_id}" if group_id > 0 else "取消分组")
            return format_success_response(
                message=f"音轨「{track_name}」已{action}",
                data={"group_id": group_id},
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("设置音轨分组", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_track_folder(
        folder_name: str = "",
        child_tracks: list = None,
    ) -> dict:
        """
        创建文件夹轨道，并将子轨道放入其中。

        文件夹轨道是 REAPER 中组织和管理多条轨道的层级结构。
        文件夹轨道在混音器中表现为一个"总线"，子轨道的音频会经过文件夹轨道。

        Args:
            folder_name: 文件夹轨道名称
            child_tracks: 子轨道名称列表，如 ["Guitar 1", "Guitar 2"]

        Returns:
            操作结果，包含文件夹和子轨道信息
        """
        if not folder_name:
            raise InvalidParameterError("folder_name", folder_name, "请提供文件夹名")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        if child_tracks is None:
            child_tracks = []

        try:
            from reapy import reascript_api as reaper

            # 创建文件夹轨道
            folder_track = project.add_track(len(project.tracks), folder_name)
            folder_track.make_only_selected_track()

            # 设置为文件夹
            reaper.SetMediaTrackInfo_Value(folder_track, "I_FOLDERDEPTH", 1)

            # 处理子轨道
            added_children = []
            for child_name in child_tracks:
                child = get_track_by_name(child_name)
                if child is None:
                    # 创建子轨道
                    child = project.add_track(len(project.tracks), child_name)
                    added_children.append(f"{child_name} (新建)")

                # 将子轨道移入文件夹
                # 最后一个子轨道设置 I_FOLDERDEPTH = -1（结束文件夹）
                reaper.SetMediaTrackInfo_Value(child, "I_FOLDERDEPTH", 0)

            if child_tracks:
                # 最后一个子轨道结束文件夹
                last_child = get_track_by_name(child_tracks[-1])
                if last_child:
                    reaper.SetMediaTrackInfo_Value(last_child, "I_FOLDERDEPTH", -1)

            update_arrange()
            return format_success_response(
                message=f"文件夹轨道「{folder_name}」已创建",
                data={
                    "folder": folder_name,
                    "children": child_tracks,
                    "new_children": added_children,
                },
            )
        except Exception as e:
            raise OperationFailedError("创建文件夹轨道", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_duplicate_track(track_name: str = "") -> dict:
        """
        复制指定音轨（包括其所有媒体项和设置）。

        Args:
            track_name: 要复制的音轨名称

        Returns:
            操作结果，包含新音轨名称
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的音轨名称")

        track = get_track_by_name(track_name)
        if track is None:
            avail = get_available_track_names()
            raise TrackNotFoundError(track_name, avail)

        try:
            from reapy import reascript_api as reaper
            reaper.SetOnlyTrackSelected(track)
            reaper.Main_OnCommand(40062, 0)  # Track: Duplicate tracks
            update_arrange()
            return format_success_response(
                message=f"音轨「{track_name}」已复制",
                data={"original": track_name},
            )
        except (TrackNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("复制音轨", str(e))