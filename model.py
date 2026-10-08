
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union


class Event:
    _id_counter = 1
    
    def __init__(
        self,
        start_dt: datetime,
        end_dt: datetime,
        name: str,
        description: str = "",
        color: str = "blue",
        meta: Optional[Dict[str, Any]] = None,
        event_id: Optional[int] = None,
        recurrence: Optional[Union[str, Dict]] = None, # 'daily' or {'freq': 'weekly', ...}
        recurrence_end: Optional[datetime] = None
    ):
        if start_dt >= end_dt:
            raise ValueError("start_dt < end_dt is required")
        
        if start_dt.tzinfo is None or end_dt.tzinfo is None:
            raise ValueError("datetime objects must be timezone-aware")
        
        self.id = event_id if event_id is not None else Event._id_counter
        if event_id is None:
            Event._id_counter += 1
            
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.name = name
        self.description = description
        self.color = color
        self.meta = meta or {}
        self.recurrence = recurrence
        self.recurrence_end = recurrence_end
    
    @property
    def recurrence_rule(self) -> Dict:
        if isinstance(self.recurrence, dict):
            return self.recurrence
        elif isinstance(self.recurrence, str):
            # Convert simple strings to rule dict
            if self.recurrence in ['daily', 'weekly', 'monthly', 'yearly']:
                return {'freq': self.recurrence, 'interval': 1}
        return {}
        
    @property
    def duration(self) -> timedelta:
        return self.end_dt - self.start_dt
        
    def intersects(self, range_start: datetime, range_end: datetime) -> bool:
        return not (self.end_dt <= range_start or self.start_dt >= range_end)
    
    def move_to(self, new_start_dt: datetime):
        duration = self.duration
        self.start_dt = new_start_dt
        self.end_dt = new_start_dt + duration
    
    def resize_to(self, new_end_dt: datetime):
        if new_end_dt <= self.start_dt:
            raise ValueError("new_end_dt must be greater than start_dt")
        self.end_dt = new_end_dt
    
    def __repr__(self):
        return f"Event(id={self.id}, '{self.name}')"


class EventBox:
    def __init__(
        self,
        event: Event,
        visible_start: datetime,
        visible_end: datetime
    ):
        self.event = event
        self.visible_start = visible_start
        self.visible_end = visible_end
    
    @property
    def duration_minutes(self) -> float:
        return (self.visible_end - self.visible_start).total_seconds() / 60
    
    def __repr__(self):
        return f"EventBox(event_id={self.event.id}, {self.visible_start} -> {self.visible_end})"