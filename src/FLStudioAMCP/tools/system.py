"""系统元工具 - 工具列表、搜索、通用调用器。"""

from __future__ import annotations

import json
import math
import platform
import time
from pathlib import Path

from typing import TYPE_CHECKING

from FLStudioAMCP.tools.registry import TOOL_REGISTRY, get_tool, search_tools

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_system_tools(mcp: FastMCP) -> None:
    """注册系统元工具到 MCP 服务器。"""
    from FLStudioAMCP.utils.connection import get_connection
    from FLStudioAMCP.utils.fl_trigger import get_trigger, trigger_fl_studio

    # =========================================================================
    # 钢琴卷帘辅助函数（热键 + 文件通信）
    # =========================================================================

    def _get_fl_scripts_dir() -> Path:
        """获取 FL Studio Piano Roll 脚本目录。"""
        system_name = platform.system()
        if system_name in ("Darwin", "Windows"):
            base = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Settings"
        else:
            base = Path.home() / ".fl-studio" / "Settings"
        scripts_dir = base / "Piano roll scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        return scripts_dir

    def _handle_piano_roll(tool_id: str, params: dict) -> dict:
        """处理钢琴卷帘工具：写入请求文件 → 激活 FL Studio 窗口 → 发送 Ctrl+Alt+Y 热键触发 pyscript。"""
        trigger = get_trigger()
        if not trigger.is_supported:
            return {"error": f"钢琴卷帘工具不支持当前平台: {platform.system()}"}

        scripts_dir = _get_fl_scripts_dir()
        request_file = scripts_dir / "mcp_request.json"
        response_file = scripts_dir / "mcp_response.json"

        action_map = {
            "piano_roll.add_notes": "add_notes",
            "piano_roll.add_chord": "add_chord",
            "piano_roll.delete_notes": "delete_notes",
            "piano_roll.clear": "clear",
        }
        action = action_map.get(tool_id)
        if not action:
            return {"error": f"未知的钢琴卷帘操作: {tool_id}"}

        request_data = {"action": action}
        if action == "add_notes":
            request_data["notes"] = params.get("notes", [])
        elif action == "add_chord":
            request_data["notes"] = params.get("notes", [])
            request_data["time"] = params.get("time", 0)
            request_data["duration"] = params.get("duration", 1.0)
        elif action == "delete_notes":
            request_data["notes"] = params.get("notes", [])

        try:
            if response_file.exists():
                response_file.unlink()
            request_file.write_text(json.dumps([request_data]), encoding="utf-8")
        except Exception as e:
            return {"error": f"写入请求文件失败: {e}"}

        # 触发 FL Studio（先激活窗口，再发送热键）
        success = trigger_fl_studio(delay=3.0)
        if not success:
            return {"error": "触发 FL Studio 热键失败"}

        for _ in range(20):
            if response_file.exists():
                try:
                    data = json.loads(response_file.read_text(encoding="utf-8"))
                    try:
                        request_file.write_text("[]", encoding="utf-8")
                    except Exception:
                        pass
                    return data
                except Exception as e:
                    return {"error": f"读取响应文件失败: {e}"}
            time.sleep(0.5)

        return {"error": "等待钢琴卷帘脚本响应超时"}

    # =========================================================================
    # 元工具
    # =========================================================================

    @mcp.tool()
    def fl_list_tools(
        category: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """分页获取所有可用 MCP 工具列表。

        返回工具列表，包含每个工具的 id、名称、描述、分类和参数信息。
        支持按分类过滤和分页。

        Args:
            category: 按分类过滤（留空返回全部）。可选: transport/mixer/channels/plugins/stepseq/patterns/playlist/arrangement/general/ui/piano_roll/system
            page: 页码（从 1 开始）
            page_size: 每页条数（默认 50）
        """
        # 过滤
        if category:
            tools = [t for t in TOOL_REGISTRY.values() if t["category"] == category]
        else:
            tools = list(TOOL_REGISTRY.values())

        total = len(tools)
        total_pages = max(1, math.ceil(total / page_size))
        page = max(1, min(page, total_pages))

        start = (page - 1) * page_size
        end = start + page_size
        page_tools = tools[start:end]

        # 为每个工具条目添加 calling_convention，不修改原始 TOOL_REGISTRY
        tools_with_convention = [
            {**tool, "calling_convention": "params"}
            for tool in page_tools
        ]

        return {
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "tools": tools_with_convention,
        }

    @mcp.tool()
    def fl_search_tools(query: str, category: str = "") -> dict:
        """按名称和描述搜索 MCP 工具。

        在工具注册表中搜索名称或描述包含关键词的工具。
        返回匹配的工具列表，每个工具包含 id、名称、描述、分类和参数信息。

        Args:
            query: 搜索关键词（中文或英文）
            category: 可选，限定搜索范围到指定分类
        """
        results = search_tools(query, category if category else None)
        # 为每个工具条目添加 calling_convention，不修改原始 TOOL_REGISTRY
        results_with_convention = [
            {**tool, "calling_convention": "params"}
            for tool in results
        ]
        return {
            "query": query,
            "total": len(results_with_convention),
            "tools": results_with_convention,
        }

    @mcp.tool()
    def fl_call_tool(tool_id: str, params: dict = {}) -> dict:
        """通过工具 ID 调用 MCP 工具。

        根据工具 ID 查找注册表，构造参数并执行对应的 FL Studio 操作。
        钢琴卷帘工具使用热键+文件通信（Ctrl+Alt+Y 触发 pyscript）。

        Args:
            tool_id: 工具唯一标识（如 "transport.play"、"mixer.set_track_volume"）
            params: 工具参数，key 为参数名，value 为参数值
        """
        tool = get_tool(tool_id)
        if not tool:
            return {"error": f"未知工具: {tool_id}"}

        # 钢琴卷帘工具：热键 + 文件通信
        if tool_id.startswith("piano_roll."):
            return _handle_piano_roll(tool_id, params)

        # MIDI 工具
        action = tool.get("action")
        if not action:
            return {"error": f"工具 {tool_id} 没有定义 action 或 handler"}

        # 通用 API 调用（flapi.call）需要特殊构造参数
        if action == "flapi.call":
            module = tool.get("module", "")
            function = tool.get("function", "")
            if not module or not function:
                return {"error": f"工具 {tool_id} 缺少 module 或 function 字段"}
            # 按 args 顺序将用户参数映射为位置参数列表
            arg_names = tool.get("args", [])
            arg_values = [params.get(name) for name in arg_names]
            action_params = {
                "module": module,
                "function": function,
                "args": arg_values,
            }
        else:
            # 参数映射：通过 param_map 将文档参数名翻译为 FL Studio API 实际 key
            # 由于 registry.py 中 params key 已与 param_map 映射目标一致，
            # 调用者按文档参数名传参即可，无需关心内部映射关系
            param_map = tool.get("param_map", {})
            action_params = {}
            for mcp_key, value in params.items():
                action_key = param_map.get(mcp_key, mcp_key)
                action_params[action_key] = value

        # 发送命令
        conn = get_connection()
        try:
            conn.ensure_connected()
        except RuntimeError as e:
            return {"error": f"未连接到 FL Studio: {e}"}

        try:
            result = conn.send_command(action, action_params, timeout=5.0)
        except Exception as e:
            return {"error": str(e)}

        return result

    @mcp.tool()
    def fl_get_tool_schema(category: str = "") -> dict:
        """批量获取工具 schema 摘要，减少逐个读取 MCP 工具描述的开销。

        返回所有工具的摘要信息，每个工具包含 tool_id、name、description、
        category、params、calling_convention。支持按分类过滤。

        Args:
            category: 按分类过滤（留空返回全部）
        """
        if category:
            tools = [t for t in TOOL_REGISTRY.values() if t["category"] == category]
        else:
            tools = list(TOOL_REGISTRY.values())

        summaries = []
        for tool in tools:
            summaries.append({
                "tool_id": tool["id"],
                "name": tool["name"],
                "description": tool["description"],
                "category": tool["category"],
                "params": tool.get("params", {}),
                "calling_convention": "params",
            })

        return {
            "total": len(summaries),
            "tools": summaries,
        }

    # =========================================================================
    # 调试工具
    # =========================================================================

    @mcp.tool()
    def fl_debug() -> dict:
        """FL Studio MCP 动态调试工具。

        直接调用 FL Studio 测试各种通信路径，返回结果用于诊断。
        不用任何硬编码路径，纯动态调用。
        """
        conn = get_connection()
        try:
            conn.ensure_connected()
        except RuntimeError as e:
            return {"connected": False, "error": str(e)}

        results = {"connected": True, "port": conn._midi._port_name, "tests": {}}

        # 测试直接 MIDI action
        r = conn.send_command("transport.getStatus", {}, timeout=2.0)
        results["tests"]["midi_direct"] = {
            "ok": r.get("success", False) and "error" not in r,
            "response": r,
        }

        # 测试 flapi.call - patterns
        r = conn.send_command("flapi.call", {
            "module": "patterns", "function": "patternCount", "args": []
        }, timeout=2.0)
        results["tests"]["flapi_patterns"] = {
            "ok": r.get("success", False) and "error" not in r,
            "response": r,
        }

        # 测试 flapi.call - playlist
        r = conn.send_command("flapi.call", {
            "module": "playlist", "function": "trackCount", "args": []
        }, timeout=2.0)
        results["tests"]["flapi_playlist"] = {
            "ok": r.get("success", False) and "error" not in r,
            "response": r,
        }

        # 测试 flapi.call - transport
        r = conn.send_command("flapi.call", {
            "module": "transport", "function": "getLoopMode", "args": []
        }, timeout=2.0)
        results["tests"]["flapi_transport"] = {
            "ok": r.get("success", False) and "error" not in r,
            "response": r,
        }

        # 测试 channels 直接 action
        r = conn.send_command("channels.getCount", {"global_count": True}, timeout=2.0)
        results["tests"]["channels_get_count"] = {
            "ok": r.get("success", False) and "error" not in r,
            "response": r,
        }

        # 汇总
        all_ok = all(t["ok"] for t in results["tests"].values())
        results["all_pass"] = all_ok

        return results

    # =========================================================================
    # 保留：获取 FL Studio 原生 API
    # =========================================================================

    @mcp.tool()
    def fl_get_all_interfaces() -> dict:
        """获取 FL Studio 原生 Python API 所有接口。

        通过 dir() 反射枚举 channels、mixer、plugins、transport、general、
        arrangement、patterns、playlist、ui、device 等模块的公开函数和属性。

        需要在 FL Studio 运行且 MIDI 控制器已连接时使用。
        """
        conn = get_connection()
        try:
            conn.ensure_connected()
        except RuntimeError as e:
            return {"error": f"未连接到 FL Studio: {e}"}

        result = conn.send_command("system.listFLStudioAPI", {}, timeout=5.0)

        if "error" in result:
            return {"error": result["error"]}

        return {
            "fl_studio_version": result.get("fl_studio_version", "unknown"),
            "modules": result.get("modules", {}),
        }