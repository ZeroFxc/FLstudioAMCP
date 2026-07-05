

from __future__ import annotations

from fastmcp import FastMCP

from FLStudioAMCP.tools import (
    register_system_tools,
)
from FLStudioAMCP.utils.connection import get_connection, reset_connection

# Create the MCP server
mcp = FastMCP(
    name="FLStudioAMCP",
    instructions="""
FL Studio MCP Server - Control FL Studio from AI assistants.

This server uses a meta-tool architecture:
1. fl_list_tools - 分页获取所有可用工具列表
2. fl_search_tools - 按名称/描述搜索工具
3. fl_call_tool - 通过 tool_id 调用具体工具

典型的 AI 编曲流程：
1. 调用 fl_search_tools(query="播放") 搜索需要的工具
2. 从返回结果中获取 tool_id 和参数说明
3. 调用 fl_call_tool(tool_id="transport.play", params={}) 执行操作

工具分类：
- transport: 播放/停止/录音/位置/循环/速度
- mixer: 混音轨道/音量/声像/静音/独奏/路由/EQ
- channels: 通道选择/音量/声像/静音/独奏/步进音序器
- plugins: 插件参数/预设/名称
- patterns: 模式切换/克隆/颜色/命名/长度/分组
- playlist: 播放列表轨道/静音/独奏/颜色/Live模式
- arrangement: 标记/选区/时间定位
- general: 项目信息/撤销/节拍器
- ui: 窗口导航/缩放/浏览器
- piano_roll: 音符添加/删除/和弦（通过文件通信）
- stepseq: 步进音序器
- device: MIDI设备/端口/反馈/链接/CC处理
- launchMapPages: 启动映射页面/映射项管理

重要限制：
1. 不能加载新的 VST/AU 插件，只能控制已有插件
2. 不能通过 API 创建新 Pattern
3. fl_call_tool 需要先通过 fl_search_tools 或 fl_list_tools 查找 tool_id
""",
)


# Register connection status resource
@mcp.resource("fl://status")
def get_fl_status() -> str:
    """Get FL Studio connection status."""
    conn = get_connection()
    if conn.is_connected:
        return "Connected to FL Studio via MIDI"
    else:
        return f"Not connected: {conn.connection_error}"


@mcp.resource("fl://project")
def get_project_info() -> dict:
    """Get current FL Studio project information."""
    conn = get_connection()

    if not conn.is_connected:
        return {"error": conn.connection_error}

    try:
        result = conn.send_command("transport.getStatus")
        if not result.get("success", False) and "error" in result:
            return {"error": result["error"]}

        return {
            "is_playing": result.get("is_playing", False),
            "is_recording": result.get("is_recording", False),
            "position": result.get("position", ""),
            "loop_mode": result.get("loop_mode", "pattern"),
        }
    except Exception as e:
        return {"error": str(e)}


# Connection management tools
@mcp.tool()
def fl_connect() -> str:
    """Connect or reconnect to FL Studio via MIDI.

    Use this tool to:
    - Check if FL Studio is connected
    - Retry connection after starting FL Studio
    - Reconnect if the connection was lost

    Returns the connection status.
    """
    # Reset connection state to force a fresh connection attempt
    reset_connection()

    conn = get_connection()
    try:
        conn.ensure_connected()
    except RuntimeError as e:
        return f"Connection failed: {e}"
    return "Successfully connected to FL Studio via MIDI!"


@mcp.tool()
def fl_connection_status() -> dict:
    """Get the current FL Studio connection status.

    Returns information about whether FL Studio is connected
    and any error messages if not.
    """
    conn = get_connection()
    # Eagerly attempt a connection so the reported status reflects actual
    # reachability rather than the lazily-initialized flag.
    try:
        conn.ensure_connected()
    except RuntimeError:
        pass
    status = conn.get_status()
    return {
        "connected": status.get("connected", False),
        "port_name": status.get("port_name"),
        "available_ports": status.get("available_ports", []),
        "error": status.get("error"),
    }


# Register all tools
register_system_tools(mcp)


def main():
    """Run the FL Studio MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
