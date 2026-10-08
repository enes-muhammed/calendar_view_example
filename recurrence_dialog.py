
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QSpinBox, QPushButton, QRadioButton, QButtonGroup, 
    QCheckBox, QDateEdit, QWidget, QFrame
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

class RecurrenceDialog(QDialog):
    def __init__(self, parent=None, rule=None, start_date=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Recurrence")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; border-radius: 8px; }
            QLabel { color: #37352f; font-size: 14px; }
            QComboBox, QSpinBox, QDateEdit { 
                padding: 5px; border: 1px solid #e1e1e0; border-radius: 4px; 
            }
            QPushButton { 
                padding: 6px 12px; border-radius: 4px; 
            }
        """)
        
        self.rule = rule or {}
        self.start_date = start_date or datetime.now()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        layout.addWidget(QLabel("Repeat every"))
        
        # Frequency and Interval
        freq_row = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 999)
        self.interval_spin.setValue(self.rule.get('interval', 1))
        
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["day", "week", "month", "year"])
        freq_map = {'daily': 0, 'weekly': 1, 'monthly': 2, 'yearly': 3}
        self.freq_combo.setCurrentIndex(freq_map.get(self.rule.get('freq', 'weekly'), 1))
        
        freq_row.addWidget(self.interval_spin)
        freq_row.addWidget(self.freq_combo)
        layout.addLayout(freq_row)
        
        # Weekdays (visible only if weekly)
        self.weekdays_container = QWidget()
        wd_layout = QVBoxLayout(self.weekdays_container)
        wd_layout.setContentsMargins(0, 0, 0, 0)
        wd_layout.addWidget(QLabel("On"))
        
        days_row = QHBoxLayout()
        days_row.setSpacing(4)
        self.day_buttons = []
        labels = ["M", "T", "W", "T", "F", "S", "S"]
        keys = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        
        current_byday = self.rule.get('by_day', [])
        
        for i, (label, key) in enumerate(zip(labels, keys)):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedSize(30, 30)
            btn.setProperty("day_key", key)
            btn.setProperty("day_idx", i)
            
            # Check if selected
            if key in current_byday or i in current_byday:
                btn.setChecked(True)
            
            # Helper logic: if new rule, select user's start day? 
            # Or default empty?
            # If no rule and freq is weekly, maybe preselect start_date weekday?
            if not current_byday and self.rule.get('freq') == 'weekly' and self.start_date.weekday() == i:
                 btn.setChecked(True)
            
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #f0f0f0; border: none; color: #37352f;
                }
                QPushButton:checked { 
                    background-color: #2e90dc; color: white; 
                }
            """)
            days_row.addWidget(btn)
            self.day_buttons.append(btn)
            
        wd_layout.addLayout(days_row)
        layout.addWidget(self.weekdays_container)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e1e1e0;")
        layout.addWidget(sep)
        
        # Ends
        layout.addWidget(QLabel("Ends"))
        
        self.end_group = QButtonGroup(self)
        
        # Never
        self.radio_never = QRadioButton("Never")
        self.end_group.addButton(self.radio_never)
        layout.addWidget(self.radio_never)
        
        # On Date
        date_row = QHBoxLayout()
        self.radio_date = QRadioButton("On")
        self.end_group.addButton(self.radio_date)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addMonths(1))
        if self.rule.get('until'):
            self.end_date_edit.setDate(self.rule['until'].date())
            self.radio_date.setChecked(True)
        else:
            self.radio_never.setChecked(True)
            self.end_date_edit.setEnabled(False)
            
        date_row.addWidget(self.radio_date)
        date_row.addWidget(self.end_date_edit)
        layout.addLayout(date_row)
        
        # After Count
        count_row = QHBoxLayout()
        self.radio_count = QRadioButton("After")
        self.end_group.addButton(self.radio_count)
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 999)
        if self.rule.get('count'):
            self.count_spin.setValue(self.rule['count'])
            self.radio_count.setChecked(True)
        else:
            self.count_spin.setEnabled(False)
            
        count_row.addWidget(self.radio_count)
        count_row.addWidget(self.count_spin)
        count_row.addWidget(QLabel("occurrences"))
        layout.addLayout(count_row)
        
        # Connect signals
        self.freq_combo.currentIndexChanged.connect(self._on_freq_changed)
        self.radio_never.toggled.connect(self._on_end_toggled)
        self.radio_date.toggled.connect(self._on_end_toggled)
        self.radio_count.toggled.connect(self._on_end_toggled)
        
        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background-color: #2e90dc; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.accept_rule)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        self._on_freq_changed() # visual update
        
    def _on_freq_changed(self):
        txt = self.freq_combo.currentText()
        if txt == 'week':
            self.weekdays_container.setVisible(True)
        else:
            self.weekdays_container.setVisible(False)
            
    def _on_end_toggled(self):
        self.end_date_edit.setEnabled(self.radio_date.isChecked())
        self.count_spin.setEnabled(self.radio_count.isChecked())
        
    def accept_rule(self):
        freq_map = {0: 'daily', 1: 'weekly', 2: 'monthly', 3: 'yearly'}
        freq = freq_map[self.freq_combo.currentIndex()]
        interval = self.interval_spin.value()
        
        new_rule = {
            'freq': freq,
            'interval': interval
        }
        
        if freq == 'weekly':
            selected_days = []
            for btn in self.day_buttons:
                if btn.isChecked():
                    selected_days.append(btn.property("day_key"))
            if selected_days:
                new_rule['by_day'] = selected_days
                
        if self.radio_date.isChecked():
            d = self.end_date_edit.date().toPython()
            new_rule['until'] = datetime(d.year, d.month, d.day, 23, 59, 59)
        elif self.radio_count.isChecked():
            new_rule['count'] = self.count_spin.value()
            
        self.rule = new_rule
        self.accept()
