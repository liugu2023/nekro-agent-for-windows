from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui.styles import STYLESHEET


def show_notice_dialog(parent, title, text, button_text="确定", danger=False):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(340)
    dialog.setMaximumWidth(440)
    dialog.setModal(True)
    dialog.setStyleSheet(STYLESHEET)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setProperty("role", "dialog_title")
    title_label.setWordWrap(True)
    title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(title_label)

    desc_label = QLabel(text)
    desc_label.setProperty("role", "dialog_desc")
    desc_label.setWordWrap(True)
    desc_label.setTextFormat(Qt.TextFormat.PlainText)
    desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    layout.addWidget(desc_label)

    button_row = QHBoxLayout()
    button_row.addStretch()
    btn = QPushButton(button_text)
    if danger:
        btn.setProperty("role", "danger")
    btn.clicked.connect(dialog.accept)
    button_row.addWidget(btn)
    layout.addLayout(button_row)
    dialog.adjustSize()
    dialog.exec()


class ActionButton(QPushButton):
    def __init__(self, badge, title, desc, variant="default", parent=None):
        super().__init__(parent)
        self.setProperty("variant", variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(112)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._base_min_height = 112

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        self._layout = layout

        self.badge_label = QLabel(badge)
        self.badge_label.setObjectName("ActionBadge")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setFixedSize(42, 42)
        layout.addWidget(self.badge_label)

        text_container = QWidget()
        text_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)
        self._text_layout = text_layout

        self.title_label = QLabel(title)
        self.title_label.setObjectName("ActionTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.desc_label = QLabel(desc)
        self.desc_label.setObjectName("ActionDesc")
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch()
        layout.addWidget(text_container, 1)

    def set_scale(self, scale):
        scale = max(0.78, min(scale, 1.0))

        badge_size = int(42 * scale)
        self.badge_label.setFixedSize(badge_size, badge_size)

        title_font = QFont(self.title_label.font())
        title_font.setPointSizeF(15 * scale)
        self.title_label.setFont(title_font)

        desc_font = QFont(self.desc_label.font())
        desc_font.setPointSizeF(12 * scale)
        self.desc_label.setFont(desc_font)

        badge_font = QFont(self.badge_label.font())
        badge_font.setPointSizeF(13 * scale)
        badge_font.setBold(True)
        self.badge_label.setFont(badge_font)

        self._layout.setContentsMargins(
            int(18 * scale),
            int(18 * scale),
            int(18 * scale),
            int(18 * scale),
        )
        self._layout.setSpacing(int(14 * scale))
        self._text_layout.setSpacing(max(2, int(4 * scale)))
        self.setMinimumHeight(int(self._base_min_height * scale))


class MetricCard(QFrame):
    def __init__(self, label, value, hint="", accent="blue", parent=None):
        super().__init__(parent)
        self.setProperty("accent", accent)
        self.setObjectName("MetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setObjectName("MetricLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("MetricValue")
        value_widget.setWordWrap(True)
        value_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)

        if hint:
            hint_widget = QLabel(hint)
            hint_widget.setObjectName("MetricHint")
            hint_widget.setWordWrap(True)
            hint_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            layout.addWidget(hint_widget)


class SectionCard(QFrame):
    def __init__(self, title, desc="", parent=None):
        super().__init__(parent)
        self.setObjectName("SectionCard")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(22, 22, 22, 22)
        self._layout.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(4)

        title_widget = QLabel(title)
        title_widget.setObjectName("SectionTitle")
        header.addWidget(title_widget)

        if desc:
            desc_widget = QLabel(desc)
            desc_widget.setObjectName("SectionDesc")
            desc_widget.setWordWrap(True)
            desc_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            header.addWidget(desc_widget)

        self._layout.addLayout(header)

    def body_layout(self):
        return self._layout
