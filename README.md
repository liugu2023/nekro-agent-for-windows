# Nekro-Agent Windows 管理系统

一个基于 PyQt6 的 Windows 跨平台虚拟机管理和 Docker 容器编排系统，用于在 Windows 上快速部署和管理 Nekro-Agent 服务。

## 功能特性

- 🚀 **一键部署** - 自动配置 WSL、Docker 和 Nekro-Agent 服务
- 🖥️ **图形化界面** - 简洁直观的 PyQt6 GUI 界面
- 📊 **日志分类** - 应用日志、NekroAgent 日志、NapCat 日志分类显示
- 🔄 **服务管理** - 启动、停止、更新、卸载服务
- 🌐 **浏览器集成** - 一键打开服务管理界面
- 💾 **系统托盘** - 最小化到托盘，后台运行
- ⚙️ **开机自启** - 可选的开机自动启动功能
- 🎯 **首次运行向导** - 引导用户完成初始配置

## 系统要求

- Windows 10/11 (64位)
- WSL 2
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

## 快速开始

### 方式一：使用可执行文件（推荐）

1. 下载最新的 Release 版本
2. 解压到任意目录
3. 运行 `NekroAgent-Setup-v1.0.0-beta.exe`
4. 按照首次运行向导完成配置

### 方式二：从源码运行

1. 克隆仓库
```bash
git clone https://github.com/liugu2023/nekro-agent-for-windows
cd nekro-agent-for-windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python main.py
```

启用调试模式：
```bash
python main.py --debug
```

## 部署模式

### 精简版 (lite)
- 仅包含 Nekro-Agent 核心服务
- 适合轻量级部署
- 需要外部 OneBot 实现

### 完整版 (napcat)
- 包含 Nekro-Agent + NapCat
- 一站式解决方案
- 内置 QQ 机器人支持

## 使用说明

### 首次运行

1. 程序会自动检测 WSL 环境
2. 如果未安装 WSL，会提示安装
3. 选择部署模式（精简版/完整版）
4. 等待自动部署完成
5. 记录显示的管理员密码和访问地址

### 日常使用

- **启动服务**：点击"一键部署项目"按钮
- **查看日志**：切换到"日志"页面，选择日志源
- **访问服务**：切换到"浏览器"页面，点击对应按钮
- **系统设置**：配置开机自启、数据目录等
- **更新服务**：点击"检查环境更新"拉取最新镜像

### 关闭程序

点击关闭按钮时可选择：
- **最小化到托盘** - 服务继续运行
- **停止服务并退出** - 完全关闭

## 目录结构

```
na_for_windows/
├── main.py                 # 程序入口
├── core/                   # 核心模块
│   ├── config_manager.py   # 配置管理
│   └── wsl_manager.py      # WSL 管理
├── ui/                     # 界面模块
│   ├── main_window.py      # 主窗口
│   ├── first_run_dialog.py # 首次运行向导
│   ├── widgets.py          # 自定义组件
│   └── styles.py           # 样式定义
├── assets/                 # 资源文件
│   ├── NekroAgent.png      # 应用图标
│   └── check.png           # 复选框图标
├── env                     # 环境变量模板
├── docker-compose_*.yml    # Docker 编排文件
└── build.spec              # 打包配置
```

## 配置文件

配置文件位于 `config.json`，包含以下内容：

```json
{
  "autostart": false,
  "deploy_mode": "napcat",
  "wsl_distro": "NekroAgent",
  "wsl_install_dir": "安装路径",
  "data_dir": "/root/nekro_agent_data",
  "deploy_info": {
    "port": "8021",
    "admin_password": "管理员密码",
    "onebot_token": "OneBot令牌",
    "napcat_port": "6099",
    "napcat_token": "NapCat令牌"
  }
}
```

## 开发

### 打包为可执行文件

```bash
# 运行打包脚本
build.bat

# 或手动打包
pyinstaller build.spec
```

打包后的文件位于 `dist/NekroAgent/`

### 调试模式

```bash
python main.py --debug
```

调试模式会显示详细的 DEBUG 级别日志。

## 常见问题

### WSL 安装失败
- 确保 Windows 版本支持 WSL 2
- 以管理员权限运行程序
- 检查网络连接

### Docker 镜像拉取慢
- 程序会自动尝试多个镜像源
- 可以手动配置 Docker 镜像加速

### 服务启动失败
- 查看日志页面的详细错误信息
- 确保端口 8021 和 6099 未被占用
- 检查 WSL 虚拟机状态

## 技术栈

- **GUI**: PyQt6
- **虚拟化**: WSL 2 + QEMU
- **容器**: Docker + Docker Compose
- **语言**: Python 3.8+

## 许可证

[添加许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [Nekro-Agent](https://github.com/KroMiose/nekro-agent) - 核心服务
- [NapCat](https://github.com/NapNeko/NapCatQQ) - QQ 机器人实现

