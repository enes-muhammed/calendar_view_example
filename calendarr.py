
from PySide6.QtWidgets import QWidget, QScrollArea
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent, QPainterPath
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from model import Event, EventBox
from utils import (
    snap_to_grid, get_day_start, get_day_end, get_week_days,
    pixels_to_minutes, minutes_to_pixels, SNAP_STEP_MINUTES,
    get_local_timezone)
from styles import EVENT_COLORS

PIXELS_PER_MINUTE = 1.5                        
HOUR_HEIGHT = int(60 * PIXELS_PER_MINUTE)            
TIME_COLUMN_WIDTH = 60
HEADER_HEIGHT = 36                
OCLOCK_X = 25


class CalendarGrid(QWidget):
    
    event_created = Signal(datetime, datetime)
    event_moved = Signal(int, datetime)                          
    event_resized = Signal(int, datetime)                        
    event_clicked = Signal(int)            
    
    def __init__(self, num_days: int = 7, theme: dict = None):
        super().__init__()
        self.num_days = num_days
        self.theme = theme or {}
        self.events: List[Event] = []
        self.event_boxes: List[EventBox] = []
        self.day_column_width = 180                                              
        
                               
        tz = get_local_timezone()
        self.reference_date = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        self.days = get_week_days(self.reference_date, num_days)
        
                           
        self.dragging_box: Optional[EventBox] = None
        self.drag_start_pos: Optional[QPoint] = None
        self.drag_mode: str = "none"                              
        self.creating_start_dt: Optional[datetime] = None
        self.creating_end_dt: Optional[datetime] = None
        self.creating_rect: Optional[QRect] = None
        
                     
        self.hover_box: Optional[EventBox] = None
        
        self.setMouseTracking(True)
        self.update_size()
    
    def set_theme(self, theme: dict):
                           
        self.theme = theme
        self.update()
    
    def set_num_days(self, num_days: int):
                                   
        self.num_days = min(num_days, 9)             
        self.days = get_week_days(self.reference_date, self.num_days)
        self.render_events()
        self.update_size()
        self.update()
    
    def set_reference_date(self, date: datetime):
                                                   
        self.reference_date = get_day_start(date)
        self.days = get_week_days(self.reference_date, self.num_days)
        self.render_events()
        self.update()
    
    def go_to_today(self):
                        
        self.set_reference_date(datetime.now(get_local_timezone()))
    
    def go_previous(self):
                                 
        self.set_reference_date(self.reference_date - timedelta(days=self.num_days))
    
    def go_next(self):
                                  
        self.set_reference_date(self.reference_date + timedelta(days=self.num_days))
    
    def update_size(self):
                                     
                                                
        if self.parent() and hasattr(self.parent(), 'viewport'):
            available_width = self.parent().viewport().width()
        elif self.parent():
            available_width = self.parent().width()
        else:
            available_width = 1200
        
                                               
        self.day_column_width = max((available_width - TIME_COLUMN_WIDTH) // self.num_days, 100)
        
        width = TIME_COLUMN_WIDTH + (self.day_column_width * self.num_days)
        height = HEADER_HEIGHT + (24 * HOUR_HEIGHT)           
        self.setMinimumSize(width, height)
    
    def resizeEvent(self, event):
                                                                         
        super().resizeEvent(event)
        self.update_size()
        self.update()
    
    def set_events(self, events: List[Event]):



           
        self.events = events
        self.render_events()
        self.update()
    
    def render_events(self):


           
        self.event_boxes = []
        
        for day_idx, day_start in enumerate(self.days):
            day_end = get_day_end(day_start)
            
            for event in self.events:
                if event.intersects(day_start, day_end):
                                           
                    visible_start = max(event.start_dt, day_start)
                    visible_end = min(event.end_dt, day_end)
                    
                    box = EventBox(event, visible_start, visible_end)
                    self.event_boxes.append(box)
    
    def paintEvent(self, event):
                                       
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self._draw_background(painter)
        self._draw_time_grid(painter)
        self._draw_day_headers(painter)
        self._draw_event_boxes(painter)
        
                          
        if self.creating_rect:
                                                
            bg_color = self.theme.get('creating_bg', 'rgba(150, 200, 255, 127)')
            painter.setBrush(QColor(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.creating_rect, 4, 4)
    
    def _draw_background(self, painter: QPainter):
                       
        bg_color = self.theme.get('calendar_bg', '#ffffff')
        painter.fillRect(self.rect(), QColor(bg_color))
    
    def _draw_time_grid(self, painter: QPainter):
                                          
        painter.setFont(QFont("Arial", 9))
        time_text_color = self.theme.get('time_text', '#666666')
        grid_line_color = self.theme.get('grid_line', '#e5e5e5')
        grid_line_hour_color = self.theme.get('grid_line_hour', '#d0d0d0')
        
        for hour in range(24):
            y = HEADER_HEIGHT + (hour * HOUR_HEIGHT)

            painter.setPen(QPen(QColor(grid_line_hour_color), 1))
            painter.drawLine(TIME_COLUMN_WIDTH, y, self.width(), y)
                                             
            painter.setFont(QFont("Helvetica", 7))
            painter.setPen(QColor(time_text_color), )
            am_or_pm = "AM" if hour < 12 else "PM"
            time_text = f"{hour % 12} {am_or_pm}"
            painter.drawText(OCLOCK_X, y+5, time_text)
            
                                      
        for day_idx in range(self.num_days + 1):
            x = TIME_COLUMN_WIDTH + (day_idx * self.day_column_width)
            painter.setPen(QPen(QColor(grid_line_color), 0))
            painter.drawLine(x, HEADER_HEIGHT, x, self.height())
    
    def _draw_day_headers(self, painter: QPainter):
                                                           
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        day_header_color = self.theme.get('day_header_text', '#000000')
        today_bg_color = self.theme.get('today_bg', 'rgb(255, 59, 48)')
        today_text_color = self.theme.get('today_text', '#ffffff')
        
        tz = get_local_timezone()
        today = get_day_start(datetime.now(tz))
        
        for day_idx, day_dt in enumerate(self.days):
            x = TIME_COLUMN_WIDTH + (day_idx * self.day_column_width)                          
            day_name = day_dt.strftime("%a %d")
            is_today = (get_day_start(day_dt) == today)
            
            if is_today:
                                                                    
                padding = 8
                text_width = painter.fontMetrics().horizontalAdvance(day_name)
                rect_width = text_width + (padding * 2)
                rect_height = 28
                rect_x = x + (self.day_column_width - rect_width) // 2
                rect_y = (HEADER_HEIGHT - rect_height) // 2
                
                painter.setBrush(QColor(today_bg_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect_x+1, rect_y+4, rect_width-2, rect_height-8, 6, 6)
                
                            
                painter.setPen(QColor(today_text_color))
            else:
                painter.setPen(QColor(day_header_color))
            
                              
            text_rect = QRect(x, 10, self.day_column_width, HEADER_HEIGHT - 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, day_name)
    
    def _draw_event_boxes(self, painter: QPainter):
                               
        for box in self.event_boxes:
            rect = self._get_box_rect(box)
            if not rect:
                continue
            
            event_color_name = getattr(box.event, 'color', 'blue')
                                                 
            colors = EVENT_COLORS.get(event_color_name, EVENT_COLORS['blue'])
            
            is_hover = box == self.hover_box
            is_dragging = box == self.dragging_box
            
            strip_color = QColor(colors['strip'])
                   
            bg_color = QColor(strip_color)
            bg_color.setAlpha(40)               

            if is_dragging:
                bg_color.setAlpha(100)
            elif is_hover:
                bg_color.setAlpha(80)
            
            text_color_hex = colors.get('text', '#37352f')
            text_color = QColor(text_color_hex)
            
            painter.setBrush(bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
                                              
            painter.save()
            path = QPainterPath()
            path.addRoundedRect(rect, 4, 4)
            painter.setClipPath(path)
            
            painter.drawRect(rect)
            strip_rect = QRect(rect.x(), rect.y(), 4, rect.height())
            painter.fillRect(strip_rect, strip_color)
            
            painter.restore()
             
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                    
            text_rect = rect.adjusted(8, 3, -5, -3)
            
            display_text = box.event.name
            if getattr(box.event, 'recurrence', None):
                display_text = "🔁 " + display_text
                
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, display_text)
    
    def _get_box_rect(self, box: EventBox) -> Optional[QRect]:
                                         
                              
        day_start = get_day_start(box.visible_start)
        if day_start not in self.days:
            return None
        
        day_idx = self.days.index(day_start)
        
                     
        x = TIME_COLUMN_WIDTH + (day_idx * self.day_column_width) + 5
        width = self.day_column_width - 10
        
                                        
        start_minutes = box.visible_start.hour * 60 + box.visible_start.minute
        y = HEADER_HEIGHT + minutes_to_pixels(start_minutes, PIXELS_PER_MINUTE)
        
                   
        height = minutes_to_pixels(box.duration_minutes, PIXELS_PER_MINUTE)
        height = max(height, 20)                     
        
        return QRect(int(x), int(y), int(width), int(height))
    


    def mouseMoveEvent(self, event: QMouseEvent):
                                                 
        pos = event.pos()
        
        if self.drag_mode == "move" and self.dragging_box:
            self._handle_move_drag(pos)
        elif self.drag_mode == "resize" and self.dragging_box:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self._handle_resize_drag(pos)
        elif self.drag_mode == "create" and self.creating_start_dt:
            self._handle_create_drag(pos)
        else:
                                                      
            self.hover_box = self._get_box_at_pos(pos)
            if self.hover_box:
                rect = self._get_box_rect(self.hover_box)
                if rect and self._is_resize_handle(pos, rect):
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
                                        
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        if self.drag_mode == "move" and self.dragging_box:
            self._finalize_move()
        elif self.drag_mode == "resize" and self.dragging_box:
            self._finalize_resize()
        elif self.drag_mode == "create" and self.creating_start_dt:
            self._finalize_create(event.pos())
        
        self.drag_mode = "none"
        self.dragging_box = None
        self.drag_start_pos = None
        self._drag_offset_minutes = None                
        self.creating_start_dt = None
        self.creating_end_dt = None
        self.creating_rect = None
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
                                                                    
        if event.button() != Qt.MouseButton.LeftButton:
            return
        else:
            pos = event.pos()
            clicked_box = self._get_box_at_pos(pos)
        
        if clicked_box:
                                                     
            self.event_clicked.emit(clicked_box.event.id)
            
            rect = self._get_box_rect(clicked_box)
            if self._is_resize_handle(pos, rect):
                self.drag_mode = "resize"
                self.dragging_box = clicked_box
                self.drag_start_pos = pos
            else:
                             
                self.drag_mode = "move"
                self.dragging_box = clicked_box
                self.drag_start_pos = pos
        else:
                                                     
            dt = self._pos_to_datetime(pos)
            if dt:
                self.drag_mode = "create"
                self.creating_start_dt = snap_to_grid(dt)
                self.creating_end_dt = self.creating_start_dt
                self.drag_start_pos = pos
    
    def _handle_move_drag(self, pos: QPoint):
                                      
        if not self.dragging_box:
            return
            
                                                                             
        if not hasattr(self, "_drag_offset_minutes") or self._drag_offset_minutes is None:
                                       
            cursor_dt = self._pos_to_datetime(self.drag_start_pos)
            if not cursor_dt: 
                return
            
                                       
            event_start = self.dragging_box.event.start_dt
            
                                   
                                                                          
            diff = cursor_dt - event_start
            self._drag_offset_minutes = diff.total_seconds() / 60
            
                                              
        current_cursor_dt = self._pos_to_datetime(pos)
        if not current_cursor_dt:
            return
            
                                                           
                                             
        new_start_raw = current_cursor_dt - timedelta(minutes=self._drag_offset_minutes)
        
                     
        new_start = snap_to_grid(new_start_raw)
        
                                                 
        duration = self.dragging_box.event.duration
        self.dragging_box.event.start_dt = new_start
        self.dragging_box.event.end_dt = new_start + duration
        
        self.render_events()
        self.update()
    
    def _handle_resize_drag(self, pos: QPoint):
        self.setCursor(Qt.SizeVerCursor)
                                      
        if not self.dragging_box:
            return
        
        rect = self._get_box_rect(self.dragging_box)
        if not rect:
            return
        
                        
        new_height = pos.y() - rect.top()
        new_minutes = pixels_to_minutes(new_height, PIXELS_PER_MINUTE)
        new_minutes = max(SNAP_STEP_MINUTES, round(new_minutes / SNAP_STEP_MINUTES) * SNAP_STEP_MINUTES)
        
                     
        new_end = self.dragging_box.event.start_dt + timedelta(minutes=new_minutes)
        self.dragging_box.event.end_dt = new_end
        
        self.render_events()
        self.update()
    
    def _handle_create_drag(self, pos: QPoint):
                                              
        if not self.creating_start_dt:
            return
        
        end_dt = self._pos_to_datetime(pos)
        if not end_dt:
            return
        
        end_dt = snap_to_grid(end_dt)
        
        
        self.creating_end_dt = end_dt
        
                         
        day_start = get_day_start(self.creating_start_dt)
        if day_start not in self.days:
            return
            
        day_idx = self.days.index(day_start)
        x = TIME_COLUMN_WIDTH + (day_idx * self.day_column_width) + 5
        width = self.day_column_width - 10
        
        start_minutes = self.creating_start_dt.hour * 60 + self.creating_start_dt.minute
        end_minutes = end_dt.hour * 60 + end_dt.minute
        
        y1 = HEADER_HEIGHT + minutes_to_pixels(start_minutes, PIXELS_PER_MINUTE)
        y2 = HEADER_HEIGHT + minutes_to_pixels(end_minutes, PIXELS_PER_MINUTE)
        
        self.creating_rect = QRect(int(x), int(y1), int(width), int(y2 - y1))
        self.update()
    
    def _finalize_move(self):
                                       
        if self.dragging_box:
            self.event_moved.emit(self.dragging_box.event.id, self.dragging_box.event.start_dt)
    
    def _finalize_resize(self):
                                       
        if self.dragging_box:
            self.event_resized.emit(self.dragging_box.event.id, self.dragging_box.event.end_dt)
    
    def _finalize_create(self, pos: QPoint):
                                              
        if not self.creating_start_dt or not self.creating_end_dt:
            return
        
                                                     
        if self.creating_end_dt == self.creating_start_dt:
            self.creating_start_dt = None
            self.creating_end_dt = None
            self.creating_rect = None
            self.update()
            return
            
                                                          
        if self.creating_end_dt < self.creating_start_dt:
            self.creating_start_dt, self.creating_end_dt = self.creating_end_dt, self.creating_start_dt
        
        self.event_created.emit(self.creating_start_dt, self.creating_end_dt)
    
    def _get_box_at_pos(self, pos: QPoint) -> Optional[EventBox]:
                                         
        for box in reversed(self.event_boxes):
            rect = self._get_box_rect(box)
            if rect and rect.contains(pos):
                return box
        return None
    
    def _is_resize_handle(self, pos: QPoint, rect: QRect) -> bool:
                                             
        if not rect:
            return False
        return abs(pos.y() - rect.bottom()) < 10
    
    def _pos_to_datetime(self, pos: QPoint) -> Optional[datetime]:
                                                
                    
        day_idx = (pos.x() - TIME_COLUMN_WIDTH) // self.day_column_width
        if day_idx < 0 or day_idx >= len(self.days):
            return None
        
        day_dt = self.days[day_idx]
        
                
        minutes = pixels_to_minutes(pos.y() - HEADER_HEIGHT, PIXELS_PER_MINUTE)
        minutes = max(0, min(24 * 60 - 1, minutes))
        
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        
        return day_dt.replace(hour=hours, minute=mins, second=0, microsecond=0)


class CalendarScrollArea(QScrollArea):
                                                            
    
    def __init__(self, num_days: int = 7, theme: dict = None):
        super().__init__()
        self.calendar_grid = CalendarGrid(num_days, theme)
        self.setWidget(self.calendar_grid)
        self.setWidgetResizable(True)                                 
        
                              
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def resizeEvent(self, event):
                                                      
        super().resizeEvent(event)
        if self.calendar_grid:
            self.calendar_grid.update_size()