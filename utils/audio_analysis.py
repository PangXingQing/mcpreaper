"""
音频分析与处理工具。

提供音频文件的波形分析、响度检测、静音检测、频谱分析等功能。
作为 MCP 工具的后端支持。
"""
import os
import struct
import math
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict


# ============================================================
# 音频文件基本信息
# ============================================================

def get_wav_info(filepath: str) -> Dict[str, Any]:
    """解析 WAV 文件头，返回音频基本信息。

    Args:
        filepath: WAV 文件路径

    Returns:
        包含采样率、位深、声道数、时长等信息的字典
    """
    if not os.path.exists(filepath):
        return {"error": f"文件不存在: {filepath}"}

    try:
        with open(filepath, "rb") as f:
            # RIFF header
            riff = f.read(4)
            if riff != b"RIFF":
                return {"error": "不是有效的 WAV 文件（缺少 RIFF 头）"}
            _ = f.read(4)  # file size
            wave = f.read(4)
            if wave != b"WAVE":
                return {"error": "不是有效的 WAV 文件（缺少 WAVE 标识）"}

            # Parse chunks
            sample_rate = 44100
            bits_per_sample = 16
            num_channels = 1
            data_size = 0
            byte_rate = 0

            while True:
                chunk_id = f.read(4)
                if len(chunk_id) < 4:
                    break
                chunk_size_bytes = f.read(4)
                if len(chunk_size_bytes) < 4:
                    break
                chunk_size = struct.unpack("<I", chunk_size_bytes)[0]

                if chunk_id == b"fmt ":
                    fmt_data = f.read(chunk_size)
                    if len(fmt_data) >= 16:
                        audio_format = struct.unpack("<H", fmt_data[0:2])[0]
                        num_channels = struct.unpack("<H", fmt_data[2:4])[0]
                        sample_rate = struct.unpack("<I", fmt_data[4:8])[0]
                        byte_rate = struct.unpack("<I", fmt_data[8:12])[0]
                        bits_per_sample = struct.unpack("<H", fmt_data[14:16])[0]
                elif chunk_id == b"data":
                    data_size = chunk_size
                    break  # data 通常是最后一个关心的 chunk
                else:
                    f.seek(chunk_size, 1)

            if sample_rate == 0:
                return {"error": "无效的采样率"}

            duration = data_size / byte_rate if byte_rate > 0 else 0
            return {
                "filepath": filepath,
                "filename": os.path.basename(filepath),
                "size_bytes": os.path.getsize(filepath),
                "sample_rate": sample_rate,
                "bits_per_sample": bits_per_sample,
                "num_channels": num_channels,
                "duration_seconds": round(duration, 3),
                "data_size_bytes": data_size,
                "byte_rate": byte_rate,
            }
    except Exception as e:
        return {"error": f"解析 WAV 文件失败: {e}"}


def get_audio_format_name(bits: int) -> str:
    """获取音频格式的可读名称。"""
    formats = {8: "8-bit PCM", 16: "16-bit PCM", 24: "24-bit PCM", 32: "32-bit float"}
    return formats.get(bits, f"{bits}-bit")


# ============================================================
# 响度分析
# ============================================================

def calculate_rms(samples: List[float]) -> float:
    """计算 RMS (Root Mean Square) 响度。"""
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def calculate_peak(samples: List[float]) -> float:
    """计算峰值电平。"""
    if not samples:
        return 0.0
    return max(abs(s) for s in samples)


def calculate_lufs_momentary(samples: List[float], sample_rate: int = 44100) -> float:
    """估算瞬时 LUFS 值（简化实现，基于 RMS）。

    完整的 LUFS 需要 ITU-R BS.1770 算法，这里用 RMS 近似。
    """
    rms = calculate_rms(samples)
    if rms == 0:
        return -120.0
    return 20 * math.log10(rms)


def analyze_audio_levels(
    filepath: str,
    window_ms: float = 400.0,
    max_samples: int = 10000000,
) -> Dict[str, Any]:
    """分析音频文件的电平信息。

    Args:
        filepath: WAV 文件路径
        window_ms: 分析窗口大小（毫秒）
        max_samples: 最大分析采样数（防止大文件超时）

    Returns:
        峰值、RMS、近似 LUFS 电平等
    """
    info = get_wav_info(filepath)
    if "error" in info:
        return info

    try:
        sample_rate = info["sample_rate"]
        num_channels = info["num_channels"]
        bits = info["bits_per_sample"]

        # 计算窗口采样数
        window_samples = int(sample_rate * window_ms / 1000)
        if window_samples < 1:
            window_samples = 1

        # 读取 PCM 数据
        with open(filepath, "rb") as f:
            # 跳过头部到 data chunk
            f.seek(0)
            riff = f.read(4)
            _ = f.read(4)
            wave = f.read(4)

            while True:
                chunk_id = f.read(4)
                if len(chunk_id) < 4:
                    break
                chunk_size = struct.unpack("<I", f.read(4))[0]
                if chunk_id == b"data":
                    break
                f.seek(chunk_size, 1)
            else:
                return {"error": "未找到 data chunk"}

            data = f.read(min(chunk_size, max_samples * num_channels * (bits // 8)))

        # 解析采样
        samples_all = []
        if bits == 16:
            fmt = f"<{len(data) // 2}h"
            raw = struct.unpack(fmt, data)
            samples_all = [s / 32768.0 for s in raw]
        elif bits == 24:
            step = 3
            for i in range(0, len(data) - step + 1, step):
                chunk = data[i : i + step]
                val = int.from_bytes(chunk, "little", signed=True)
                samples_all.append(val / 8388608.0)
        elif bits == 32:
            fmt = f"<{len(data) // 4}f"
            samples_all = list(struct.unpack(fmt, data))
        else:
            return {"error": f"不支持的位深: {bits}"}

        if not samples_all:
            return {"error": "无法读取采样数据"}

        # 分离声道（取第一声道进行分析）
        ch1_samples = samples_all[::num_channels]

        # 逐窗口计算
        window_peaks = []
        window_rms = []
        for i in range(0, len(ch1_samples), window_samples):
            segment = ch1_samples[i : i + window_samples]
            if segment:
                window_peaks.append(calculate_peak(segment))
                window_rms.append(calculate_rms(segment))

        overall_peak = max(window_peaks) if window_peaks else 0.0
        overall_rms = calculate_rms(ch1_samples)
        peak_db = 20 * math.log10(overall_peak) if overall_peak > 0 else -120.0
        rms_db = 20 * math.log10(overall_rms) if overall_rms > 0 else -120.0

        return {
            "filepath": filepath,
            "sample_rate": sample_rate,
            "num_channels": num_channels,
            "bits_per_sample": bits,
            "peak_linear": round(overall_peak, 6),
            "peak_db": round(peak_db, 1),
            "rms_linear": round(overall_rms, 6),
            "rms_db": round(rms_db, 1),
            "crest_factor_db": round(peak_db - rms_db, 1),
            "analyzed_windows": len(window_peaks),
            "window_ms": window_ms,
        }
    except Exception as e:
        return {"error": f"电平分析失败: {e}"}


# ============================================================
# 静音检测
# ============================================================

def detect_silence(
    filepath: str,
    threshold_db: float = -40.0,
    min_silence_ms: float = 500.0,
    window_ms: float = 100.0,
) -> Dict[str, Any]:
    """检测音频文件中的静音段落。

    Args:
        filepath: WAV 文件路径
        threshold_db: 静音阈值（dB），低于此值视为静音
        min_silence_ms: 最短静音持续时间
        window_ms: 分析窗口大小

    Returns:
        静音段落列表和时间轴统计
    """
    info = get_wav_info(filepath)
    if "error" in info:
        return info

    try:
        sample_rate = info["sample_rate"]
        num_channels = info["num_channels"]
        bits = info["bits_per_sample"]

        threshold_linear = 10 ** (threshold_db / 20.0)
        window_samples = int(sample_rate * window_ms / 1000)
        min_silence_windows = int(min_silence_ms / window_ms)

        # 读取数据
        with open(filepath, "rb") as f:
            f.seek(0)
            _ = f.read(12)  # RIFF header
            while True:
                chunk_id = f.read(4)
                chunk_size = struct.unpack("<I", f.read(4))[0]
                if chunk_id == b"data":
                    break
                f.seek(chunk_size, 1)

            data = f.read(chunk_size)

        if bits == 16:
            fmt = f"<{len(data) // 2}h"
            raw = struct.unpack(fmt, data)
            samples_all = [s / 32768.0 for s in raw]
        elif bits == 24:
            samples_all = []
            for i in range(0, len(data) - 2, 3):
                val = int.from_bytes(data[i:i+3], "little", signed=True)
                samples_all.append(val / 8388608.0)
        else:
            return {"error": f"不支持的位深: {bits}"}

        ch1 = samples_all[::num_channels]

        # 逐窗口判断
        silence_regions = []
        in_silence = False
        silence_start_window = 0
        total_silence_windows = 0

        for i in range(0, len(ch1), window_samples):
            segment = ch1[i:i + window_samples]
            if not segment:
                continue
            rms = calculate_rms(segment)
            is_silence = rms < threshold_linear

            if is_silence and not in_silence:
                silence_start_window = i
                in_silence = True
            elif not is_silence and in_silence:
                duration_windows = (i - silence_start_window) // window_samples
                if duration_windows >= min_silence_windows:
                    start_sec = silence_start_window / sample_rate
                    end_sec = i / sample_rate
                    silence_regions.append({
                        "start_seconds": round(start_sec, 3),
                        "end_seconds": round(end_sec, 3),
                        "duration_seconds": round(end_sec - start_sec, 3),
                    })
                total_silence_windows += duration_windows
                in_silence = False

        # 处理文件末尾的静音
        if in_silence:
            end_sample = len(ch1)
            duration_windows = (end_sample - silence_start_window) // window_samples
            if duration_windows >= min_silence_windows:
                start_sec = silence_start_window / sample_rate
                end_sec = end_sample / sample_rate
                silence_regions.append({
                    "start_seconds": round(start_sec, 3),
                    "end_seconds": round(end_sec, 3),
                    "duration_seconds": round(end_sec - start_sec, 3),
                })

        total_duration = len(ch1) / sample_rate
        total_silence_sec = sum(r["duration_seconds"] for r in silence_regions)

        return {
            "filepath": filepath,
            "threshold_db": threshold_db,
            "min_silence_ms": min_silence_ms,
            "total_duration_seconds": round(total_duration, 3),
            "total_silence_seconds": round(total_silence_sec, 3),
            "silence_percentage": round(total_silence_sec / total_duration * 100, 1) if total_duration > 0 else 0,
            "silence_regions": silence_regions,
            "num_regions": len(silence_regions),
        }
    except Exception as e:
        return {"error": f"静音检测失败: {e}"}


# ============================================================
# 批量分析
# ============================================================

def batch_analyze_directory(
    directory: str,
    extensions: Tuple[str, ...] = (".wav", ".mp3", ".flac", ".ogg"),
) -> List[Dict[str, Any]]:
    """批量分析目录下所有音频文件。"""
    results = []
    if not os.path.isdir(directory):
        return results

    for root, _, files in os.walk(directory):
        for filename in sorted(files):
            if filename.lower().endswith(extensions):
                filepath = os.path.join(root, filename)
                if filename.lower().endswith(".wav"):
                    info = get_wav_info(filepath)
                else:
                    info = {
                        "filepath": filepath,
                        "filename": filename,
                        "size_bytes": os.path.getsize(filepath),
                    }
                results.append(info)

    return results


def get_audio_library_stats(directory: str) -> Dict[str, Any]:
    """获取音频素材库的统计信息。"""
    files = batch_analyze_directory(directory)

    total_size = sum(f.get("size_bytes", 0) for f in files)
    total_duration = sum(f.get("duration_seconds", 0) for f in files)

    # 按格式统计
    format_counts = {}
    for f in files:
        ext = os.path.splitext(f.get("filename", ""))[1].lower()
        format_counts[ext] = format_counts.get(ext, 0) + 1

    # 按声道统计
    channel_counts = OrderedDict()
    for f in files:
        ch = f.get("num_channels", 0)
        label = f"{ch} ch" if ch else "unknown"
        channel_counts[label] = channel_counts.get(label, 0) + 1

    return {
        "directory": directory,
        "total_files": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_duration_seconds": round(total_duration, 1),
        "format_distribution": format_counts,
        "channel_distribution": dict(channel_counts),
        "files": files[:100],  # 最多返回 100 个文件
    }
