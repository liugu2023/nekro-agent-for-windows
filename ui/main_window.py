import os
import sys
import webbrowser

def get_resource_path(relative_path):
    """获取资源文件路径，兼容打包后"""
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QLineEdit,
                             QFrame, QGridLayout, QComboBox, QTextEdit,
                             QCheckBox, QFileDialog, QMessageBox, QDialog,
                             QApplication, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QCloseEvent

from ui.styles import STYLESHEET
from ui.widgets import ActionButton
from core.config_manager import ConfigManager
from core.wsl_manager import WSLManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nekro-Agent 管理")
        self.resize(1050, 750)
        self.setStyleSheet(STYLESHEET)

        # 初始化后端
        self.config = ConfigManager()
        self.wsl = WSLManager(config=self.config)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 侧边栏 ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 25)
        sidebar_layout.setSpacing(10)

        # Logo
        logo_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_label.setScaledContents(True)

        icon_path = get_resource_path(os.path.join("assets", "NekroAgent.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logo_label.setPixmap(QPixmap(icon_path))

        logo_text = QLabel("NekroAgent")
        logo_text.setStyleSheet("font-size: 18px; font-weight: bold; color: #24292f; margin-left: 5px;")
        logo_layout.addWidget(logo_label); logo_layout.addWidget(logo_text); logo_layout.addStretch()
        sidebar_layout.addLayout(logo_layout)
        sidebar_layout.addSpacing(30)

        # 导航按钮
        self.btn_home = self.create_sidebar_btn("🏠", "项目概览", 0)
        self.btn_browser = self.create_sidebar_btn("🌐", "应用浏览器", 1)
        self.btn_logs = self.create_sidebar_btn("📝", "运行日志", 2)
        self.btn_files = self.create_sidebar_btn("📁", "文件管理", 3)
        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_browser)
        sidebar_layout.addWidget(self.btn_logs)
        sidebar_layout.addWidget(self.btn_files)
        sidebar_layout.addStretch()
        self.btn_settings = self.create_sidebar_btn("⚙️", "系统设置", 4)
        sidebar_layout.addWidget(self.btn_settings)

        main_layout.addWidget(self.sidebar)

        # --- 2. 右侧 Stack 布局 ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.init_home_page()
        self.init_browser_page()
        self.init_logs_page()
        self.init_files_page()
        self.init_settings_page()

        self.switch_tab(0)

        # 绑定后端信号
        self.wsl.log_received.connect(self.append_log)
        self.wsl.status_changed.connect(self.update_status_ui)
        self.wsl.deploy_info_ready.connect(self._show_credentials_dialog)
        self.setFocus()

        # 系统托盘
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = get_resource_path(os.path.join("assets", "NekroAgent.png"))
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 首次运行检测 / 自动部署
        QTimer.singleShot(200, self._on_startup)

    def _on_startup(self):
        """启动时检测是否需要首次运行向导"""
        if self.config.get("first_run") or not self.config.get("deploy_mode"):
            self._show_first_run_dialog()
        else:
            self.start_deploy()

    def _show_first_run_dialog(self):
        """显示首次运行向导"""
        from ui.first_run_dialog import FirstRunDialog
        dialog = FirstRunDialog(self.wsl, self.config, parent=self)
        dialog.deploy_requested.connect(self._on_deploy_mode_selected)
        dialog.exec()

    def _on_deploy_mode_selected(self, mode):
        """首次运行向导完成后启动部署"""
        self._is_first_deploy = True
        if hasattr(self, 'mode_combo'):
            self.mode_combo.setCurrentText("完整版 (napcat)" if mode == "napcat" else "精简版 (lite)")
        self.start_deploy()

    def create_sidebar_btn(self, icon, text, index):
        btn = QPushButton(f"  {icon}   {text}")
        btn.setObjectName("SidebarBtn")
        btn.setCheckable(True)
        btn.setFixedHeight(48)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        btns = [self.btn_home, self.btn_browser, self.btn_logs, self.btn_files, self.btn_settings]
        for i, btn in enumerate(btns):
            btn.setChecked(i == index)

    def append_log(self, msg, level="info"):
        # debug 级别只在 --debug 模式下显示
        if level == "debug" and not getattr(self, 'debug_mode', False):
            return

        color = {"error": "#f85149", "warning": "#d29922", "warn": "#d29922", "debug": "#8b949e", "vm": "#8b949e"}.get(level, "#7ee787")
        # 统一 warn 为 warning
        if level == "warn":
            level = "warning"

        # vm 级别不显示标签前缀
        if level == "vm":
            formatted = f"<span style='color:{color};'>{msg}</span>"
        else:
            formatted = f"<span style='color:{color};'>[{level.upper()}]</span> {msg}"

        # 根据日志类型分类
        if level == "vm":
            # 容器日志，判断是 nekro 还是 napcat
            if "napcat" in msg.lower():
                self.log_viewer_napcat.append(formatted)
            else:
                self.log_viewer_nekro.append(formatted)
        else:
            # 应用日志
            self.log_viewer_app.append(formatted)

        # 同时输出到 stdout
        try:
            print(f"[{level.upper()}] {msg}")
        except Exception:
            pass

    def _switch_log_source(self, index):
        """切换日志源"""
        self.log_viewer_app.setVisible(index == 0)
        self.log_viewer_nekro.setVisible(index == 1)
        self.log_viewer_napcat.setVisible(index == 2)

    # --- 各页面具体实现 ---

    def init_home_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(25)

        title_box = QVBoxLayout()
        lbl_title = QLabel("Nekro-Agent 环境管理")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold;")
        self.lbl_status = QLabel("● 当前状态: 未就绪")
        self.lbl_status.setStyleSheet("font-size: 14px; color: #cf222e; margin-top: 5px;")
        title_box.addWidget(lbl_title); title_box.addWidget(self.lbl_status)
        layout.addLayout(title_box); layout.addSpacing(10)

        grid = QGridLayout(); grid.setSpacing(20)

        self.btn_env_check = ActionButton("🔍", "环境检查", "检测 WSL2 和 Docker 环境")
        self.btn_deploy_action = ActionButton("🚀", "一键部署项目", "自动配置 Docker 服务", "DeployBtn")
        self.btn_update_action = ActionButton("🔄", "检查环境更新", "更新镜像并重启")
        self.btn_uninstall_action = ActionButton("🗑️", "卸载清除环境", "删除所有容器和数据", "UninstallBtn")
        self.btn_web_home = ActionButton("🏠", "访问项目主页", "获取文档与支持")
        self.btn_show_creds = ActionButton("🔑", "查看部署凭据", "查看密码和访问地址")

        grid.addWidget(self.btn_env_check, 0, 0)
        grid.addWidget(self.btn_deploy_action, 0, 1)
        grid.addWidget(self.btn_update_action, 1, 0)
        grid.addWidget(self.btn_uninstall_action, 1, 1)
        grid.addWidget(self.btn_show_creds, 2, 0)
        grid.addWidget(self.btn_web_home, 2, 1)

        # 绑定按钮事件
        self.btn_deploy_action.clicked.connect(self.start_deploy)
        self.btn_env_check.clicked.connect(self._show_first_run_dialog)
        self.btn_show_creds.clicked.connect(self._show_saved_credentials)
        self.btn_update_action.clicked.connect(self._update_services)
        self.btn_uninstall_action.clicked.connect(self._uninstall_environment)
        self.btn_web_home.clicked.connect(lambda: __import__('webbrowser').open("https://github.com/KroMiose/nekro-agent"))

        layout.addLayout(grid); layout.addStretch()
        self.stack.addWidget(page)

    def start_deploy(self):
        """启动部署流程"""
        if self.wsl.is_running:
            QMessageBox.information(self, "提示", "服务已在运行中")
            return

        deploy_mode = self.config.get("deploy_mode")
        if not deploy_mode:
            QMessageBox.critical(self, "错误", "未选择部署版本，请先运行环境检查")
            return

        # 切换到日志页查看进度
        self.switch_tab(2)
        self.log_viewer_app.clear()
        self.log_viewer_app.append(f"<span style='color:#7ee787;'>[INFO]</span> 开始部署服务 (模式: {deploy_mode})...")

        # 启动服务
        self.wsl.start_services(deploy_mode)

    def update_status_ui(self, status):
        prev_status = self.lbl_status.text()
        self.lbl_status.setText(f"● 当前状态: {status}")
        if status == "运行中":
            self.lbl_status.setStyleSheet("font-size: 14px; color: #2da44e; margin-top: 5px;")
            # 禁用一键部署按钮
            self.btn_deploy_action.setEnabled(False)
            self.btn_deploy_action.setCursor(Qt.CursorShape.ForbiddenCursor)
            # 覆盖按钮样式使其变灰
            self.btn_deploy_action.setStyleSheet("""
                QPushButton {
                    background: #e8e9eb !important;
                    border: 1px solid #d0d7de !important;
                    color: #8b949e !important;
                }
            """)
            # 仅在状态首次变为运行中时打开浏览器
            if "运行中" not in prev_status:
                # 只在首次部署时弹窗提示收藏
                if hasattr(self, '_is_first_deploy') and self._is_first_deploy:
                    deploy_mode = self.config.get("deploy_mode")
                    msg = "服务已启动！\n\n建议在浏览器中收藏以下地址：\n\n"
                    msg += "• NekroAgent: http://localhost:8021"
                    if deploy_mode == "napcat":
                        msg += "\n• NapCat: http://localhost:6099"
                    QMessageBox.information(self, "服务已启动", msg)
                    self._is_first_deploy = False
                webbrowser.open("http://localhost:8021")
                if self.config.get("deploy_mode") == "napcat":
                    self.btn_napcat.setVisible(True)
        else:
            self.lbl_status.setStyleSheet("font-size: 14px; color: #cf222e; margin-top: 5px;")

    def _on_browser_ready(self, ok):
        """页面加载完成后再切换到浏览器页签"""
        try:
            self.webview.loadFinished.disconnect(self._on_browser_ready)
        except TypeError:
            pass
        if ok:
            self.switch_tab(1)

    def init_browser_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(20)

        title = QLabel("服务访问")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        desc = QLabel("点击下方按钮在系统默认浏览器中打开服务页面，建议收藏以便后续访问。")
        desc.setStyleSheet("font-size: 14px; color: #57606a; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # NekroAgent 按钮
        btn_na = QPushButton("🌐 打开 NekroAgent 管理界面")
        btn_na.setFixedHeight(50)
        btn_na.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_na.setStyleSheet("""
            QPushButton {
                background-color: #0969da; color: white; border: none;
                border-radius: 8px; font-size: 15px; font-weight: 600;
            }
            QPushButton:hover { background-color: #0860ca; }
        """)
        btn_na.clicked.connect(lambda: webbrowser.open("http://localhost:8021"))
        layout.addWidget(btn_na)

        # NapCat 按钮
        self.btn_napcat = QPushButton("🤖 打开 NapCat 管理界面")
        self.btn_napcat.setFixedHeight(50)
        self.btn_napcat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_napcat.setStyleSheet("""
            QPushButton {
                background-color: #1f883d; color: white; border: none;
                border-radius: 8px; font-size: 15px; font-weight: 600;
            }
            QPushButton:hover { background-color: #1a7f37; }
        """)
        self.btn_napcat.clicked.connect(lambda: webbrowser.open("http://localhost:6099"))
        deploy_mode = self.config.get("deploy_mode")
        self.btn_napcat.setVisible(deploy_mode == "napcat")
        layout.addWidget(self.btn_napcat)

        layout.addStretch(); self.stack.addWidget(page)

    def init_logs_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(25, 25, 25, 25); layout.setSpacing(15)
        top = QHBoxLayout()
        self.log_source = QComboBox()
        self.log_source.addItems(["应用日志", "NekroAgent 日志", "NapCat 日志"])
        self.log_source.currentIndexChanged.connect(self._switch_log_source)
        top.addWidget(QLabel("日志源:")); top.addWidget(self.log_source); top.addStretch()
        layout.addLayout(top)

        # 三个日志查看器
        self.log_viewer_app = QTextEdit(); self.log_viewer_app.setObjectName("LogViewer"); self.log_viewer_app.setReadOnly(True)
        self.log_viewer_nekro = QTextEdit(); self.log_viewer_nekro.setObjectName("LogViewer"); self.log_viewer_nekro.setReadOnly(True)
        self.log_viewer_napcat = QTextEdit(); self.log_viewer_napcat.setObjectName("LogViewer"); self.log_viewer_napcat.setReadOnly(True)

        layout.addWidget(self.log_viewer_app)
        layout.addWidget(self.log_viewer_nekro)
        layout.addWidget(self.log_viewer_napcat)

        self.log_viewer_nekro.hide()
        self.log_viewer_napcat.hide()

        self.stack.addWidget(page)

    def init_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(30)
        lbl_title = QLabel("系统设置"); lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #24292f;")
        layout.addWidget(lbl_title)

        self.check_auto = QCheckBox("开机自动启动 Nekro-Agent 管理系统")
        self.check_auto.setChecked(self.config.get("autostart"))
        self.check_auto.stateChanged.connect(lambda s: self.config.set("autostart", s == 2))
        check_icon = get_resource_path(os.path.join("assets", "check.png"))
        self.check_auto.setStyleSheet(f"""
            QCheckBox::indicator:checked {{
                background-color: #0969da;
                border-color: #0969da;
                image: url({check_icon.replace(os.sep, '/')});
            }}
        """)
        layout.addWidget(self.check_auto)

        # 部署版本显示
        lbl_mode = QLabel("部署版本:"); layout.addWidget(lbl_mode)
        current_mode = self.config.get("deploy_mode")
        mode_text = "完整版 (napcat)" if current_mode == "napcat" else "精简版 (lite)"
        self.mode_display = QLineEdit(mode_text)
        self.mode_display.setReadOnly(True)
        layout.addWidget(self.mode_display)

        # WSL 安装目录
        lbl_wsldir = QLabel("WSL 安装目录:"); layout.addWidget(lbl_wsldir)
        self.wsldir_edit = QLineEdit(self.config.get("wsl_install_dir") or "未配置")
        self.wsldir_edit.setReadOnly(True)
        layout.addWidget(self.wsldir_edit)

        # 数据目录
        lbl_datadir = QLabel("数据目录 (WSL 内路径):"); layout.addWidget(lbl_datadir)
        datadir_box = QHBoxLayout()
        self.datadir_edit = QLineEdit(self.config.get("data_dir") or "/root/nekro_agent_data")
        self.datadir_edit.setPlaceholderText("/root/nekro_agent_data")
        self.datadir_edit.editingFinished.connect(
            lambda: self.config.set("data_dir", self.datadir_edit.text().strip())
        )
        datadir_box.addWidget(self.datadir_edit)

        btn_open_datadir = QPushButton("打开目录")
        btn_open_datadir.setFixedHeight(32)
        btn_open_datadir.setFixedWidth(80)
        btn_open_datadir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_datadir.clicked.connect(self._open_datadir_in_explorer)
        datadir_box.addWidget(btn_open_datadir)

        layout.addLayout(datadir_box)

        datadir_hint = QLabel()
        datadir_hint.setStyleSheet("font-size: 12px; color: #8b949e;")
        datadir_hint.setWordWrap(True)
        datadir_hint.setText("在 Windows 中可通过 \\\\wsl$\\NekroAgent\\... 访问此目录")
        layout.addWidget(datadir_hint)

        layout.addStretch(); self.stack.addWidget(page)

    def _on_mode_changed(self, index):
        mode = "napcat" if index == 1 else "lite"
        self.config.set("deploy_mode", mode)

    def _open_datadir_in_explorer(self):
        """在 Windows 资源管理器中打开 WSL 数据目录"""
        data_dir = self.datadir_edit.text().strip() or "/root/nekro_agent_data"
        # 将 WSL 路径转为 \\wsl$\NekroAgent\... 格式
        win_path = f"\\\\wsl$\\NekroAgent{data_dir}"
        try:
            os.startfile(win_path)
        except Exception as e:
            QMessageBox.warning(self, "提示", f"无法打开目录，请确认服务已启动且目录已创建。\n\n路径: {win_path}\n错误: {e}")

    def _update_services(self):
        """拉取最新镜像并重启服务"""
        if not self.wsl.is_running:
            QMessageBox.information(self, "提示", "服务未运行，请先部署启动。")
            return

        reply = QMessageBox.question(
            self, "确认更新",
            "将拉取最新镜像并重启所有容器，期间服务会短暂中断。\n确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.switch_tab(2)
        self.log_viewer_app.append("<span style='color:#7ee787;'>[INFO]</span> 开始更新服务...")
        self.wsl.update_services()

    def _uninstall_environment(self):
        """卸载清除环境：停止服务、删除容器和 WSL 发行版"""
        reply = QMessageBox.warning(
            self, "确认卸载",
            "此操作将：\n"
            "  1. 停止所有运行中的容器\n"
            "  2. 删除所有容器和镜像数据\n"
            "  3. 删除 NekroAgent WSL 发行版\n\n"
            "此操作不可撤销！确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.switch_tab(2)
        self.log_viewer_app.append("<span style='color:#7ee787;'>[INFO]</span> 开始卸载环境...")
        self.wsl.uninstall_environment()

    def init_files_page(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(20)

        lbl_title = QLabel("文件管理")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #24292f;")
        layout.addWidget(lbl_title)

        desc = QLabel("通过 Windows 资源管理器访问 WSL 内的 NekroAgent 文件目录。")
        desc.setStyleSheet("font-size: 14px; color: #57606a;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 快捷目录按钮
        dirs_info = [
            ("📂  数据目录", "存储数据库、配置、日志等运行数据", "data_dir", "/root/nekro_agent_data"),
            ("📂  部署目录", "存储 docker-compose 和 .env 配置文件", None, "/root/nekro_agent"),
        ]
        for icon_text, hint, config_key, default_path in dirs_info:
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background: white; border: 1px solid #d0d7de; border-radius: 8px; padding: 15px; }"
            )
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 10)

            info_layout = QVBoxLayout()
            lbl_name = QLabel(icon_text)
            lbl_name.setStyleSheet("font-size: 15px; font-weight: 600; color: #24292f;")
            lbl_hint = QLabel(hint)
            lbl_hint.setStyleSheet("font-size: 12px; color: #8b949e;")
            info_layout.addWidget(lbl_name)
            info_layout.addWidget(lbl_hint)
            card_layout.addLayout(info_layout)

            card_layout.addStretch()

            btn_open = QPushButton("在资源管理器中打开")
            btn_open.setFixedHeight(34)
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet(
                "QPushButton { background-color: #f3f4f6; color: #24292f; border: 1px solid #d0d7de; "
                "border-radius: 6px; font-size: 13px; padding: 0 15px; }"
                "QPushButton:hover { background-color: #e8e9eb; }"
            )
            wsl_path = default_path
            if config_key:
                wsl_path = self.config.get(config_key) or default_path
            btn_open.clicked.connect(lambda checked, p=wsl_path: self._open_wsl_path(p))
            card_layout.addWidget(btn_open)

            layout.addWidget(card)

        layout.addStretch()
        self.stack.addWidget(page)

    def _open_wsl_path(self, wsl_path):
        """在 Windows 资源管理器中打开 WSL 路径"""
        win_path = f"\\\\wsl$\\NekroAgent{wsl_path}"
        try:
            os.startfile(win_path)
        except Exception as e:
            QMessageBox.warning(self, "提示", f"无法打开目录，请确认服务已启动且目录已创建。\n\n路径: {win_path}\n错误: {e}")

    def init_empty_page(self, title):
        page = QWidget(); layout = QVBoxLayout(page); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"<h3>{title}</h3> 模块开发中..."))
        self.stack.addWidget(page)

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭时选择最小化到托盘或退出"""
        if self.wsl.is_running:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("选择操作")
            dlg.setText("服务正在运行，请选择操作：")
            dlg.setIcon(QMessageBox.Icon.Question)
            btn_tray = dlg.addButton("最小化到托盘", QMessageBox.ButtonRole.AcceptRole)
            btn_quit = dlg.addButton("停止服务并退出", QMessageBox.ButtonRole.DestructiveRole)
            dlg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            dlg.exec()
            clicked = dlg.clickedButton()
            if clicked == btn_tray:
                self.hide()
                self.tray_icon.show()
                self.tray_icon.showMessage("Nekro-Agent", "已最小化到托盘，服务继续运行", QSystemTrayIcon.MessageIcon.Information, 2000)
                event.ignore()
            elif clicked == btn_quit:
                self.wsl.stop_services()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _on_tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.tray_icon.hide()

    def _quit_app(self):
        """从托盘退出应用"""
        if self.wsl.is_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "服务正在运行，退出将停止所有容器。确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.wsl.stop_services()
                QApplication.quit()
        else:
            QApplication.quit()

    def _show_credentials_dialog(self, info):
        """弹窗显示部署凭据"""
        print(f"[DEBUG] 凭据信息: {info}")
        print(f"[DEBUG] deploy_mode: {info.get('deploy_mode')}")

        dlg = QDialog(self)
        dlg.setWindowTitle("部署凭据信息")
        dlg.setFixedSize(480, 400)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("部署完成 - 请妥善保存以下信息")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        # NekroAgent 信息
        port = info.get("port", "8021")
        na_info = QLabel(
            f"<b style='color: #0969da;'>NekroAgent</b><br>"
            f"<b>访问地址:</b> http://127.0.0.1:{port}<br>"
            f"<b>管理员账号:</b> admin<br>"
            f"<b>管理员密码:</b> {info.get('admin_password', '')}<br>"
            f"<b>OneBot 令牌:</b> {info.get('onebot_token', '')}"
        )
        na_info.setStyleSheet(
            "background: #f6f8fa; border: 1px solid #d0d7de; "
            "border-radius: 6px; padding: 15px; font-size: 13px; color: #24292f;"
        )
        na_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        na_info.setWordWrap(True)
        layout.addWidget(na_info)

        # NapCat 信息
        if info.get("deploy_mode") == "napcat":
            napcat_port = info.get('napcat_port', '6099')
            napcat_token = info.get("napcat_token", "")
            token_text = napcat_token if napcat_token else "(等待捕获)"

            napcat_info = QLabel(
                f"<b style='color: #1f883d;'>NapCat</b><br>"
                f"<b>访问地址:</b> http://127.0.0.1:{napcat_port}<br>"
                f"<b>登录 Token:</b> {token_text}"
            )
            napcat_info.setStyleSheet(
                "background: #f6fff8; border: 1px solid #d0d7de; "
                "border-radius: 6px; padding: 15px; font-size: 13px; color: #24292f;"
            )
            napcat_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            napcat_info.setWordWrap(True)
            layout.addWidget(napcat_info)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_copy = QPushButton("复制到剪贴板")
        btn_copy.setStyleSheet(
            "QPushButton { background: #2da44e; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-size: 13px; }"
            "QPushButton:hover { background: #218838; }"
        )
        copy_text = (
            f"=== NekroAgent ===\n"
            f"访问地址: http://127.0.0.1:{port}\n"
            f"管理员账号: admin\n"
            f"管理员密码: {info.get('admin_password', '')}\n"
            f"OneBot 令牌: {info.get('onebot_token', '')}"
        )
        if info.get("deploy_mode") == "napcat":
            napcat_port = info.get('napcat_port', '6099')
            napcat_token = info.get("napcat_token", "") or "(等待捕获)"
            copy_text += (
                f"\n\n=== NapCat ===\n"
                f"访问地址: http://127.0.0.1:{napcat_port}\n"
                f"登录 Token: {napcat_token}"
            )
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(copy_text),
            btn_copy.setText("已复制!"),
        ))

        btn_close = QPushButton("关闭")
        btn_close.setStyleSheet(
            "QPushButton { background: #f6f8fa; border: 1px solid #d0d7de; "
            "border-radius: 6px; padding: 8px 20px; font-size: 13px; }"
            "QPushButton:hover { background: #eaeef2; }"
        )
        btn_close.clicked.connect(dlg.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        dlg.exec()

    def _show_saved_credentials(self):
        """从配置读取已保存的凭据并弹窗显示"""
        info = self.config.get("deploy_info")
        if not info:
            QMessageBox.information(self, "提示", "尚未部署，暂无凭据信息。\n请先完成部署。")
            return
        self._show_credentials_dialog(info)
