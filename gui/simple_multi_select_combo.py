from PyQt6.QtWidgets import QComboBox, QLineEdit
from PyQt6.QtCore import Qt

class SimpleMultiSelectComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 绑定输入框
        self.edit = QLineEdit()
        self.setLineEdit(self.edit)

        # 核心样式：彻底抹除下拉按钮区域
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #b6d4f2;
                border-radius: 6px;
                min-height: 34px;
                padding-left: 8px;
                padding-right: 8px;
                background-color: #ffffff;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #222222;
            }
            QComboBox:hover {
                border: 1px solid #62a8ff;
            }
            QComboBox:focus {
                border: 1px solid #3388ee;
                outline: none;
            }
            /* 完全隐藏下拉按钮容器 */
            QComboBox::drop-down {
                width: 0px !important;
                border: none !important;
                background: transparent !important;
            }
            /* 隐藏箭头图标 */
            QComboBox::down-arrow {
                width: 0px;
                height: 0px;
                image: none;
            }
        """)

        # 强制禁用下拉弹窗，键盘快捷键也打不开
        self.setMaxVisibleItems(0)
        # 禁止点击触发下拉
        self.activated.connect(lambda: None)

    def setPlaceholderText(self, text):
        self.edit.setPlaceholderText(text)

    def get_selected_items(self):
        text = self.edit.text().strip()
        if not text:
            return []
        return [x.strip() for x in text.split(",") if x.strip()]

    def clear(self):
        self.edit.clear()