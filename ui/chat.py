"""
LLM 对话引擎。

提供与 OpenAI 兼容 API 的对话能力，包括：
- 流式对话
- 上下文管理
- 预设系统提示词
- REAPER 工程上下文注入
"""
import json
import time
from typing import Optional, Dict, Any, List, Generator, AsyncGenerator

import httpx


# ============================================================
# 系统提示词模板
# ============================================================

SYSTEM_PROMPTS = {
    "reaper_expert": """你是一个 REAPER DAW 资深专家助手。

你能帮助用户：
1. **REAPER 操作指导**：轨道管理、路由、混音、效果器链、自动化
2. **MIDI 编曲**：GM 音色选择、和弦进行、配器建议
3. **音频处理**：EQ、压缩、混响、降噪等音频参数建议
4. **工程优化**：CPU 负载分析、路由优化、Template 建议
5. **脚本操作**：通过 MCP 工具直接操作 REAPER 工程

回答风格：专业、简洁、可操作。给出具体步骤，而非泛泛而谈。
使用中文回答。""",

    "midi_composer": """你是一个 MIDI 音乐编曲助手。

你的专长：
1. 分析乐曲需求，推荐合适的 GM 音色搭配
2. 设计多声部编曲方案（旋律、和声、低音、打击乐）
3. 推荐和弦进行和音阶
4. 调整力度、弯音、CC 控制等 MIDI 表现力参数
5. 传统/民族/影视配乐风格建议

回答风格：创作导向，给出具体的音色编号和编曲建议。使用中文。""",

    "mix_engineer": """你是一个音频混音工程師助手。

你能帮助用户：
1. 推荐 EQ 设置（频率、Q 值、增益）
2. 动态处理建议（压缩比、阈值、Attack/Release）
3. 空间效果（混响类型、延迟时间、房间大小）
4. 立体声场规划和声相设置
5. 母带处理（限制器、多段压缩、响度标准）

回答时使用具体的参数值。使用中文。""",

    "audio_analyzer": """你是一个音频分析助手。

你能帮助：
1. 分析音频文件的电平、频谱特性
2. 检测静音、削波、噪声问题
3. 建议降噪和修复方案
4. 匹配参考音频的响度和频谱特征
5. 音频素材库管理和检索建议

回答风格：技术分析导向，给出具体数据和建议。使用中文。""",
}

ASSISTANT_MODE_NAMES = {
    "reaper_expert": "REAPER 专家",
    "midi_composer": "MIDI 作曲",
    "mix_engineer": "混音工程",
    "audio_analyzer": "音频分析",
}


# ============================================================
# 对话管理器
# ============================================================

class ConversationManager:
    """管理 LLM 对话上下文的类。"""

    def __init__(self, max_history: int = 20):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.system_prompt: str = SYSTEM_PROMPTS["reaper_expert"]

    def set_mode(self, mode: str):
        """切换助手模式。"""
        if mode in SYSTEM_PROMPTS:
            self.system_prompt = SYSTEM_PROMPTS[mode]
        self.history = []  # 切换模式时清空历史

    def add_user_message(self, message: str):
        """添加用户消息到历史。"""
        self.history.append({"role": "user", "content": message})
        self._trim_history()

    def add_assistant_message(self, message: str):
        """添加助手回复到历史。"""
        self.history.append({"role": "assistant", "content": message})
        self._trim_history()

    def get_messages(self, custom_system: Optional[str] = None) -> List[Dict[str, str]]:
        """获取完整消息列表（包含系统提示词）。"""
        system = custom_system or self.system_prompt
        return [{"role": "system", "content": system}] + self.history

    def _trim_history(self):
        """保持历史在最大长度内。"""
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2):]

    def clear(self):
        """清空对话历史（保留系统提示词）。"""
        self.history = []

    def inject_context(self, context_text: str):
        """注入 REAPER 工程上下文。"""
        context_msg = f"[当前 REAPER 工程状态]\n{context_text}\n请基于以上工程信息回答用户问题。"
        self.history.insert(0, {"role": "system", "content": context_msg})


# ============================================================
# 工程上下文构建
# ============================================================

def build_project_context() -> Optional[str]:
    """构建当前 REAPER 工程的上下文信息。"""
    try:
        from utils.project_reporter import generate_project_report
        report = generate_project_report()
        if not report["success"]:
            return None

        context_parts = []
        context_parts.append(f"BPM: {report.get('bpm', '?')}")
        context_parts.append(f"拍号: {report.get('time_signature', '?')}")
        context_parts.append(f"轨道数: {report.get('track_count', 0)}")
        context_parts.append(f"效果器总数: {report.get('total_fx', 0)}")
        context_parts.append(f"MIDI 音符总数: {report.get('total_midi_notes', 0)}")
        context_parts.append(f"标记数: {report.get('total_markers', 0)}")

        # 轨道列表
        tracks = report.get("tracks_detail", [])
        if tracks:
            context_parts.append("\n轨道清单:")
            for t in tracks[:15]:
                context_parts.append(
                    f"  - {t['name']}: {t['items']} items, "
                    f"{t['midi_notes']} notes, "
                    f"{t['fx']} FX, "
                    f"{'[MUTE]' if t.get('mute') else ''}"
                    f"{'[SOLO]' if t.get('solo') else ''}"
                )

        return "\n".join(context_parts)
    except Exception:
        return None


# ============================================================
# LLM 对话接口
# ============================================================

class LLMClient:
    """OpenAI 兼容 API 的 LLM 对话客户端。"""

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.conversation = ConversationManager()

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """同步对话。

        Returns:
            {"success": bool, "reply": str, "usage": {...}}
        """
        if not self.api_key:
            return {"success": False, "error": "API Key 未配置"}

        self.conversation.add_user_message(message)
        messages = self.conversation.get_messages(custom_system=system_prompt)

        try:
            start = time.perf_counter()
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API 错误 ({response.status_code}): {response.text[:300]}",
                }

            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            self.conversation.add_assistant_message(reply)

            return {
                "success": True,
                "reply": reply,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            }

        except httpx.TimeoutException:
            return {"success": False, "error": "请求超时（60s）"}
        except Exception as e:
            return {"success": False, "error": f"对话失败: {e}"}

    async def chat_async(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """异步对话。"""
        if not self.api_key:
            return {"success": False, "error": "API Key 未配置"}

        self.conversation.add_user_message(message)
        messages = self.conversation.get_messages(custom_system=system_prompt)

        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API 错误 ({response.status_code})",
                }

            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            self.conversation.add_assistant_message(reply)

            return {
                "success": True,
                "reply": reply,
                "usage": data.get("usage", {}),
                "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            }

        except Exception as e:
            return {"success": False, "error": f"对话失败: {e}"}

    def set_mode(self, mode: str):
        """切换助手模式。"""
        self.conversation.set_mode(mode)

    def clear_history(self):
        """清空对话历史。"""
        self.conversation.clear()

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史（不含系统提示词）。"""
        return self.conversation.history


# ============================================================
# 全局客户端实例
# ============================================================

_instance: Optional[LLMClient] = None


def get_llm_client(
    api_key: str = "",
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o",
) -> LLMClient:
    """获取或创建 LLM 客户端实例（单例）。"""
    global _instance
    if _instance is None:
        _instance = LLMClient(api_key=api_key, api_base=api_base, model=model)
    return _instance


def reset_llm_client():
    """重置 LLM 客户端实例。"""
    global _instance
    _instance = None
