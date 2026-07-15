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
