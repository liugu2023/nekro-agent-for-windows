# Project Memory

## 项目概述

Nekro-Agent 环境管理系统 - 一个 Windows 跨平台虚拟机管理和 Docker 容器编排系统，使用 Python + PyQt6 构建。

## 技术栈

- Python 3 + PyQt6 GUI
- QEMU 虚拟化
- Docker 容器编排
- Alpine Linux 轻量级虚拟机

## 重要开发规范

### Windows 兼容性

- **此项目将在 Windows 下测试运行**
- 所有文件必须使用 Windows 换行符 (CRLF, `\r\n`)
- 路径分隔符注意使用 `os.path.join()` 或 `pathlib.Path` 保证跨平台兼容
- 文件编码统一使用 UTF-8 with BOM 或 UTF-8
- 注意 Windows 文件名大小写不敏感
