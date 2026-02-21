# 全局样式表
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

/* 交互颜色 */
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
