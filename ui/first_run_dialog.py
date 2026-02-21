import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget, QStackedWidget,
                             QMessageBox, QLineEdit, QFileDialog,
                             QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class EnvCheckThread(QThread):
    """后台环境检测线程"""
    finished = pyqtSignal(dict)

    def __init__(self, wsl_manager):
        super().__init__()
        self.wsl_manager = wsl_manager

    def run(self):
        result = self.wsl_manager.check_environment()
        self.finished.emit(result)


class CreateDistroThread(QThread):
    """后台创建发行版线程"""
    finished = pyqtSignal(bool)

    def __init__(self, wsl_manager, install_dir):
        super().__init__()
        self.wsl_manager = wsl_manager
        self.install_dir = install_dir

    def run(self):
        ok = self.wsl_manager.create_distro(self.install_dir)
        self.finished.emit(ok)


class FirstRunDialog(QDialog):
    """首次运行向导对话框"""

    deploy_requested = pyqtSignal(str)  # 发出部署模式: "lite" 或 "napcat"

    def __init__(self, wsl_manager, config, parent=None):
        super().__init__(parent)
        self.wsl_manager = wsl_manager
        self.config = config
        self.env_result = None

        self.setWindowTitle("Nekro-Agent 环境配置向导")
        self.setFixedSize(560, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._init_check_page()       # 页面 0: 环境检测
        self._init_create_page()      # 页面 1: 创建运行环境
        self._init_select_page()      # 页面 2: 版本选择
        self._init_datadir_page()     # 页面 3: 数据目录配置

        self.stack.setCurrentIndex(0)

        # 监听 wsl_manager 的进度信号
        self.wsl_manager.progress_updated.connect(self._on_progress)

        # 启动检测
        self._start_check()

    # ------------------------------------------------------------------ #
    #  页面 0：环境检测
    # ------------------------------------------------------------------ #

    def _init_check_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("环境检测")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        desc = QLabel("正在检测系统环境，请稍候...")
        desc.setStyleSheet("font-size: 14px; color: #57606a;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        self.check_desc = desc

        # 检测项
        self.lbl_wsl = self._create_check_item("WSL2")
        self.lbl_distro = self._create_check_item("NekroAgent 运行环境")
        self.lbl_docker = self._create_check_item("Docker")
        self.lbl_compose = self._create_check_item("Docker Compose")

        layout.addWidget(self.lbl_wsl)
        layout.addWidget(self.lbl_distro)
        layout.addWidget(self.lbl_docker)
        layout.addWidget(self.lbl_compose)

        # 进度条（安装 Docker 时显示）
        self.check_progress = QProgressBar()
        self.check_progress.setRange(0, 0)  # 不确定进度（循环动画）
        self.check_progress.setFixedHeight(6)
        self.check_progress.setStyleSheet(
            "QProgressBar { border: none; background: #e8e9eb; border-radius: 3px; }"
            "QProgressBar::chunk { background: #0969da; border-radius: 3px; }"
        )
        self.check_progress.setVisible(False)
        layout.addWidget(self.check_progress)

        layout.addStretch()

        # 底部按钮
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_action = QPushButton("检测中...")
        self.btn_action.setFixedHeight(38)
        self.btn_action.setMinimumWidth(120)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setStyleSheet(
            "QPushButton { background-color: #2da44e; color: white; border: none; "
            "border-radius: 6px; font-size: 14px; font-weight: 600; padding: 0 20px; }"
            "QPushButton:hover { background-color: #28943f; }"
            "QPushButton:disabled { background-color: #94d3a2; }"
        )
        self.btn_action.setEnabled(False)
        self.btn_action.clicked.connect(self._handle_action)
        btn_box.addWidget(self.btn_action)

        layout.addLayout(btn_box)
        self.stack.addWidget(page)

    def _create_check_item(self, name):
        lbl = QLabel(f"⏳  {name}")
        lbl.setStyleSheet("font-size: 15px; color: #57606a; padding: 5px 0;")
        lbl.setProperty("check_name", name)
        return lbl

    def _update_check_item(self, label, ok, detail=""):
        name = label.property("check_name")
        if ok:
            label.setText(f"✅  {name}" + (f"  —  {detail}" if detail else ""))
            label.setStyleSheet("font-size: 15px; color: #2da44e; padding: 5px 0;")
        else:
            label.setText(f"❌  {name}" + (f"  —  {detail}" if detail else ""))
            label.setStyleSheet("font-size: 15px; color: #cf222e; padding: 5px 0;")

    def _start_check(self):
        self._check_thread = EnvCheckThread(self.wsl_manager)
        self._check_thread.finished.connect(self._on_check_done)
        self._check_thread.start()

    def _on_check_done(self, result):
        self.env_result = result

        self._update_check_item(self.lbl_wsl, result["wsl_installed"])
        self._update_check_item(self.lbl_distro, bool(result["distro"]),
                                result["distro"] if result["distro"] else "未创建")
        self._update_check_item(self.lbl_docker, result["docker_available"])
        self._update_check_item(self.lbl_compose, result["compose_available"])

        all_ok = (result["wsl_installed"] and result["distro"]
                  and result["docker_available"] and result["compose_available"])

        if all_ok:
            self.check_desc.setText("所有环境组件已就绪！请点击下一步选择部署版本。")
            self.btn_action.setText("下一步")
            self.btn_action.setEnabled(True)
            self._action_mode = "next"
        else:
            if not result["wsl_installed"]:
                self.check_desc.setText("WSL2 未安装，请点击安装。")
                self.btn_action.setText("安装 WSL2")
                self._action_mode = "install_wsl"
            elif not result["distro"]:
                self.check_desc.setText("NekroAgent 运行环境未创建，请点击创建。")
                self.btn_action.setText("创建运行环境")
                self._action_mode = "create_distro"
            elif not result["docker_available"] or not result["compose_available"]:
                self.check_desc.setText("Docker 未安装，请点击安装。")
                self.btn_action.setText("安装 Docker")
                self._action_mode = "install_docker"
            self.btn_action.setEnabled(True)

    def _handle_action(self):
        mode = getattr(self, '_action_mode', None)

        if mode == "next":
            self.stack.setCurrentIndex(2)
            return

        if mode == "install_wsl":
            reply = QMessageBox.information(
                self, "安装 WSL2",
                "将以管理员权限安装 WSL2。\n\n"
                "注意：安装过程需要 5-10 分钟，请耐心等待。\n"
                "安装完成后将自动重启电脑。",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Ok:
                self.wsl_manager.install_wsl()
            return

        if mode == "create_distro":
            self.stack.setCurrentIndex(1)
            return

        if mode == "install_docker":
            self.wsl_manager.install_docker()
            self.check_desc.setText("正在安装 Docker...")
            self.btn_action.setEnabled(False)
            self.check_progress.setVisible(True)
            self._action_mode = "recheck"
            return

        if mode == "recheck":
            self._recheck()
            return

    def _recheck(self):
        """重新执行环境检测"""
        self.btn_action.setEnabled(False)
        self.btn_action.setText("检测中...")
        self.check_desc.setText("正在重新检测...")
        self.check_progress.setVisible(False)

        for lbl in [self.lbl_wsl, self.lbl_distro, self.lbl_docker, self.lbl_compose]:
            name = lbl.property("check_name")
            lbl.setText(f"⏳  {name}")
            lbl.setStyleSheet("font-size: 15px; color: #57606a; padding: 5px 0;")

        self._start_check()

    # ------------------------------------------------------------------ #
    #  页面 1：创建运行环境
    # ------------------------------------------------------------------ #

    def _init_create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        title = QLabel("创建 NekroAgent 运行环境")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        desc = QLabel("将下载 Ubuntu 并创建专用 WSL 发行版，与系统已有的 WSL 环境互不影响。")
        desc.setStyleSheet("font-size: 13px; color: #57606a;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 安装目录
        lbl_dir = QLabel("安装目录:")
        lbl_dir.setStyleSheet("font-size: 14px; font-weight: 600; color: #24292f; margin-top: 10px;")
        layout.addWidget(lbl_dir)

        dir_box = QHBoxLayout()
        self.dir_edit = QLineEdit(self.wsl_manager.get_default_install_dir())
        self.dir_edit.setStyleSheet(
            "padding: 8px; border: 1px solid #d0d7de; border-radius: 6px; "
            "background: white; font-size: 13px;"
        )
        btn_browse = QPushButton("浏览...")
        btn_browse.setFixedHeight(35)
        btn_browse.setFixedWidth(80)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_install_dir)
        dir_box.addWidget(self.dir_edit)
        dir_box.addWidget(btn_browse)
        layout.addLayout(dir_box)

        hint = QLabel("此目录将存放 WSL 虚拟磁盘文件，建议预留 10GB 以上空间。")
        hint.setStyleSheet("font-size: 12px; color: #8b949e;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 进度条
        self.create_progress = QProgressBar()
        self.create_progress.setRange(0, 0)  # 不确定进度
        self.create_progress.setFixedHeight(8)
        self.create_progress.setStyleSheet(
            "QProgressBar { border: none; background: #e8e9eb; border-radius: 4px; }"
            "QProgressBar::chunk { background: #0969da; border-radius: 4px; }"
        )
        self.create_progress.setVisible(False)
        layout.addWidget(self.create_progress)

        # 进度状态文本
        self.lbl_progress = QLabel("")
        self.lbl_progress.setStyleSheet("font-size: 13px; color: #0969da; margin-top: 8px;")
        self.lbl_progress.setWordWrap(True)
        self.lbl_progress.setWordWrap(True)
        layout.addWidget(self.lbl_progress)

        layout.addStretch()

        # 底部按钮
        btn_box = QHBoxLayout()

        self.btn_back = QPushButton("返回")
        self.btn_back.setFixedHeight(38)
        self.btn_back.setFixedWidth(80)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "QPushButton { background-color: #f3f4f6; color: #24292f; border: 1px solid #d0d7de; "
            "border-radius: 6px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #e8e9eb; }"
        )
        self.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_box.addWidget(self.btn_back)

        btn_box.addStretch()

        self.btn_create = QPushButton("开始创建")
        self.btn_create.setFixedHeight(38)
        self.btn_create.setFixedWidth(120)
        self.btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create.setStyleSheet(
            "QPushButton { background-color: #2da44e; color: white; border: none; "
            "border-radius: 6px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #28943f; }"
            "QPushButton:disabled { background-color: #94d3a2; }"
        )
        self.btn_create.clicked.connect(self._start_create)
        btn_box.addWidget(self.btn_create)

        layout.addLayout(btn_box)
        self.stack.addWidget(page)

    def _browse_install_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "选择安装目录", self.dir_edit.text()
        )
        if d:
            # 在选择的目录下加上 NekroAgent 子目录
            self.dir_edit.setText(os.path.join(d, "NekroAgent", "wsl"))

    def _start_create(self):
        install_dir = self.dir_edit.text().strip()
        if not install_dir:
            QMessageBox.warning(self, "提示", "请指定安装目录")
            return

        self.btn_create.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.dir_edit.setReadOnly(True)
        self.create_progress.setVisible(True)
        self.lbl_progress.setText("准备下载...")

        self._create_thread = CreateDistroThread(self.wsl_manager, install_dir)
        self._create_thread.finished.connect(self._on_create_done)
        self._create_thread.start()

    def _on_progress(self, text):
        """接收 wsl_manager.progress_updated 信号"""
        # 检查当前是否在创建页面（页面 1）
        if self.stack.currentIndex() == 1:
            self.lbl_progress.setText(text)
            return

        # 检测页面的处理
        if text == "__docker_done__":
            self.check_progress.setVisible(False)
            self._recheck()
            return
        if text == "__docker_fail__":
            self.check_progress.setVisible(False)
            self.check_desc.setText("Docker 安装失败，请重试。")
            self.btn_action.setText("安装 Docker")
            self.btn_action.setEnabled(True)
            self._action_mode = "install_docker"
            return

    def _on_create_done(self, success):
        self.btn_create.setEnabled(True)
        self.btn_back.setEnabled(True)
        self.dir_edit.setReadOnly(False)
        self.create_progress.setVisible(False)

        if success:
            self.lbl_progress.setText("环境创建完成！")
            self.lbl_progress.setStyleSheet("font-size: 13px; color: #2da44e; margin-top: 8px;")
            # 直接跳到版本选择页
            self.stack.setCurrentIndex(2)
        else:
            self.lbl_progress.setStyleSheet("font-size: 13px; color: #cf222e; margin-top: 8px;")

    # ------------------------------------------------------------------ #
    #  页面 2：版本选择
    # ------------------------------------------------------------------ #

    def _init_select_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("选择部署版本")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        desc = QLabel("请选择要部署的 Nekro-Agent 版本:")
        desc.setStyleSheet("font-size: 14px; color: #57606a;")
        layout.addWidget(desc)

        self.card_lite = self._create_mode_card(
            "精简版 (Lite)",
            "仅包含核心 Nekro-Agent 服务\n适合不需要 QQ 机器人功能的用户",
            "lite",
        )
        layout.addWidget(self.card_lite)

        self.card_napcat = self._create_mode_card(
            "完整版 (Napcat)",
            "包含 Nekro-Agent + QQ 机器人 (Napcat)\n需要更多系统资源",
            "napcat",
        )
        layout.addWidget(self.card_napcat)

        layout.addStretch()
        self.stack.addWidget(page)

    def _create_mode_card(self, title, desc, mode):
        card = QPushButton()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedHeight(90)
        card.setStyleSheet(
            "QPushButton { background-color: #ffffff; border: 2px solid #d0d7de; "
            "border-radius: 10px; padding: 15px 20px; }"
            "QPushButton:hover { border-color: #0969da; background-color: #f6f8fa; }"
        )

        inner = QVBoxLayout(card)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(4)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #24292f; "
                                "background: transparent; border: none;")
        lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 12px; color: #57606a; "
                               "background: transparent; border: none;")
        lbl_desc.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        inner.addWidget(lbl_title)
        inner.addWidget(lbl_desc)

        card.clicked.connect(lambda: self._select_mode(mode))
        return card

    def _select_mode(self, mode):
        self._selected_mode = mode
        if self.config:
            self.config.set("deploy_mode", mode)
        self.stack.setCurrentIndex(3)  # 跳转到数据目录配置页

    # ------------------------------------------------------------------ #
    #  页面 3：数据目录配置
    # ------------------------------------------------------------------ #

    def _init_datadir_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        title = QLabel("配置数据目录")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #24292f;")
        layout.addWidget(title)

        desc = QLabel("数据目录用于存储 NekroAgent 运行数据（数据库、配置、日志等）。")
        desc.setStyleSheet("font-size: 14px; color: #57606a;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        lbl_dir = QLabel("数据目录路径:")
        lbl_dir.setStyleSheet("font-size: 14px; font-weight: 600; color: #24292f; margin-top: 10px;")
        layout.addWidget(lbl_dir)

        self.datadir_edit = QLineEdit("/root/nekro_agent_data")
        self.datadir_edit.setStyleSheet(
            "padding: 8px; border: 1px solid #d0d7de; border-radius: 6px; "
            "background: white; font-size: 13px;"
        )
        layout.addWidget(self.datadir_edit)

        hint = QLabel("此目录位于 WSL 内部，可通过 \\\\wsl$\\NekroAgent\\... 在 Windows 中访问。")
        hint.setStyleSheet("font-size: 12px; color: #8b949e;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()

        # 底部按钮
        btn_box = QHBoxLayout()

        btn_back = QPushButton("返回")
        btn_back.setFixedHeight(38)
        btn_back.setFixedWidth(80)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(
            "QPushButton { background-color: #f3f4f6; color: #24292f; border: 1px solid #d0d7de; "
            "border-radius: 6px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #e8e9eb; }"
        )
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_box.addWidget(btn_back)

        btn_box.addStretch()

        btn_deploy = QPushButton("开始部署")
        btn_deploy.setFixedHeight(38)
        btn_deploy.setFixedWidth(120)
        btn_deploy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_deploy.setStyleSheet(
            "QPushButton { background-color: #2da44e; color: white; border: none; "
            "border-radius: 6px; font-size: 14px; font-weight: 600; }"
            "QPushButton:hover { background-color: #28943f; }"
        )
        btn_deploy.clicked.connect(self._confirm_datadir)
        btn_box.addWidget(btn_deploy)

        layout.addLayout(btn_box)
        self.stack.addWidget(page)

    def _confirm_datadir(self):
        data_dir = self.datadir_edit.text().strip()
        if not data_dir:
            QMessageBox.warning(self, "提示", "请指定数据目录")
            return
        if self.config:
            self.config.set("data_dir", data_dir)
            self.config.set("first_run", False)
        self.deploy_requested.emit(self._selected_mode)
        self.accept()
