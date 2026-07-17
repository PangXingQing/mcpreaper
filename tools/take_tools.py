"""
Take（录音片段）管理工具。

提供多 Take 管理、Take 切换、Take 删除和复制等功能。
"""
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    get_track_by_name,
    reaper_tool_error_handler,
    TrackNotFoundError,
    ItemNotFoundError,
    InvalidParameterError,
    OperationFailedError,
    format_success_response,
    get_available_track_names,
)


def register_take_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_track_takes(track_name: str = "") -> dict:
        """
        获取指定轨道上所有媒体项的 Take 列表。

        每个媒体项可以包含多个 Take（如多次录音的片段），
        此工具列出每个 Item 的所有 Take 及其信息。

        Args:
            track_name: 轨道名称

        Returns:
            Take 列表，包含每个 Take 的名称、起始位置、长度、是否激活
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接REAPER", message)

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            result = []
            item_count = reaper.CountTrackMediaItems(track)

            for item_idx in range(item_count):
                item = reaper.GetTrackMediaItem(track, item_idx)
                item_pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
                item_len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
                take_count = reaper.GetMediaItemNumTakes(item)
                takes_info = []

                for take_idx in range(take_count):
                    take = reaper.GetMediaItemTake(item, take_idx)
                    take_name = reaper.GetTakeName(take, "", 256)[1] if take else ""
                    is_active = take_idx == reaper.GetMediaItemInfo_Value(item, "I_CURTAKE")

                    # 尝试获取 MIDI 信息
                    midi_notes = 0
                    try:
                        _, _, nn, _, _ = reaper.MIDI_CountEvts(take, 0, 0, 0)
                        midi_notes = nn
                    except Exception:
                        pass

                    takes_info.append({
                        "index": take_idx,
                        "name": take_name,
                        "active": is_active,
                        "midi_note_count": midi_notes,
                    })

                result.append({
                    "item_index": item_idx,
                    "position": round(item_pos, 3),
                    "length": round(item_len, 3),
                    "take_count": take_count,
                    "takes": takes_info,
                })

            return format_success_response(data={
                "track_name": track_name,
                "item_count": item_count,
                "items": result,
            })

        except Exception as e:
            raise OperationFailedError("获取 Take 列表", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_switch_active_take(track_name: str = "", item_index: int = 0, take_index: int = 0) -> dict:
        """
        切换媒体项的激活 Take。

        如果一个 Item 有多个 Take（如多次录音），可以切换激活哪一个。

        Args:
            track_name: 轨道名称
            item_index: 媒体项索引（从 0 开始）
            take_index: 要激活的 Take 索引（从 0 开始）

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")
        if item_index < 0:
            raise InvalidParameterError("item_index", item_index, "索引必须 >= 0")

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            item = reaper.GetTrackMediaItem(track, item_index)
            if not item:
                raise ItemNotFoundError(track_name, item_index, 0)
            take_count = reaper.GetMediaItemNumTakes(item)
            if take_index < 0 or take_index >= take_count:
                raise InvalidParameterError(
                    "take_index", take_index,
                    f"有效范围：[0, {take_count - 1}]"
                )
            reaper.SetActiveTake(item, take_index)  # type: ignore
            reaper.UpdateArrange()

            take_name = reaper.GetTakeName(
                reaper.GetMediaItemTake(item, take_index), "", 256
            )[1]

            return format_success_response(
                message=f"已将 Take[{take_index}]「{take_name}」设为激活。"
            )
        except (TrackNotFoundError, ItemNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("切换 Take", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_delete_take(track_name: str = "", item_index: int = 0, take_index: int = 0) -> dict:
        """
        删除媒体项的指定 Take。

        Args:
            track_name: 轨道名称
            item_index: 媒体项索引
            take_index: 要删除的 Take 索引

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            item = reaper.GetTrackMediaItem(track, item_index)
            if not item:
                raise ItemNotFoundError(track_name, item_index, 0)
            take = reaper.GetMediaItemTake(item, take_index)
            if not take:
                raise InvalidParameterError(
                    "take_index", take_index,
                    f"该 Item 没有 Take[{take_index}]"
                )
            reaper.DeleteTake(take)  # type: ignore
            reaper.UpdateArrange()
            return format_success_response(
                message=f"已删除 Take[{take_index}]。"
            )
        except (TrackNotFoundError, ItemNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("删除 Take", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_crop_to_active_take(track_name: str = "", item_index: int = 0) -> dict:
        """
        裁剪到激活 Take：删除所有非激活 Take，只保留当前激活的。

        Args:
            track_name: 轨道名称
            item_index: 媒体项索引

        Returns:
            操作结果
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            item = reaper.GetTrackMediaItem(track, item_index)
            if not item:
                raise ItemNotFoundError(track_name, item_index, 0)
            reaper.CropToActiveTake(item)  # type: ignore
            reaper.UpdateArrange()
            return format_success_response(
                message=f"已裁剪 Item[{item_index}] 到激活 Take。"
            )
        except (TrackNotFoundError, ItemNotFoundError):
            raise
        except Exception as e:
            raise OperationFailedError("裁剪 Take", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_explode_takes_to_tracks(
        track_name: str = "", item_index: int = 0,
    ) -> dict:
        """
        将媒体项的所有 Take 展开到独立轨道。

        每个 Take 会创建一条新轨道，并放置对应的 Take 内容。
        原始 Item 中的 Take 会被清空。

        Args:
            track_name: 轨道名称
            item_index: 媒体项索引

        Returns:
            新创建的轨道名称列表
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            item = reaper.GetTrackMediaItem(track, item_index)
            if not item:
                raise ItemNotFoundError(track_name, item_index, 0)

            take_count = reaper.GetMediaItemNumTakes(item)
            if take_count <= 1:
                raise OperationFailedError(
                    "展开 Take", "该 Item 只有一个 Take，无需展开"
                )

            new_track_names = []
            item_pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
            item_len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")

            for take_idx in range(take_count):
                take = reaper.GetMediaItemTake(item, take_idx)
                take_name = reaper.GetTakeName(take, "", 256)[1]

                # 创建新轨道
                new_track_idx = reaper.InsertTrackAtIndex(
                    reaper.CountTracks(0), False
                )
                new_track = reaper.GetTrack(0, new_track_idx)
                reaper.GetSetMediaTrackInfo_String(
                    new_track, "P_NAME", take_name, True
                )

                # 复制 Take 到新轨道
                reaper.SetActiveTake(item, take_idx)
                new_item = reaper.AddMediaItemToTrack(new_track)
                reaper.SetMediaItemInfo_Value(new_item, "D_POSITION", item_pos)
                reaper.SetMediaItemInfo_Value(new_item, "D_LENGTH", item_len)

                # 复制源文件
                source = reaper.GetMediaItemTake_Source(take)
                reaper.SetMediaItemTake_Source(
                    reaper.GetMediaItemTake(new_item, 0), source
                )

                new_track_names.append(take_name)

            reaper.UpdateArrange()
            return format_success_response(
                message=f"已将 {take_count} 个 Take 展开为独立轨道",
                data={"new_track_names": new_track_names},
            )
        except (TrackNotFoundError, ItemNotFoundError):
            raise
        except Exception as e:
            raise OperationFailedError("展开 Take", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_get_take_info(
        track_name: str = "", item_index: int = 0, take_index: int = 0,
    ) -> dict:
        """
        获取指定 Take 的详细信息。

        Args:
            track_name: 轨道名称
            item_index: 媒体项索引
            take_index: Take 索引

        Returns:
            Take 详细信息（名称、源文件、MIDI 统计等）
        """
        if not track_name:
            raise InvalidParameterError("track_name", track_name, "请提供有效的轨道名称")

        track = get_track_by_name(track_name)
        if track is None:
            available_tracks = get_available_track_names()
            raise TrackNotFoundError(track_name, available_tracks)

        try:
            from reapy import reascript_api as reaper
            item = reaper.GetTrackMediaItem(track, item_index)
            if not item:
                raise ItemNotFoundError(track_name, item_index, 0)
            take = reaper.GetMediaItemTake(item, take_index)
            if not take:
                raise InvalidParameterError(
                    "take_index", take_index,
                    "该 Item 没有此索引的 Take"
                )

            take_name = reaper.GetTakeName(take, "", 256)[1]
            is_midi = reaper.TakeIsMIDI(take)
            is_active = take_index == reaper.GetMediaItemInfo_Value(item, "I_CURTAKE")

            take_info = {
                "name": take_name,
                "is_midi": bool(is_midi),
                "is_active": is_active,
                "item_index": item_index,
                "take_index": take_index,
            }

            if is_midi:
                _, _, nn, ncc, ntxt = reaper.MIDI_CountEvts(take, 0, 0, 0)
                take_info.update({
                    "midi_note_count": nn,
                    "midi_cc_count": ncc,
                    "midi_text_count": ntxt,
                })

            return format_success_response(data=take_info)
        except (TrackNotFoundError, ItemNotFoundError, InvalidParameterError):
            raise
        except Exception as e:
            raise OperationFailedError("获取 Take 信息", str(e))
