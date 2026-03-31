from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QComboBox, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QCheckBox, QScrollArea, QFrame,
                             QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QKeySequence
import numpy as np

def clean_float(val_str):
    """Handle both dot and comma as decimal separator."""
    if not val_str:
        return np.nan
    try:
        # Replace comma with dot and remove any whitespace
        cleaned = val_str.replace(',', '.').strip()
        return float(cleaned)
    except ValueError:
        return np.nan

class GroupInputWidget(QGroupBox):
    removed = pyqtSignal()
    dataChanged = pyqtSignal()

    def __init__(self, group_name="Group", time_points=None, n_samples=5):
        super().__init__(group_name)
        self.time_points = time_points or [0, 15, 30, 60, 120]
        self.n_samples = n_samples
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Name, N-Adjustment and Remove
        header_layout = QHBoxLayout()
        self.name_edit = QLineEdit(self.title())
        self.name_edit.textChanged.connect(self.setTitle)
        
        self.n_spin = QSpinBox()
        self.n_spin.setRange(0, 100)
        self.n_spin.setValue(self.n_samples)
        self.n_spin.valueChanged.connect(self.update_n_samples)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setFixedWidth(60)
        self.remove_btn.clicked.connect(self.removed.emit)
        
        header_layout.addWidget(QLabel("Name:"))
        header_layout.addWidget(self.name_edit)
        header_layout.addWidget(QLabel("N:"))
        header_layout.addWidget(self.n_spin)
        header_layout.addStretch()
        header_layout.addWidget(self.remove_btn)
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget(0, len(self.time_points) + 1)
        self.update_headers()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.installEventFilter(self) # For paste
        layout.addWidget(self.table)

        # Initial rows
        for _ in range(self.n_samples):
            self.add_row()

        self.setLayout(layout)
        self.table.itemChanged.connect(self.on_item_changed)

    def eventFilter(self, source, event):
        if (event.type() == QKeyEvent.Type.KeyPress and 
            event.matches(QKeySequence.StandardKey.Paste)):
            self.paste_data()
            return True
        return super().eventFilter(source, event)

    def paste_data(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        rows = text.split('\n')
        curr_row = self.table.currentRow()
        curr_col = self.table.currentColumn()

        if curr_row < 0: curr_row = 0
        if curr_col < 1: curr_col = 1 # Don't paste into checkbox column

        for i, row_text in enumerate(rows):
            if not row_text.strip(): continue
            target_row = curr_row + i
            # Add rows if needed
            while target_row >= self.table.rowCount():
                self.add_row()
            
            cols = row_text.split('\t')
            for j, col_text in enumerate(cols):
                target_col = curr_col + j
                if target_col >= self.table.columnCount():
                    break
                
                item = self.table.item(target_row, target_col)
                if not item:
                    item = QTableWidgetItem()
                    self.table.setItem(target_row, target_col, item)
                item.setText(col_text.strip())
        
        self.n_spin.setValue(self.table.rowCount())
        self.dataChanged.emit()

    def update_n_samples(self, new_n):
        curr_n = self.table.rowCount()
        if new_n > curr_n:
            for _ in range(new_n - curr_n):
                self.add_row()
        elif new_n < curr_n:
            for _ in range(curr_n - new_n):
                self.table.removeRow(self.table.rowCount() - 1)
        self.dataChanged.emit()

    def update_headers(self):
        headers = ["Active"] + [f"{t} min" for t in self.time_points]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def add_row(self):
        row = self.table.rowCount()
        self.table.blockSignals(True)
        self.table.insertRow(row)
        
        # Active checkbox
        active_cb = QCheckBox()
        active_cb.setChecked(True)
        active_cb.stateChanged.connect(lambda: self.dataChanged.emit())
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.addWidget(active_cb)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, cell_widget)
        
        # Data cells
        for col in range(1, self.table.columnCount()):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)
        
        self.table.blockSignals(False)

    def set_time_points(self, time_points):
        self.time_points = time_points
        self.update_headers()
        # Ensure all rows have the right number of columns
        for row in range(self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                if not self.table.item(row, col):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, col, item)

    def on_item_changed(self, item):
        self.dataChanged.emit()

    def get_data(self):
        data = []
        for row in range(self.table.rowCount()):
            active_widget = self.table.cellWidget(row, 0)
            is_active = active_widget.findChild(QCheckBox).isChecked()
            
            values = []
            excluded = []
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                val_str = item.text() if item else ""
                val = clean_float(val_str)
                values.append(val)
                if np.isnan(val) and val_str.strip(): # Mark invalid numeric as excluded
                     excluded.append(col - 1)
                
                if item and item.background().color() == Qt.GlobalColor.lightGray:
                    if (col - 1) not in excluded:
                        excluded.append(col - 1)

            data.append({
                'is_active': is_active,
                'values': np.array(values),
                'excluded': excluded
            })
        return data

class InputPanel(QWidget):
    run_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.groups = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Top Settings
        settings_group = QGroupBox("Global Settings")
        settings_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(["GTT", "ITT"])
        row1.addWidget(QLabel("Test Type:"))
        row1.addWidget(self.test_type_combo)
        
        self.unit_edit = QLineEdit("mM Glucose")
        row1.addWidget(QLabel("Unit:"))
        row1.addWidget(self.unit_edit)
        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.time_points_edit = QLineEdit("0, 15, 30, 60, 120")
        self.time_points_edit.editingFinished.connect(self.update_time_points)
        row2.addWidget(QLabel("Time Points:"))
        row2.addWidget(self.time_points_edit)
        settings_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.n_groups_spin = QSpinBox()
        self.n_groups_spin.setRange(0, 20)
        self.n_groups_spin.setValue(2) # Default to 2 groups
        self.n_groups_spin.valueChanged.connect(self.sync_groups_count)
        row3.addWidget(QLabel("Groups:"))
        row3.addWidget(self.n_groups_spin)
        row3.addStretch()
        settings_layout.addLayout(row3)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Groups area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.groups_container = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.groups_container)
        layout.addWidget(self.scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_group_btn = QPushButton("Add Group Manually")
        self.add_group_btn.clicked.connect(lambda: self.add_group())
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.run_btn.clicked.connect(self.run_requested.emit)
        
        btn_layout.addWidget(self.add_group_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Initialize with 2 groups of N=6
        self.sync_groups_count(2)

    def sync_groups_count(self, count):
          curr = len(self.groups)
          if count > curr:
              for i in range(count - curr):
                  self.add_group(n_samples=6) # Default to 6 if added via count sync
          elif count < curr:
            for i in range(curr - count):
                self.remove_group(self.groups[-1])

    def update_time_points(self):
        try:
            tp_str = self.time_points_edit.text()
            tp = [float(x.strip()) for x in tp_str.split(',')]
            for g in self.groups:
                g.set_time_points(tp)
        except ValueError:
            pass

    def add_group(self, name=None, n_samples=None):
        tp_str = self.time_points_edit.text()
        try:
            tp = [float(x.strip()) for x in tp_str.split(',')]
        except:
            tp = [0, 15, 30, 60, 120]
            
        g_name = name or f"Group {len(self.groups) + 1}"
        n = n_samples if n_samples is not None else 6 # Default to 6
        
        g_widget = GroupInputWidget(g_name, tp, n)
        g_widget.removed.connect(lambda: self.remove_group(g_widget))
        self.groups_layout.addWidget(g_widget)
        self.groups.append(g_widget)
        # Update spinbox if added manually
        self.n_groups_spin.blockSignals(True)
        self.n_groups_spin.setValue(len(self.groups))
        self.n_groups_spin.blockSignals(False)

    def remove_group(self, widget):
        self.groups_layout.removeWidget(widget)
        if widget in self.groups:
            self.groups.remove(widget)
        widget.deleteLater()
        self.n_groups_spin.blockSignals(True)
        self.n_groups_spin.setValue(len(self.groups))
        self.n_groups_spin.blockSignals(False)

    def get_all_data(self):
        tp_str = self.time_points_edit.text()
        try:
            tp = np.array([float(x.strip()) for x in tp_str.split(',')])
        except:
            tp = np.array([0, 15, 30, 60, 120])
        
        all_data = {}
        for g in self.groups:
            all_data[g.title()] = g.get_data()
            
        return {
            'test_type': self.test_type_combo.currentText(),
            'unit': self.unit_edit.text(),
            'time_points': tp,
            'groups': all_data
        }
