import sys
import os
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QLineEdit, QFrame, QSizePolicy, QProgressBar, QGridLayout,
                             QComboBox, QTextEdit, QCheckBox, QFileDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QSize, qInstallMessageHandler, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QPixmap

# --- 屏蔽 Qt 繁琐日志 ---
def qt_message_handler(mode, context, message):
    if "libpng warning" in message or "Accessibility" in message:
        return

qInstallMessageHandler(qt_message_handler)


# --- 日志重定向 ---
class LogRedirector:
    """将 stdout 和 stderr 重定向到文件和控制台（安全处理编码）"""
    def __init__(self, log_file):
        self.log_file = log_file
        self.file = open(log_file, 'w', encoding='utf-8', buffering=1)
        # 保存原始的 stdout/stderr（已经是打开状态的文件对象）
        self.console = sys.__stdout__

    def write(self, message):
        try:
            # 写入文件（使用 UTF-8）
            self.file.write(message)
            self.file.flush()
        except Exception:
            pass

        try:
            # 写入控制台（尝试用原始 stdout）
            self.console.write(message)
            self.console.flush()
        except UnicodeEncodeError:
            # 如果编码出错，用 errors='replace' 重新尝试
            try:
                self.console.write(message.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
                self.console.flush()
            except Exception:
                pass
        except Exception:
            pass

    def flush(self):
        try:
            self.file.flush()
        except Exception:
            pass
        try:
            self.console.flush()
        except Exception:
            pass

    def close(self):
        try:
            self.file.close()
        except Exception:
            pass

# --- 样式表 (CSS) ---
STYLESHEET = """
QMainWindow {
    background-color: #f6f8fa;
}

/* 强制去掉所有按钮的焦点虚线框/选中框 */
QPushButton {
    outline: none;
}
QPushButton:focus {
    outline: none;
}

/* 侧边栏 */
QFrame#Sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0d7de;
}

QPushButton.SidebarBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 0 15px;
    text-align: left;
    color: #57606a;
    font-size: 14px;
    font-weight: 600;
}
QPushButton.SidebarBtn:hover {
    background-color: #f3f4f6;
    color: #24292f;
}
QPushButton.SidebarBtn:checked {
    background-color: #ddf4ff;
    color: #0969da;
}

/* 下拉框样式 */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 5px 10px;
    min-width: 200px;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #0969da;
}

/* 日志文本框 */
QTextEdit#LogViewer {
    background-color: #0d1117;
    color: #e6edf3;
    border-radius: 8px;
    padding: 15px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
}

/* 卡片按钮基础样式 */
QPushButton#ActionBtn, QPushButton#DeployBtn, QPushButton#UninstallBtn {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    text-align: left;
    padding: 15px;
}

/* 只有悬停时才显示各自的强调色，彻底解决绿色选中框问题 */
QPushButton#ActionBtn:hover {
    border-color: #0969da;
    background-color: #f6f8fa;
}

QPushButton#DeployBtn:hover {
    border-color: #2da44e;
    background-color: #f6fff8;
}

QPushButton#UninstallBtn:hover {
    border-color: #cf222e;
    background-color: #fff8f8;
}

QPushButton:pressed {
    background-color: #f3f4f6;
}

QLabel#ActionTitle {
    font-size: 16px;
    font-weight: bold;
    color: #24292f;
}
QLabel#ActionDesc {
    font-size: 12px;
    color: #57606a;
    margin-top: 4px;
}

/* 复选框样式 */
QCheckBox {
    font-size: 14px;
    color: #24292f;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 1px solid #d0d7de;
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}
"""

class ActionButton(QPushButton):
    def __init__(self, icon, title, desc, btn_id=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionBtn")
        if btn_id:
            self.setObjectName(btn_id)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(110)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 36px; border: none; background: transparent;")
        layout.addWidget(lbl_icon)

        text_container = QWidget()
        text_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_container.setStyleSheet("background: transparent; border: none;")
        v_layout = QVBoxLayout(text_container)
        v_layout.setContentsMargins(0, 5, 0, 5)
        v_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("ActionTitle")
        lbl_desc = QLabel(desc)
        lbl_desc.setObjectName("ActionDesc")

        v_layout.addWidget(lbl_title)
        v_layout.addWidget(lbl_desc)
        v_layout.addStretch()

        layout.addWidget(text_container)
        layout.addStretch()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nekro-Agent 管理")
        self.resize(1000, 750)
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 左侧侧边栏 ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 25)
        sidebar_layout.setSpacing(12)

        logo_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_label.setScaledContents(True)
        logo_text = QLabel("Nekro Agent")
        logo_text.setStyleSheet("font-size: 18px; font-weight: bold; color: #24292f; margin-left: 5px;")

        icon_path = "NekroAgent.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("N")
            logo_label.setStyleSheet("background-color: #24292f; color: white; border-radius: 8px; font-weight: bold; font-size: 20px;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        sidebar_layout.addLayout(logo_layout)
        sidebar_layout.addSpacing(30)

        self.btn_home = self.create_sidebar_btn("🏠", "项目概览")
        self.btn_browser = self.create_sidebar_btn("🌐", "应用浏览器")
        self.btn_logs = self.create_sidebar_btn("📝", "运行日志")
        self.btn_files = self.create_sidebar_btn("📁", "文件管理")
        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_browser)
        sidebar_layout.addWidget(self.btn_logs)
        sidebar_layout.addWidget(self.btn_files)
        sidebar_layout.addStretch()
        self.btn_settings = self.create_sidebar_btn("⚙️", "系统设置")
        sidebar_layout.addWidget(self.btn_settings)

        main_layout.addWidget(self.sidebar)

        # --- 2. 右侧主区域 ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.init_home_page()
        self.init_browser_page()
        self.init_logs_page()
        self.init_empty_page("文件管理")
        self.init_settings_page()

        self.switch_tab(0)
        self.setFocus()

    def create_sidebar_btn(self, icon, text):
        btn = QPushButton(f"  {icon}   {text}")
        btn.setObjectName("SidebarBtn")
        btn.setCheckable(True)
        btn.setFixedHeight(48)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        index_map = {"项目概览": 0, "应用浏览器": 1, "运行日志": 2, "文件管理": 3, "系统设置": 4}
        if text in index_map:
            btn.clicked.connect(lambda: self.switch_tab(index_map[text]))
        return btn

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        btns = [self.btn_home, self.btn_browser, self.btn_logs, self.btn_files, self.btn_settings]
        for i, btn in enumerate(btns):
            btn.setChecked(i == index)

    def init_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        title_box = QVBoxLayout()
        lbl_title = QLabel("Nekro-Agent 环境管理")
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #24292f;")
        lbl_status = QLabel("● 当前状态: 未就绪")
        lbl_status.setStyleSheet("font-size: 14px; color: #cf222e; margin-top: 5px;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_status)
        layout.addLayout(title_box)
        layout.addSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(20)

        grid.addWidget(ActionButton("📥", "下载虚拟机镜像", "从云端获取最新系统环境"), 0, 0)
        grid.addWidget(ActionButton("🚀", "一键部署项目", "自动配置并运行 Docker 服务", btn_id="DeployBtn"), 0, 1)
        grid.addWidget(ActionButton("🔄", "检查环境更新", "拉取最新镜像并重启服务"), 1, 0)
        grid.addWidget(ActionButton("🗑️", "卸载清除环境", "删除容器、镜像及所有数据", btn_id="UninstallBtn"), 1, 1)
        grid.addWidget(ActionButton("🏠", "访问项目主页", "获取文档、教程及社区支持"), 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        self.stack.addWidget(page)

    def init_browser_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame(); toolbar.setObjectName("TopBar"); toolbar.setFixedHeight(55)
        tb_layout = QHBoxLayout(toolbar); tb_layout.setContentsMargins(15, 0, 15, 0)

        btn_back = QPushButton("◀"); btn_back.setFixedSize(32, 32); btn_back.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_forward = QPushButton("▶"); btn_forward.setFixedSize(32, 32); btn_forward.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_reload = QPushButton("🔄"); btn_reload.setFixedSize(32, 32); btn_reload.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.url_bar = QLineEdit(); self.url_bar.setObjectName("UrlBar"); self.url_bar.setText("http://localhost:8080"); self.url_bar.setReadOnly(True)
        btn_open = QPushButton("外部打开"); btn_open.setFixedHeight(32); btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        tb_layout.addWidget(btn_back); tb_layout.addWidget(btn_forward); tb_layout.addWidget(btn_reload); tb_layout.addWidget(self.url_bar); tb_layout.addWidget(btn_open)
        layout.addWidget(toolbar)

        self.webview = QWebEngineView()
        self.webview.setHtml("<html><body style='background-color:#f6f8fa; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; color:#8b949e;'><h2>服务启动后自动加载界面</h2></body></html>")
        layout.addWidget(self.webview)

        btn_back.clicked.connect(self.webview.back)
        btn_forward.clicked.connect(self.webview.forward)
        btn_reload.clicked.connect(self.webview.reload)
        self.webview.urlChanged.connect(lambda url: self.url_bar.setText(url.toString()))
        self.stack.addWidget(page)

    def init_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        top_layout = QHBoxLayout()
        lbl_select = QLabel("选择日志源:")
        lbl_select.setStyleSheet("font-weight: bold; color: #24292f;")

        self.log_source_combo = QComboBox()
        self.log_source_combo.addItems(["虚拟机系统日志", "Docker 守护进程日志", "--- Docker 容器 ---", "[待部署] Nekro-Agent 主进程"])
        self.log_source_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        btn_clear = QPushButton("清空日志")
        btn_clear.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_clear.setFixedWidth(100)

        top_layout.addWidget(lbl_select); top_layout.addWidget(self.log_source_combo); top_layout.addStretch(); top_layout.addWidget(btn_clear)
        layout.addLayout(top_layout)

        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("LogViewer")
        self.log_viewer.setReadOnly(True)
        self.log_viewer.append("<span style='color:#7ee787;'>[INFO]</span> 欢迎使用 Nekro-Agent 管理系统")
        layout.addWidget(self.log_viewer)
        self.stack.addWidget(page)

    def init_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        lbl_title = QLabel("系统设置")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #24292f;")
        layout.addWidget(lbl_title)

        # 1. 开机自启
        self.check_autostart = QCheckBox("随系统开机自动启动 Nekro-Agent 管理系统")
        self.check_autostart.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.check_autostart)

        # 2. 共享目录设置
        dir_layout = QVBoxLayout()
        lbl_dir = QLabel("虚拟机共享目录 (Shared Directory):")
        lbl_dir.setStyleSheet("font-weight: bold; color: #24292f; margin-top: 10px;")

        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit(os.path.join(os.getcwd(), "shared"))
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("padding: 8px; border: 1px solid #d0d7de; border-radius: 6px; background: white;")

        btn_select = QPushButton("选择目录")
        btn_select.setFixedWidth(100); btn_select.setFixedHeight(35); btn_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_select.clicked.connect(self.select_shared_dir)

        path_input_layout.addWidget(self.path_edit); path_input_layout.addWidget(btn_select)
        dir_layout.addWidget(lbl_dir); dir_layout.addLayout(path_input_layout)
        layout.addLayout(dir_layout)

        layout.addStretch()
        self.stack.addWidget(page)

    def select_shared_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择共享目录", os.getcwd())
        if directory:
            self.path_edit.setText(directory)

    def init_empty_page(self, title):
        page = QWidget(); layout = QVBoxLayout(page); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title = QLabel(title); lbl_title.setObjectName("EmptyTitle")
        lbl_desc = QLabel(f"{title} 模块正在开发中..."); lbl_desc.setObjectName("EmptyDesc")
        layout.addWidget(lbl_title, 0, Qt.AlignmentFlag.AlignHCenter); layout.addWidget(lbl_desc, 0, Qt.AlignmentFlag.AlignHCenter)
        self.stack.addWidget(page)

if __name__ == "__main__":
    # 强制设置控制台编码为 UTF-8（Windows 兼容）
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

    # 设置日志文件
    log_file = os.path.join(os.path.dirname(__file__), "debug.log")

    # 重定向 stdout 和 stderr 到日志文件和控制台
    redirector = LogRedirector(log_file)
    sys.stdout = redirector
    sys.stderr = redirector

    print(f"[LOG] 程序启动，日志文件: {log_file}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
