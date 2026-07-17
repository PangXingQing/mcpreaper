from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    reaper_tool_error_handler,
    InvalidParameterError,
    OperationFailedError,
    format_success_response
)

def register_marker_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_marker(time: float = 0.0, marker_name: str = "") -> dict:
        """
        在指定位置添加标记。
        
        Args:
            time: 标记位置（秒，>= 0）
            marker_name: 标记名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if time < 0:
            raise InvalidParameterError("time", time, "有效值范围：>= 0")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.AddProjectMarker(project, False, time, 0, marker_name, -1)
            return format_success_response(message=f"成功在{time}秒处添加标记「{marker_name}」。")
        except Exception as e:
            raise OperationFailedError("添加标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_add_region(start_time: float = 0.0, end_time: float = 0.0, region_name: str = "") -> dict:
        """
        添加区域。
        
        Args:
            start_time: 区域开始时间（秒，>= 0）
            end_time: 区域结束时间（秒，> start_time）
            region_name: 区域名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if start_time < 0:
            raise InvalidParameterError("start_time", start_time, "有效值范围：>= 0")
        
        if end_time <= start_time:
            raise InvalidParameterError(
                "end_time", end_time,
                f"必须大于开始时间({start_time})，请提供更大的值"
            )
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            reaper.AddProjectMarker(project, True, start_time, end_time, region_name, -1)
            return format_success_response(message=f"成功添加区域「{region_name}」，范围{start_time}秒到{end_time}秒。")
        except Exception as e:
            raise OperationFailedError("添加区域", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_all_markers() -> dict:
        """
        获取所有标记和区域。
        
        Returns:
            标记和区域信息字典，包含success字段和markers数据列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            markers = []
            retval, _p, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            
            for i in range(num_markers):
                enum_result = reaper.EnumProjectMarkers(i, 0, 0, 0, '', 256)
                retval, is_region, _, pos, rgn_end, name, markrgnindex = enum_result
                markers.append({
                    "index": i,
                    "name": name,
                    "is_region": bool(is_region),
                    "position": pos,
                    "end_position": rgn_end if is_region else None
                })
            
            return format_success_response(data={"markers": markers, "count": len(markers)})
        except Exception as e:
            raise OperationFailedError("获取标记信息", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_marker(index: int = 0) -> dict:
        """
        删除指定标记或区域。
        
        Args:
            index: 标记/区域索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if index < 0:
            raise InvalidParameterError("index", index, "有效值范围：>= 0")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            retval, _p, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total_count = num_markers + num_regions
            if index >= total_count:
                raise InvalidParameterError(
                    "index", index,
                    f"有效值范围：[0, {total_count-1}]，项目共有{total_count}个标记/区域（{num_markers}个标记，{num_regions}个区域）"
                )
            
            enum_result = reaper.EnumProjectMarkers(index, 0, 0, 0, '', 256)
            retval, is_region, _, pos, rgn_end, name, markrgnindex = enum_result
            reaper.DeleteProjectMarker(project, markrgnindex, is_region)
            
            type_name = "区域" if is_region else "标记"
            return format_success_response(message=f"成功删除{type_name}「{name}」。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("删除标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_rename_marker(index: int = 0, new_name: str = "") -> dict:
        """
        重命名标记或区域。
        
        Args:
            index: 标记/区域索引（从0开始，>= 0）
            new_name: 新名称
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if index < 0:
            raise InvalidParameterError("index", index, "有效值范围：>= 0")
        
        if not new_name:
            raise InvalidParameterError("new_name", new_name, "请提供有效的新名称")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            retval, _p, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total_count = num_markers + num_regions
            if index >= total_count:
                raise InvalidParameterError(
                    "index", index,
                    f"有效值范围：[0, {total_count-1}]，项目共有{total_count}个标记/区域（{num_markers}个标记，{num_regions}个区域）"
                )
            
            enum_result = reaper.EnumProjectMarkers(index, 0, 0, 0, '', 256)
            retval, is_region, _, pos, rgn_end, old_name, markrgnindex = enum_result
            reaper.SetProjectMarker(markrgnindex, is_region, pos, rgn_end, new_name)
            
            type_name = "区域" if is_region else "标记"
            return format_success_response(message=f"成功将{type_name}「{old_name}」重命名为「{new_name}」。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("重命名标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_go_to_marker(index: int = 0) -> dict:
        """
        跳转到指定标记位置。
        
        Args:
            index: 标记索引（从0开始，>= 0）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if index < 0:
            raise InvalidParameterError("index", index, "有效值范围：>= 0")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            retval, _p, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total_count = num_markers + num_regions
            if index >= total_count:
                raise InvalidParameterError(
                    "index", index,
                    f"有效值范围：[0, {total_count-1}]，项目共有{total_count}个标记/区域（{num_markers}个标记，{num_regions}个区域）"
                )
            
            enum_result = reaper.EnumProjectMarkers(index, 0, 0, 0, '', 256)
            retval, is_region, _, pos, rgn_end, name, markrgnindex = enum_result
            reaper.SetEditCurPos(pos, True, False)
            
            return format_success_response(message=f"已跳转到标记「{name}」位置：{pos}秒。")
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("跳转标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_clear_all_markers() -> dict:
        """
        清除工程中的所有标记和区域。

        警告：此操作不可逆！请先确认需要清除。

        Returns:
            操作结果，包含清除的标记/区域数量
        """
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total = num_markers + num_regions

            # 从后往前删除普通标记
            for i in range(num_markers - 1, -1, -1):
                try:
                    reaper.DeleteProjectMarker(project, i, False)
                except Exception:
                    pass

            # 从后往前删除区域
            for i in range(num_regions - 1, -1, -1):
                try:
                    reaper.DeleteProjectMarker(project, i, True)
                except Exception:
                    pass

            return format_success_response(
                message=f"已清除 {total} 个标记/区域（{num_markers} 个标记 + {num_regions} 个区域）",
                data={"cleared_markers": num_markers, "cleared_regions": num_regions},
            )
        except Exception as e:
            raise OperationFailedError("清除标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_find_marker_by_name(marker_name: str = "") -> dict:
        """
        按名称查找标记或区域。

        Args:
            marker_name: 标记名称（模糊匹配，大小写敏感）

        Returns:
            匹配的标记信息列表
        """
        if not marker_name:
            raise InvalidParameterError("marker_name", marker_name, "请提供要查找的标记名称")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total = num_markers + num_regions
            found = []

            for i in range(total):
                enum_result = reaper.EnumProjectMarkers(i, 0, 0, 0, '', 256)
                retval, is_region, _, pos, rgn_end, name, markrgnindex = enum_result
                if marker_name.lower() in name.lower():
                    found.append({
                        "index": i,
                        "markrgn_index": markrgnindex,
                        "name": name,
                        "is_region": bool(is_region),
                        "position": round(pos, 3),
                        "end_position": round(rgn_end, 3) if is_region else None,
                    })

            if not found:
                return format_success_response(
                    message=f"未找到包含「{marker_name}」的标记",
                    data={"results": [], "total": 0},
                )

            return format_success_response(
                message=f"找到 {len(found)} 个匹配的标记",
                data={"results": found, "total": len(found)},
            )
        except Exception as e:
            raise OperationFailedError("查找标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_move_marker(index: int = 0, new_time: float = 0.0) -> dict:
        """
        移动标记或区域到新的时间位置。

        Args:
            index: 标记/区域索引
            new_time: 新的时间位置（秒，>= 0）

        Returns:
            操作结果
        """
        if index < 0:
            raise InvalidParameterError("index", index, "必须 >= 0")
        if new_time < 0:
            raise InvalidParameterError("new_time", new_time, "必须 >= 0")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total = num_markers + num_regions
            if index >= total:
                raise InvalidParameterError(
                    "index", index,
                    f"有效范围：[0, {total - 1}]"
                )

            enum_result = reaper.EnumProjectMarkers(index, 0, 0, 0, '', 256)
            retval, is_region, _, _, rgn_end, name, markrgnindex = enum_result

            if is_region:
                duration = rgn_end - reaper.EnumProjectMarkers(
                    index, 0, 0, 0, '', 256
                )[3] if retval else 0
                reaper.SetProjectMarker(markrgnindex, True, new_time, new_time + duration, name)
            else:
                reaper.SetProjectMarker(markrgnindex, False, new_time, 0, name)

            type_name = "区域" if is_region else "标记"
            return format_success_response(
                message=f"已将{type_name}「{name}」移动到 {new_time:.3f}s"
            )
        except InvalidParameterError:
            raise
        except Exception as e:
            raise OperationFailedError("移动标记", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_markers_in_range(start_time: float = 0.0, end_time: float = 0.0) -> dict:
        """
        获取指定时间范围内的所有标记和区域。

        Args:
            start_time: 起始时间（秒）
            end_time: 结束时间（秒，必须 > start_time）

        Returns:
            范围内的标记列表
        """
        if start_time < 0:
            raise InvalidParameterError("start_time", start_time, "必须 >= 0")
        if end_time <= start_time:
            raise InvalidParameterError("end_time", end_time, f"必须 > {start_time}")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)

        try:
            from reapy import reascript_api as reaper
            retval, _, num_markers, num_regions = reaper.CountProjectMarkers(project, 0, 0)
            total = num_markers + num_regions
            in_range = []

            for i in range(total):
                enum_result = reaper.EnumProjectMarkers(i, 0, 0, 0, '', 256)
                retval, is_region, _, pos, rgn_end, name, markrgnindex = enum_result
                if start_time <= pos <= end_time:
                    in_range.append({
                        "index": i,
                        "name": name,
                        "is_region": bool(is_region),
                        "position": round(pos, 3),
                        "end_position": round(rgn_end, 3) if is_region else None,
                    })

            return format_success_response(
                message=f"在 [{start_time:.2f}s, {end_time:.2f}s] 范围内找到 {len(in_range)} 个标记",
                data={"results": in_range, "total": len(in_range), "range": {"start": start_time, "end": end_time}},
            )
        except Exception as e:
            raise OperationFailedError("获取范围标记", str(e))
