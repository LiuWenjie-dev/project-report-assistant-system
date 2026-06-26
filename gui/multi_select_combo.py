from PyQt6.QtWidgets import QComboBox, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

class MultiSelectComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 完整美化样式
        self.setStyleSheet("""
            QComboBox {
                combobox-popup: 1;
                border: 1px solid #b6d4f2;
                border-radius: 6px;
                min-height: 34px;
                padding-left: 8px;
                padding-right: 30px;
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
            QComboBox::drop-down {
                width: 32px;
                border: none;
                border-left: 1px solid #e0eaf7;
                background-color: #f7fbff;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 10px;
                height: 10px;
                border-top: 2px solid #6688bb;
                border-right: 2px solid #6688bb;
                transform: rotate(135deg);
                margin-left: 10px;
            }
            QAbstractItemView {
                border: 1px solid #c0d8f0;
                border-radius: 6px;
                background-color: #ffffff;
                outline: none;
                padding: 4px;
            }
            QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 28px;
            }
            QAbstractItemView::item:hover {
                background-color: #e8f2ff;
            }
            QAbstractItemView::item:selected {
                background-color: #d0e4fb;
                color: #114488;
            }
        """)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setStyleSheet("border:none;background:transparent;")
        self.setLineEdit(self.line_edit)

        self.model = QStandardItemModel()
        self.setModel(self.model)
        self._block_signal = False
        self.model.itemChanged.connect(self.item_check_change)

    def addItems(self, items):
        self.model.clear()
        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.model.appendRow(item)

    def set_selected_items(self, select_list):
        self._block_signal = True
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            item.setCheckState(Qt.CheckState.Checked if item.text() in select_list else Qt.CheckState.Unchecked)
        self._block_signal = False
        self.update_text()

    def get_selected_items(self):
        res = []
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                res.append(item.text())
        return res

    def item_check_change(self, changed_item):
        if self._block_signal:
            return
        self._block_signal = True
        text = changed_item.text()
        checked = changed_item.checkState() == Qt.CheckState.Checked
        all_item = self.find_item_by_text("All")

        if text == "All" and checked:
            for row in range(self.model.rowCount()):
                it = self.model.item(row)
                if it.text() != "All":
                    it.setCheckState(Qt.CheckState.Unchecked)
        elif text != "All" and checked and all_item:
            all_item.setCheckState(Qt.CheckState.Unchecked)

        self._block_signal = False
        self.update_text()

    def find_item_by_text(self, target):
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item.text() == target:
                return item
        return None

    def update_text(self):
        selected = self.get_selected_items()
        self.line_edit.setText(",".join(selected))