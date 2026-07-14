from mcp.server.fastmcp import FastMCP
from utils.reaper_client import ensure_project_ready

def register_marker_tools(mcp: FastMCP):

    @mcp.tool()
    def reaper_add_marker(time: float = 0.0, name: str = "") -> str:
        """
        在指定位置添加标记。
        
        Args:
            time: 标记位置（秒）
            name: 标记名称
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            from reapy import reascript_api as reaper
            reaper.AddProjectMarker(project, False, time, 0, name, -1)
            return f"成功在{time}秒处添加标记「{name}」。"
        except Exception as e:
            return f"添加标记失败：{e}"

    @mcp.tool()
    def reaper_add_region(start_time: float = 0.0, end_time: float = 0.0, name: str = "") -> str:
        """
        添加区域。
        
        Args:
            start_time: 区域开始时间（秒）
            end_time: 区域结束时间（秒）
            name: 区域名称
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        if end_time <= start_time:
            return "结束时间必须大于开始时间。"
        try:
            from reapy import reascript_api as reaper
            reaper.AddProjectMarker(project, True, start_time, end_time, name, -1)
            return f"成功添加区域「{name}」，范围{start_time}秒到{end_time}秒。"
        except Exception as e:
            return f"添加区域失败：{e}"

    @mcp.tool()
    def reaper_get_all_markers() -> list[dict]:
        """
        获取所有标记和区域。
        
        Returns:
            标记和区域列表
        """
        success, message, project = ensure_project_ready()
        if not success:
            return [{"error": message}]
        try:
            from reapy import reascript_api as reaper
            markers = []
            num_markers = reaper.CountProjectMarkers(project)
            for i in range(num_markers):
                retval, is_region, pos, rgn_end, name, markrgnindex = reaper.EnumProjectMarkers(i)
                markers.append({
                    "index": i,
                    "name": name,
                    "is_region": bool(is_region),
                    "position": pos,
                    "end_position": rgn_end if is_region else None
                })
            return markers
        except Exception as e:
            return [{"error": str(e)}]

    @mcp.tool()
    def reaper_delete_marker(index: int = 0) -> str:
        """
        删除指定标记或区域。
        
        Args:
            index: 标记/区域索引（从0开始）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            from reapy import reascript_api as reaper
            num_markers = reaper.CountProjectMarkers(project)
            if index < 0 or index >= num_markers:
                return f"标记索引无效：{index}，范围应为[0, {num_markers-1}]。"
            retval, is_region, pos, rgn_end, name, markrgnindex = reaper.EnumProjectMarkers(index)
            reaper.DeleteProjectMarker(project, markrgnindex, is_region)
            type_name = "区域" if is_region else "标记"
            return f"成功删除{type_name}「{name}」。"
        except Exception as e:
            return f"删除标记失败：{e}"

    @mcp.tool()
    def reaper_rename_marker(index: int = 0, new_name: str = "") -> str:
        """
        重命名标记或区域。
        
        Args:
            index: 标记/区域索引（从0开始）
            new_name: 新名称
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            from reapy import reascript_api as reaper
            num_markers = reaper.CountProjectMarkers(project)
            if index < 0 or index >= num_markers:
                return f"标记索引无效：{index}，范围应为[0, {num_markers-1}]。"
            retval, is_region, pos, rgn_end, old_name, markrgnindex = reaper.EnumProjectMarkers(index)
            reaper.SetProjectMarker(markrgnindex, is_region, pos, rgn_end, new_name, -1)
            type_name = "区域" if is_region else "标记"
            return f"成功将{type_name}「{old_name}」重命名为「{new_name}」。"
        except Exception as e:
            return f"重命名标记失败：{e}"

    @mcp.tool()
    def reaper_go_to_marker(index: int = 0) -> str:
        """
        跳转到指定标记位置。
        
        Args:
            index: 标记索引（从0开始）
        
        Returns:
            操作结果消息
        """
        success, message, project = ensure_project_ready()
        if not success:
            return message
        try:
            from reapy import reascript_api as reaper
            num_markers = reaper.CountProjectMarkers(project)
            if index < 0 or index >= num_markers:
                return f"标记索引无效：{index}，范围应为[0, {num_markers-1}]。"
            retval, is_region, pos, rgn_end, name, markrgnindex = reaper.EnumProjectMarkers(index)
            project.play_position = pos
            return f"已跳转到标记「{name}」位置：{pos}秒。"
        except Exception as e:
            return f"跳转标记失败：{e}"