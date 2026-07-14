import os
import wave
import struct
import math
import random
from mcp.server.fastmcp import FastMCP
from utils import (
    ensure_project_ready,
    update_arrange,
    reaper_tool_error_handler,
    InvalidParameterError,
    OperationFailedError,
    format_success_response
)

def register_generate_tools(mcp: FastMCP):

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_sine_wave(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.5) -> dict:
        """
        生成正弦波音频文件并导入到Reaper。
        
        Args:
            frequency: 频率（Hz，有效值范围：[20, 20000]）
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if frequency <= 0:
            raise InvalidParameterError("frequency", frequency, "频率必须大于0")
        
        if frequency < 20 or frequency > 20000:
            raise InvalidParameterError("frequency", frequency, "有效值范围：[20, 20000]Hz")
        
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            filename = f"sine_{int(frequency)}Hz_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                for i in range(num_samples):
                    t = i / sample_rate
                    sample = amplitude * math.sin(2 * math.pi * frequency * t)
                    wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入正弦波：{frequency}Hz，{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成正弦波", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_square_wave(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.5) -> dict:
        """
        生成方波音频文件并导入到Reaper。
        
        Args:
            frequency: 频率（Hz，有效值范围：[20, 20000]）
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if frequency <= 0:
            raise InvalidParameterError("frequency", frequency, "频率必须大于0")
        
        if frequency < 20 or frequency > 20000:
            raise InvalidParameterError("frequency", frequency, "有效值范围：[20, 20000]Hz")
        
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            filename = f"square_{int(frequency)}Hz_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                period = sample_rate / frequency
                for i in range(num_samples):
                    if (i % period) < (period / 2):
                        sample = amplitude
                    else:
                        sample = -amplitude
                    wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入方波：{frequency}Hz，{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成方波", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_triangle_wave(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.5) -> dict:
        """
        生成三角波音频文件并导入到Reaper。
        
        Args:
            frequency: 频率（Hz，有效值范围：[20, 20000]）
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if frequency <= 0:
            raise InvalidParameterError("frequency", frequency, "频率必须大于0")
        
        if frequency < 20 or frequency > 20000:
            raise InvalidParameterError("frequency", frequency, "有效值范围：[20, 20000]Hz")
        
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            filename = f"triangle_{int(frequency)}Hz_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                period = sample_rate / frequency
                for i in range(num_samples):
                    t = i % period
                    if t < period / 2:
                        sample = (4 * amplitude / period) * t - amplitude
                    else:
                        sample = -(4 * amplitude / period) * (t - period / 2) + amplitude
                    wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入三角波：{frequency}Hz，{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成三角波", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_sawtooth_wave(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.5) -> dict:
        """
        生成锯齿波音频文件并导入到Reaper。
        
        Args:
            frequency: 频率（Hz，有效值范围：[20, 20000]）
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if frequency <= 0:
            raise InvalidParameterError("frequency", frequency, "频率必须大于0")
        
        if frequency < 20 or frequency > 20000:
            raise InvalidParameterError("frequency", frequency, "有效值范围：[20, 20000]Hz")
        
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            filename = f"sawtooth_{int(frequency)}Hz_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                period = sample_rate / frequency
                for i in range(num_samples):
                    t = i % period
                    sample = (2 * amplitude / period) * t - amplitude
                    wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入锯齿波：{frequency}Hz，{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成锯齿波", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_noise(duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.5, noise_type: str = "white") -> dict:
        """
        生成噪音音频文件并导入到Reaper。
        
        Args:
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
            noise_type: 噪音类型（有效值：white, pink, brown）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        valid_noise_types = ["white", "pink", "brown"]
        if noise_type not in valid_noise_types:
            raise InvalidParameterError("noise_type", noise_type, f"有效值：{valid_noise_types}")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            filename = f"{noise_type}_noise_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                if noise_type == "white":
                    for _ in range(num_samples):
                        sample = amplitude * (2 * random.random() - 1)
                        wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
                elif noise_type == "pink":
                    b0, b1, b2, b3, b4, b5, b6 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                    for _ in range(num_samples):
                        white = random.random() * 2 - 1
                        b0 = 0.99886 * b0 + white * 0.0555179
                        b1 = 0.99332 * b1 + white * 0.0750759
                        b2 = 0.96900 * b2 + white * 0.1538520
                        b3 = 0.86650 * b3 + white * 0.3104856
                        b4 = 0.55000 * b4 + white * 0.5329522
                        b5 = -0.7616 * b5 - white * 0.0168980
                        sample = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362
                        sample *= 0.11
                        wav_file.writeframes(struct.pack('<h', int(sample * amplitude * 32767)))
                elif noise_type == "brown":
                    last_out = 0.0
                    for _ in range(num_samples):
                        white = random.random() * 2 - 1
                        sample = (last_out + 0.02 * white) / 1.02
                        last_out = sample
                        sample *= 3.5
                        wav_file.writeframes(struct.pack('<h', int(sample * amplitude * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入{noise_type}噪音：{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成噪音", str(e))

    @mcp.tool()
    @reaper_tool_error_handler
    def reaper_generate_chord(chord_notes: list = None, duration: float = 1.0, sample_rate: int = 44100, amplitude: float = 0.3) -> dict:
        """
        生成和弦音频文件并导入到Reaper。
        
        Args:
            chord_notes: 和弦音符频率列表（如[261.63, 329.63, 392.0]表示C大三和弦），至少包含1个频率
            duration: 时长（秒，有效值范围：> 0）
            sample_rate: 采样率（有效值：8000, 11025, 22050, 44100, 48000, 96000）
            amplitude: 振幅（有效值范围：(0, 1]）
        
        Returns:
            操作结果字典，包含success、message字段
        """
        if not chord_notes or len(chord_notes) == 0:
            raise InvalidParameterError("chord_notes", chord_notes, "请提供至少一个音符频率")
        
        for freq in chord_notes:
            if freq <= 0 or freq < 20 or freq > 20000:
                raise InvalidParameterError(
                    "chord_notes", chord_notes,
                    f"每个频率必须在[20, 20000]Hz范围内，当前值：{freq}"
                )
        
        if duration <= 0:
            raise InvalidParameterError("duration", duration, "时长必须大于0")
        
        valid_sample_rates = [8000, 11025, 22050, 44100, 48000, 96000]
        if sample_rate not in valid_sample_rates:
            raise InvalidParameterError("sample_rate", sample_rate, f"有效值：{valid_sample_rates}")
        
        if amplitude <= 0 or amplitude > 1:
            raise InvalidParameterError("amplitude", amplitude, "有效值范围：(0, 1]")
        
        success, message, project = ensure_project_ready()
        if not success:
            raise OperationFailedError("连接Reaper", message)
        
        try:
            from reapy import reascript_api as reaper
            
            wav_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "WAV")
            if not os.path.exists(wav_dir):
                os.makedirs(wav_dir)
            
            chord_name = "_".join(str(int(n)) for n in chord_notes)
            filename = f"chord_{chord_name}_{duration}s.wav"
            file_path = os.path.join(wav_dir, filename)
            
            num_samples = int(duration * sample_rate)
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                for i in range(num_samples):
                    t = i / sample_rate
                    sample = 0
                    for freq in chord_notes:
                        sample += math.sin(2 * math.pi * freq * t)
                    sample /= len(chord_notes)
                    sample *= amplitude
                    wav_file.writeframes(struct.pack('<h', int(sample * 32767)))
            
            track_count = reaper.CountTracks(0)
            if track_count == 0:
                reaper.Main_OnCommand(40701, 0)
            
            track = reaper.GetTrack(0, 0)
            reaper.InsertMedia(file_path, 0)
            
            update_arrange()
            return format_success_response(message=f"成功生成并导入和弦：{chord_notes}Hz，{duration}秒，采样率{sample_rate}Hz。")
        except Exception as e:
            raise OperationFailedError("生成和弦", str(e))