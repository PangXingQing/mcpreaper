from .reaper_client import ensure_project_ready, get_track_by_name, update_arrange
from .error_handler import (
    ReaperError,
    ReaperConnectionError,
    TrackNotFoundError,
    ItemNotFoundError,
    FXNotFoundError,
    InvalidParameterError,
    ReaperFileNotFoundError,
    OperationFailedError,
    format_error_response,
    format_success_response,
    reaper_tool_error_handler,
    get_available_track_names
)

def get_track_item_count(track):
    """Get track item count using reascript directly (bypasses reapy cache)."""
    from reapy import reascript_api as reaper
    return reaper.CountTrackMediaItems(track)

def get_track_item(track, item_index):
    """Get track item using reascript directly (bypasses reapy cache)."""
    from reapy import reascript_api as reaper
    return reaper.GetTrackMediaItem(track, item_index)

__all__ = [
    "ensure_project_ready",
    "get_track_by_name",
    "update_arrange",
    "get_track_item_count",
    "get_track_item",
    "ReaperError",
    "ReaperConnectionError",
    "TrackNotFoundError",
    "ItemNotFoundError",
    "FXNotFoundError",
    "InvalidParameterError",
    "ReaperFileNotFoundError",
    "OperationFailedError",
    "format_error_response",
    "format_success_response",
    "reaper_tool_error_handler",
    "get_available_track_names"
]