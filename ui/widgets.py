from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

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
