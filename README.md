# Nekro-Agent for Windows

基于 PyQt6 的 Windows 图形化部署工具，让你在 Windows 上一键部署和管理 [Nekro-Agent](https://github.com/KroMiose/nekro-agent)。

## 下载

前往 [Releases](https://github.com/NekroAI/nekro-agent-for-windows/releases) 下载最新版 `NekroAgent-Setup.exe`，以管理员身份运行即可。

## 系统要求

- Windows 10/11 64位
- WSL2（未安装时向导可引导自动安装）

## 功能

- **一键部署**：首次运行向导引导完成环境检测、WSL 发行版创建、Docker 安装、服务部署全流程
- **两种部署模式**：完整版（含 NapCat）和精简版
- **内置浏览器**：直接访问 Nekro-Agent 和 NapCat 管理界面
- **日志中心**：应用日志、Nekro-Agent 日志、NapCat 日志分离展示
- **服务管理**：启动、停止、更新、卸载一键操作
- **端口配置**：可在设置页自定义 Nekro-Agent 和 NapCat 端口

## 开发运行

```bash
pip install -r requirements.txt
python main.py
```

调试模式（显示 debug 日志）：

```bash
python main.py --debug
```

内置 WebView 出现闪烁或渲染异常时：

```bash
python main.py --disable-webview-gpu
```

## 问题反馈

请在 [Issues](https://github.com/NekroAI/nekro-agent-for-windows/issues/new) 提交问题报告。
