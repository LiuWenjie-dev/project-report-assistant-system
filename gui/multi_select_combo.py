"""
多选下拉框控件
"""
from PyQt6.QtWidgets import (
    QComboBox, QListWidget, QListWidgetItem, QCheckBox, QLineEdit,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QFrame, QApplication, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QFontMetrics


class MultiSelectComboBox(QComboBox):
    """多选下拉框控件"""

    selection_changed = pyqtSignal(list)  # 选中项变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_items = []
        self.items = []

        # 设置可编辑，用于显示选中项
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("请选择...")

        # 创建列表部件
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        # 设置下拉框的弹出部件
        self.setModel(self.list_widget.model())
        self.setView(self.list_widget)

        # 连接信号
        self.list_widget.itemChanged.connect(self.on_item_changed)

    def addItems(self, items):
        """添加项目"""
        self.items = items
        self.list_widget.clear()

        for item in items:
            list_item = QListWidgetItem(self.list_widget)
            checkbox = QCheckBox(item)
            checkbox.setChecked(item in self.selected_items)
            self.list_widget.setItemWidget(list_item, checkbox)

            # 连接复选框状态变化信号
            checkbox.stateChanged.connect(
                lambda state, item=item, checkbox=checkbox:
                self.on_checkbox_state_changed(state, item, checkbox)
            )

    def addItem(self, text):
        """添加单个项目"""
        self.items.append(text)
        list_item = QListWidgetItem(self.list_widget)
        checkbox = QCheckBox(text)
        checkbox.setChecked(text in self.selected_items)
        self.list_widget.setItemWidget(list_item, checkbox)

        # 连接复选框状态变化信号
        checkbox.stateChanged.connect(
            lambda state, item=text, checkbox=checkbox:
            self.on_checkbox_state_changed(state, item, checkbox)
        )

    def setItems(self, items):
        """设置项目列表"""
        self.clear()
        self.addItems(items)

    def clear(self):
        """清空所有项目"""
        self.items = []
        self.selected_items = []
        self.list_widget.clear()
        self.update_display_text()

    def get_selected_items(self):
        """获取选中的项目"""
        return self.selected_items.copy()

    def set_selected_items(self, items):
        """设置选中的项目"""
        self.selected_items = items.copy()
        self.update_checkboxes()
        self.update_display_text()

    def on_checkbox_state_changed(self, state, item, checkbox):
        """复选框状态变化处理"""
        if state == Qt.CheckState.Checked.value:
            if item not in self.selected_items:
                self.selected_items.append(item)
        else:
            if item in self.selected_items:
                self.selected_items.remove(item)

        self.update_display_text()
        self.selection_changed.emit(self.selected_items)

    def on_item_changed(self, item):
        """列表项变化处理（备用）"""
        pass

    def update_checkboxes(self):
        """更新所有复选框的状态"""
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(list_item)
            if checkbox:
                checkbox.setChecked(checkbox.text() in self.selected_items)

    def update_display_text(self):
        """更新显示文本"""
        if not self.selected_items:
            self.lineEdit().setText("")
            self.lineEdit().setPlaceholderText("请选择...")
        elif len(self.selected_items) <= 3:
            self.lineEdit().setText(", ".join(self.selected_items))
        else:
            self.lineEdit().setText(f"已选择 {len(self.selected_items)} 项")

    def showPopup(self):
        """显示下拉框"""
        # 计算下拉框大小
        font_metrics = QFontMetrics(self.font())
        max_width = 0
        for item in self.items:
            width = font_metrics.horizontalAdvance(item) + 40  # 加上复选框和边距
            max_width = max(max_width, width)

        # 设置下拉框大小
        self.view().setMinimumWidth(max(max_width, self.width()))
        super().showPopup()

    def hidePopup(self):
        """隐藏下拉框"""
        # 延迟隐藏，避免点击复选框时立即关闭
        QApplication.instance().postEvent(
            self, QEvent(QEvent.Type.Close)
        )

    def event(self, event):
        """事件处理"""
        if event.type() == QEvent.Type.Close:
            # 处理关闭事件
            self.lineEdit().setFocus()
            return True
        return super().event(event)


class SimpleMultiSelectComboBox(QComboBox):
    """简化版多选下拉框（使用文本输入）"""

    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_items = []

        # 设置可编辑
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("可输入多个值，用逗号分隔")

        # 连接文本变化信号
        self.lineEdit().textChanged.connect(self.on_text_changed)

    def addItems(self, items):
        """添加项目"""
        super().addItems(items)

    def clear(self):
        """清空所有项目和输入文本"""
        super().clear()
        self.selected_items = []
        self.lineEdit().clear()

    def get_selected_items(self):
        """获取选中的项目"""
        text = self.lineEdit().text().strip()
        if not text:
            return []

        # 分割逗号分隔的值
        items = [item.strip() for item in text.split(',') if item.strip()]
        return items

    def set_selected_items(self, items):
        """设置选中的项目"""
        self.selected_items = items.copy()
        self.lineEdit().setText(", ".join(items))

    def on_text_changed(self, text):
        """文本变化处理"""
        items = self.get_selected_items()
        if items != self.selected_items:
            self.selected_items = items
            self.selection_changed.emit(items)
