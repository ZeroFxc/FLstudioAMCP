# FLStudioAMCP / FL Studio Aggregated MCP

AMCP = Aggregated MCP（聚合 MCP），通过字典注册表 + 元工具架构将 200+ 工具聚合为 6 个 MCP 接口。

AMCP = Aggregated MCP, consolidating 200+ tools into 6 MCP interfaces via dictionary registry + meta-tool architecture.

## 架构 / Architecture

采用**元工具架构**，仅暴露 6 个 MCP 工具。 / Uses **meta-tool architecture**, only 6 MCP tools exposed.

| 工具 / Tool | 功能 / Function |
|------|------|
| `fl_connect` | 连接 FL Studio / Connect |
| `fl_connection_status` | 连接状态 / Status |
| `fl_get_all_interfaces` | FL Studio 原生 API / Native API |
| `fl_list_tools` | 分页工具列表（200+） / Paginated list |
| `fl_search_tools` | 搜索工具 / Search |
| `fl_call_tool` | 通用调用器 / Universal caller |

## 安装 / Install

```bash
uv pip install -e .
```

## 部署 / Deploy

双击 `deploy.bat` 或在 FL Studio 中 `Options` → `MIDI Settings` → 选择控制器。

Double-click `deploy.bat` or in FL Studio: `Options` → `MIDI Settings` → select controller.

## 使用 / Usage

AI 调用流程 / AI call flow:
1. `fl_search_tools(query="play")` → 搜索工具 / Find tool
2. `fl_call_tool(tool_id="transport.play")` → 执行 / Execute

## 工具分类 / Tool Categories

| 分类 / Category | 功能 / Features |
|------|------|
| **transport** | 播放/停止/录音/速度 / Play/Stop/Record/Tempo |
| **mixer** | 混音/音量/声像/静音/独奏/EQ / Mixer/Volume/Pan/Mute/Solo/EQ |
| **channels** | 通道/音量/步进音序器 / Channel/Volume/Step Sequencer |
| **plugins** | 插件参数/预设 / Plugin Params/Presets |
| **patterns** | 模式切换/克隆/命名 / Pattern Switch/Clone/Name |
| **playlist** | 播放列表/Live模式 / Playlist/Live Mode |
| **arrangement** | 标记/选区/时间 / Markers/Selection/Time |
| **general** | 项目信息/撤销/节拍器 / Project/Undo/Metronome |
| **ui** | 窗口/缩放/浏览器 / Window/Zoom/Browser |
| **piano_roll** | 音符/和弦 / Notes/Chords |
| **stepseq** | 步进音序器 / Step Sequencer |