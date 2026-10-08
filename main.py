
import sys
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QDialog,
    QFrame, QDateTimeEdit, QDateEdit, QTimeEdit, QComboBox, QCheckBox,
    QSpinBox, QRadioButton, QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, QDateTime, QDate, QTime, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from calendarr import CalendarScrollArea
from model import Event
from storage import Storage
from utils import snap_to_grid, get_local_timezone
from recurrence_dialog import RecurrenceDialog
from styles import (
    LIGHT_THEME, DARK_THEME, 
    get_app_stylesheet, get_sidebar_stylesheet,
    get_right_panel_stylesheet,
    get_header_stylesheet,
    EVENT_COLORS
)

class ColorButton(QPushButton):
    def __init__(self, color_name, color_hex, parent=None):
        super().__init__(parent)
        self.color_name = color_name
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setProperty("active", "false")
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 2px solid transparent;
                border-radius: 12px;
            }}
            QPushButton:checked {{
                border: 2px solid #333;
            }}
            QPushButton:hover {{
                border: 2px solid #666;
            }}
        """)

class RightPanel(QFrame):
    def __init__(self, theme: dict, storage: Storage):
        super().__init__()
        self.theme = theme
        self.storage = storage
        self.setFixedWidth(300)
        self.setStyleSheet(get_right_panel_stylesheet(theme))
        
        self.current_event = None
        self.is_updating = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Event Details")
        header.setProperty("header", "true")
        layout.addWidget(header)
        
        self.form_widget = QWidget()
        form_layout = QVBoxLayout(self.form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Event Name")
        form_layout.addWidget(QLabel("Title"))
        form_layout.addWidget(self.name_input)
        
        # Colors
        color_container = QWidget()
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(8)
        
        self.color_group = []
        for name, data in EVENT_COLORS.items():
            btn = ColorButton(name, data['strip'])
            btn.clicked.connect(lambda checked, n=name: self._on_color_clicked(n))
            color_layout.addWidget(btn)
            self.color_group.append(btn)
            
        color_layout.addStretch()
        form_layout.addWidget(QLabel("Color"))
        form_layout.addWidget(color_container)
        
        # Time Grid Layout
        time_container = QWidget()
        time_layout = QVBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)
        
        # Start Row
        start_row = QWidget()
        start_layout = QHBoxLayout(start_row)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_layout.setSpacing(8)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        self.start_date.setSizePolicy(self.start_date.sizePolicy().horizontalPolicy(), self.start_date.sizePolicy().verticalPolicy())
        
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        
        start_layout.addWidget(QLabel("Start"))
        start_layout.addWidget(self.start_date, stretch=1)
        start_layout.addWidget(self.start_time)
        
        # End Row
        end_row = QWidget()
        end_layout = QHBoxLayout(end_row)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_layout.setSpacing(8)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        
        end_layout.addWidget(QLabel("End  ")) 
        end_layout.addWidget(self.end_date, stretch=1)
        end_layout.addWidget(self.end_time)
        
        time_layout.addWidget(start_row)
        time_layout.addWidget(end_row)
        
        form_layout.addWidget(time_container)
        
        # Recurrence
        recurrence_container = QWidget()
        rec_layout = QHBoxLayout(recurrence_container)
        rec_layout.setContentsMargins(0, 0, 0, 0)
        rec_layout.setSpacing(8)
        
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(["Does not repeat", "Daily", "Weekly", "Monthly", "Yearly", "Custom..."])
        self.recurrence_combo.activated.connect(self._on_recurrence_changed) # Use activated for user interaction check
        
        self.recurrence_end_date = QDateEdit()
        self.recurrence_end_date.setCalendarPopup(True)
        self.recurrence_end_date.setDisplayFormat("dd.MM.yyyy")
        self.recurrence_end_date.setSpecialValueText("Never ends")
        self.recurrence_end_date.setDate(QDate.currentDate().addYears(1)) # Default 1 year
        
        self.recurrence_end_check = QCheckBox("Ends on:")
        # self.recurrence_end_check.setChecked(False) # Default infinite
        
        rec_layout.addWidget(self.recurrence_combo, stretch=1)
        rec_layout.addWidget(self.recurrence_end_check)
        rec_layout.addWidget(self.recurrence_end_date, stretch=1)
        
        form_layout.addWidget(QLabel("Repeat"))
        form_layout.addWidget(recurrence_container)
        
        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description...")
        self.desc_input.setMaximumHeight(100)
        form_layout.addWidget(QLabel("Description"))
        form_layout.addWidget(self.desc_input)
        
        layout.addWidget(self.form_widget)
        layout.addStretch()
        
        # Delete Button
        self.delete_btn = QPushButton("Delete Event")
        self.delete_btn.setStyleSheet("color: #eb5757;")            
        layout.addWidget(self.delete_btn)
        
        # Empty State Overlay
        self.set_event(None)
        
    def _on_recurrence_changed(self, index):
        if self.is_updating: return
        
        # "Custom..." is at index 5
        if index == 5:
            # Open custom dialog
            if not self.current_event: return # Should have an event to edit
            
            # Start date from form or current event
            start = self.current_event.start_dt
            
            current_rule = self.current_event.recurrence_rule
            
            dlg = RecurrenceDialog(self, rule=current_rule, start_date=start)
            if dlg.exec():
                # Get rule from dialog
                # The dialog updates self.rule
                new_rule = dlg.rule
                self.current_event.recurrence = new_rule
                # We might want to set combo text to "Custom" or keep it there?
                # It is already selected.
                self.name_input.editingFinished.emit() # Trigger save
        else:
            # Standard preset
            # Just mapped in get_recurrence_info or handled here?
            # Standard behavior is to trigger save which calls get_recurrence_info
            self.name_input.editingFinished.emit()

    def _on_color_clicked(self, color_name):
        if self.is_updating: return
        
        for btn in self.color_group:
            btn.setChecked(btn.color_name == color_name)
            
        if self.current_event:
            self.current_event.color = color_name
            self.name_input.editingFinished.emit()

    def set_event(self, event: Event):
        self.is_updating = True
        self.current_event = event
        
        if event:
            self.form_widget.setVisible(True)
            self.delete_btn.setVisible(True)
            
            self.name_input.setText(event.name)
            self.desc_input.setText(event.description)
            
            # Select color
            current_color = getattr(event, 'color', 'blue')
            for btn in self.color_group:
                btn.setChecked(btn.color_name == current_color)
            
            # Recurrence
            rec = event.recurrence
            idx = 0
            if isinstance(rec, str):
                rec_map = {None: 0, 'daily': 1, 'weekly': 2, 'monthly': 3, 'yearly': 4}
                idx = rec_map.get(rec, 0)
            elif isinstance(rec, dict):
                 # It's custom
                 idx = 5
            
            self.recurrence_combo.setCurrentIndex(idx)
            
            if event.recurrence_end:
                 self.recurrence_end_check.setChecked(True)
                 self.recurrence_end_date.setDate(event.recurrence_end.date())
                 self.recurrence_end_date.setEnabled(True)
            else:
                 self.recurrence_end_check.setChecked(False)
                 self.recurrence_end_date.setEnabled(False)

            # Timezone handling
            tz = get_local_timezone()
            start = event.start_dt if event.start_dt.tzinfo else event.start_dt.replace(tzinfo=tz)
            end = event.end_dt if event.end_dt.tzinfo else event.end_dt.replace(tzinfo=tz)
            
            start = start.astimezone(tz)
            end = end.astimezone(tz)
            
            self.start_date.setDate(start.date())
            self.start_time.setTime(start.time())
            
            self.end_date.setDate(end.date())
            self.end_time.setTime(end.time())
        else:
            self.form_widget.setVisible(False)
            self.delete_btn.setVisible(False)
            
        self.is_updating = False
        
    def get_recurrence_info(self):
        idx = self.recurrence_combo.currentIndex()
        
        if idx == 5:
            # Custom: already stored in event.recurrence if dialog was used?
            # Or we return what is in event.recurrence?
            # Issue: 'on_panel_edited' overwrites event properties from UI components.
            # If we select Custom, we want to keep the existing dict.
            if self.current_event and isinstance(self.current_event.recurrence, dict):
                recurrence = self.current_event.recurrence
            else:
                # Fallback if somehow Custom is selected but no dict exists
                recurrence = {'freq': 'weekly', 'interval': 1}
        else:
            rec_map = {0: None, 1: 'daily', 2: 'weekly', 3: 'monthly', 4: 'yearly'}
            recurrence = rec_map.get(idx)
        
        recurrence_end = None
        if recurrence and self.recurrence_end_check.isChecked():
            d = self.recurrence_end_date.date().toPython()
            recurrence_end = datetime.combine(d, datetime.min.time()).replace(tzinfo=get_local_timezone())
            
        return recurrence, recurrence_end

    def update_theme(self, theme: dict):
        self.theme = theme
        self.setStyleSheet(get_right_panel_stylesheet(theme))

class CalendarHeader(QWidget):
    def __init__(self, theme: dict):
        super().__init__()
        self.theme = theme
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.update_date_label()
        layout.addWidget(self.date_label)
        
        layout.addStretch()
        
        self.days_combo = QComboBox()
        self.days_combo.addItems(["1 Day", "3 Days", "7 Days"])
        self.days_combo.setCurrentIndex(2)                 
        layout.addWidget(self.days_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        layout.addWidget(self.theme_combo)
        
        self.today_btn = QPushButton("Today")
        layout.addWidget(self.today_btn)
        
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(40)
        layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(40)
        layout.addWidget(self.next_btn)
        
        self.setAutoFillBackground(True)
        self.update_theme(theme)
    
    def update_date_label(self, date: datetime = None):
        if date is None:
            date = datetime.now()
        self.date_label.setText(date.strftime("%B %Y"))
        
    def update_theme(self, theme: dict):
        self.theme = theme
        self.setStyleSheet(get_header_stylesheet(theme))
        
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(theme['header_bg']))
        self.setPalette(p)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Calendar")
        self.setGeometry(100, 100, 1400, 900)
        
        self.current_theme = LIGHT_THEME
        self.storage = Storage()
        
        central_container = QWidget()
        self.setCentralWidget(central_container)
        main_layout = QHBoxLayout(central_container)
        s = 3
        main_layout.setContentsMargins(s, s, s, s)
        main_layout.setSpacing(10)
        
        # Calendar Area (Left/Main)
        self.calendar_container = QWidget()
        cal_layout = QVBoxLayout(self.calendar_container)
        cal_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.setSpacing(0)
        
        self.header = CalendarHeader(self.current_theme)
        cal_layout.addWidget(self.header)
        
        self.calendar_scroll = CalendarScrollArea(num_days=7, theme=self.current_theme)
        self.calendar = self.calendar_scroll.calendar_grid
        self.calendar_scroll.setStyleSheet("border-radius: 6px;")
        cal_layout.addWidget(self.calendar_scroll)
        
        main_layout.addWidget(self.calendar_container, stretch=1)
        
        # Right Panel (Details)
        self.right_panel = RightPanel(self.current_theme, self.storage)
        main_layout.addWidget(self.right_panel)
        
        # Signals
        self.header.today_btn.clicked.connect(self.on_today_clicked)
        self.header.prev_btn.clicked.connect(self.on_prev_clicked)
        self.header.next_btn.clicked.connect(self.on_next_clicked)
        self.header.days_combo.currentIndexChanged.connect(self.on_days_changed)
        self.header.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        self.calendar.event_created.connect(self.on_event_created)
        self.calendar.event_moved.connect(self.on_event_moved)
        self.calendar.event_resized.connect(self.on_event_resized)
        self.calendar.event_clicked.connect(self.on_event_clicked)
        
        self.right_panel.name_input.editingFinished.connect(self.on_panel_edited)
        self.right_panel.desc_input.textChanged.connect(self.on_panel_edited)
        
        self.right_panel.start_date.dateChanged.connect(self.on_panel_edited)
        self.right_panel.start_time.timeChanged.connect(self.on_panel_edited)
        self.right_panel.end_date.dateChanged.connect(self.on_panel_edited)
        self.right_panel.end_time.timeChanged.connect(self.on_panel_edited)
        
        self.right_panel.recurrence_combo.currentIndexChanged.connect(self.on_panel_edited)
        self.right_panel.recurrence_end_check.toggled.connect(self.on_rec_end_toggled)
        self.right_panel.recurrence_end_date.dateChanged.connect(self.on_panel_edited)
        
        self.right_panel.delete_btn.clicked.connect(self.on_delete_event)
        
        self.apply_theme()
        self.load_events()
        
    def apply_theme(self):
        self.setStyleSheet(get_app_stylesheet(self.current_theme))
        self.calendar.set_theme(self.current_theme)
        self.right_panel.update_theme(self.current_theme)
        self.header.update_theme(self.current_theme)
    
    def on_theme_changed(self, index: int):
        self.current_theme = DARK_THEME if index == 1 else LIGHT_THEME
        self.apply_theme()

    def on_rec_end_toggled(self, checked):
        self.right_panel.recurrence_end_date.setEnabled(checked)
        self.on_panel_edited()
    
    def on_days_changed(self, index: int):
        days_map = {0: 1, 1: 3, 2: 7}
        num_days = days_map.get(index, 7)
        self.calendar.set_num_days(num_days)
    
    def on_today_clicked(self):
        self.calendar.go_to_today()
        self.header.update_date_label(self.calendar.reference_date)
        self.load_events() # Reload for dynamic recurrence
    
    def on_prev_clicked(self):
        self.calendar.go_previous()
        self.header.update_date_label(self.calendar.reference_date)
        self.load_events()
    
    def on_next_clicked(self):
        self.calendar.go_next()
        self.header.update_date_label(self.calendar.reference_date)
        self.load_events()
    
    def load_events(self):
        if not self.calendar.days:
            return
            
        start_range = self.calendar.days[0]
        end_range = start_range + timedelta(days=self.calendar.num_days + 7) # Extra buffer
        
        events = self.storage.load_events(start_range, end_range)
        self.calendar.set_events(events)
    
    def on_event_created(self, start_dt: datetime, end_dt: datetime):
        tz = get_local_timezone()
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=tz)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=tz)
            
        event = Event(
            start_dt=start_dt,
            end_dt=end_dt,
            name="New Event",
            description=""
        )
        self.storage.save_event(event)
        self.load_events()
        # Find the newly created event (might need ID fetch improvement but simple load works for now)
        # Using the event object directly has ID now because logic updates it in-place usually?
        # Actually storage.save_event updates event.id
        self.right_panel.set_event(event)                                            
    
    def on_event_moved(self, event_id: int, new_start_dt: datetime):
        # NOTE: Moving a recurring instance moves the WHOLE series in this simple implementation
        # OR we should ask user. For MVP, we treat drag-drop as editing the 'root' event if ID matches
        event = self.storage.get_event_by_id(event_id)
        if event:
            event.move_to(new_start_dt)
            self.storage.save_event(event)
            self.load_events()
            if self.right_panel.current_event and self.right_panel.current_event.id == event.id:
                self.right_panel.set_event(event)
    
    def on_event_resized(self, event_id: int, new_end_dt: datetime):
        event = self.storage.get_event_by_id(event_id)
        if event:
            try:
                event.resize_to(new_end_dt)
                self.storage.save_event(event)
                self.load_events()
                if self.right_panel.current_event and self.right_panel.current_event.id == event.id:
                    self.right_panel.set_event(event)
            except ValueError:
                pass
    
    def on_event_clicked(self, event_id: int):
        # We need to find the event.
        # If it's a virtual instance, get_event_by_id returns the PARENT.
        # This is expected behavior for "Edit Series" mode.
        event = self.storage.get_event_by_id(event_id)
        if event:
            self.right_panel.set_event(event)
            
    def on_panel_edited(self):
        if self.right_panel.is_updating or not self.right_panel.current_event:
            return
            
        event = self.right_panel.current_event
        
        new_name = self.right_panel.name_input.text()
        new_desc = self.right_panel.desc_input.toPlainText()
        
        s_date = self.right_panel.start_date.date().toPython()
        s_time = self.right_panel.start_time.time().toPython()
        
        e_date = self.right_panel.end_date.date().toPython()
        e_time = self.right_panel.end_time.time().toPython()
        
        start_naive = datetime.combine(s_date, s_time)
        end_naive = datetime.combine(e_date, e_time)
        
        tz = get_local_timezone()
        start_dt = start_naive.replace(tzinfo=tz)
        end_dt = end_naive.replace(tzinfo=tz)
        
        if start_dt >= end_dt:
            end_dt = start_dt + timedelta(minutes=15)
        
        recurrence, recurrence_end = self.right_panel.get_recurrence_info()

        event.name = new_name
        event.description = new_desc
        event.start_dt = start_dt
        event.end_dt = end_dt
        event.recurrence = recurrence
        event.recurrence_end = recurrence_end
        
        self.handle_recurring_edit(event, start_dt, end_dt)

    def handle_recurring_edit(self, event, start_dt, end_dt):
        # Logic to handle recurring event edits
        # If it's a recurring event (or instance), we need to check if we are splitting
        
        # Check if this object was an instance (has original_start)
        original_start = getattr(event, 'original_start', None)
        
        if original_start and event.recurrence:
            # It is an instance of a recurring event
            # For this MVP, we will auto-split if the date changed significantly or if requested.
            # But wait, 'event' here is the object from RightPanel.
            # If we clicked an instance, set_event passed that instance.
            # So 'event' is the instance.
            
            # Since we can't easily show a popup in this headless mode (though the user would see it),
            # I will implement the logic as if "This event only" was chosen for date changes,
            # unless we implement the popup.
            # Let's try to add the popup code. It will run on user's machine.
            
            from PySide6.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self, 
                "Recurring Event", 
                "Do you want to edit only this event or the whole series?",
                QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            )
            # Yes = This event only (StandardButton.Yes is just a placeholder here, let's use custom text but standard buttons are limited)
            # Actually let's use a custom dialog or just standard buttons:
            # Yes -> This event only
            # Apply -> All events (Series)
            # Cancel -> Cancel
            
            # BETTER: Custom Dialog for clarity
            msg = QMessageBox(self)
            msg.setWindowTitle("Edit Recurring Event")
            msg.setText("This is a recurring event.")
            msg.setInformativeText("Which events do you want to change?")
            btn_this = msg.addButton("This Event Only", QMessageBox.ButtonRole.ActionRole)
            btn_all = msg.addButton("All Events", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Cancel)
            
            msg.exec()
            
            if msg.clickedButton() == btn_this:
                # "This Event Only"
                # 1. Fetch original parent to add exception
                parent = self.storage.get_event_by_id(event.id)
                if parent:
                    exceptions = parent.meta.get('exceptions', [])
                    exceptions.append(original_start.strftime("%Y-%m-%d"))
                    parent.meta['exceptions'] = exceptions
                    self.storage.save_event(parent)
                    
                # 2. Create new independent event
                new_event = Event(
                    start_dt=event.start_dt,
                    end_dt=event.end_dt,
                    name=event.name,
                    description=event.description,
                    color=event.color,
                    meta=event.meta, # Copy meta? Maybe clear exceptions
                    recurrence=None,
                    recurrence_end=None
                )
                # Cleanup meta for new event
                if 'exceptions' in new_event.meta:
                    del new_event.meta['exceptions']
                    
                self.storage.save_event(new_event)
                
            elif msg.clickedButton() == btn_all:
                # "All Events"
                # Update the parent event
                # We need to update the parent with the new attributes (name, desc, color, recurrence)
                # But careful about dates. If user moved 1 instance by 1 hour, does it mean shift all by 1 hour?
                # Or set all to that new time?
                # Standard behavior: Update series attributes. If time changed, usually shifts the pattern?
                # For simplified logic: We update the parent's generic attributes.
                # If start_time changed, we update parent start_time.
                # This shifts the whole series to start from this new time (on the first day).
                # Wait, if I move the 3rd instance to 5pm, and parent started at 9am,
                # if I update parent start to 5pm, the 1st instance (past) also moves.
                # This is "Edit Series".
                
                # To properly support "All events" from an instance, we usually update the parent.
                parent = self.storage.get_event_by_id(event.id)
                if parent:
                    parent.name = event.name
                    parent.description = event.description
                    parent.color = event.color
                    parent.recurrence = event.recurrence
                    parent.recurrence_end = event.recurrence_end
                    
                    # Date handling for series edit is complex.
                    # For MVP: We just save the parent. 
                    # If the user edited the 'start_date' in the form, 
                    # it might be the date of the *instance*.
                    # We shouldn't set parent.start_dt to instance.start_dt (that would move the whole series to start on that instance's date).
                    # We should only update the TIME if changed, or Duration.
                    # This is getting complex for MVP.
                    
                    # Simplification: "All events" edits name/desc/color/recurrence. 
                    # Date changes on an instance in "All events" mode -> Ignored or applied to parent?
                    # Let's apply valid updates.
                    self.storage.save_event(parent)
            else:
                return # Cancelled
            
        else:
            # Normal event or Parent event directly
            # Just save
            self.storage.save_event(event)
            
        self.load_events()
        
    def on_delete_event(self):
        if self.right_panel.current_event:
            self.storage.delete_event(self.right_panel.current_event.id)
            self.right_panel.set_event(None)
            self.load_events()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()