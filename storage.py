import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from model import Event
from recurrence import expand_recurrence

class Storage:
    
    def __init__(self, db_path: str = "calendar.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_dt TEXT NOT NULL,
                end_dt TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT 'blue',
                meta TEXT,
                recurrence TEXT,
                recurrence_end TEXT
            )
        """)
        
        # We can clean up the schema but it's simpler to just ignore old columns if they exist.
        # But for correctness, we are defining the schema we use.
        # If the DB already exists, SQLite won't drop columns easily.
        # We will just continue to use these columns.
        
        # Migrate old columns? No, we just ignore them.
        self._check_and_migrate(cursor, "events", "recurrence", "TEXT")
        self._check_and_migrate(cursor, "events", "recurrence_end", "TEXT")
        
        conn.commit()
        conn.close()

    def _check_and_migrate(self, cursor, table, column, col_type):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def save_event(self, event: Event) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_str = event.start_dt.isoformat()
        end_str = event.end_dt.isoformat()
        meta_str = json.dumps(event.meta)
        
        # Serialize recurrence rule
        if isinstance(event.recurrence, dict):
            recurrence_str = json.dumps(event.recurrence)
        else:
            recurrence_str = event.recurrence
            
        recurrence_end_str = event.recurrence_end.isoformat() if event.recurrence_end else None
        
        existing_id = None
        if event.id is not None and event.id > 0:
            cursor.execute("SELECT id FROM events WHERE id = ?", (event.id,))
            result = cursor.fetchone()
            if result:
                existing_id = result[0]
        
        if existing_id:
            cursor.execute("""
                UPDATE events
                SET start_dt = ?, end_dt = ?, name = ?, description = ?, color = ?, meta = ?,
                    recurrence = ?, recurrence_end = ?
                WHERE id = ?
            """, (start_str, end_str, event.name, event.description, event.color, meta_str, 
                  recurrence_str, recurrence_end_str, event.id))
        else:
            cursor.execute("""
                INSERT INTO events (start_dt, end_dt, name, description, color, meta, recurrence, recurrence_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (start_str, end_str, event.name, event.description, event.color, meta_str,
                  recurrence_str, recurrence_end_str))
            event.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return event.id
    
    def load_events(self, start_range: Optional[datetime] = None, 
                    end_range: Optional[datetime] = None) -> List[Event]:
           
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # We only select columns we know about
        columns = "id, start_dt, end_dt, name, description, color, meta, recurrence, recurrence_end"
        
        if start_range and end_range:
            start_str = start_range.isoformat()
            end_str = end_range.isoformat()
            cursor.execute(f"""
                SELECT {columns}
                FROM events
                WHERE (end_dt > ? AND start_dt < ?) OR (recurrence IS NOT NULL)
                ORDER BY start_dt
            """, (start_str, end_str))
        else:
            cursor.execute(f"""
                SELECT {columns}
                FROM events
                ORDER BY start_dt
            """)
        
        events = []
        for row in cursor.fetchall():
            (event_id, start_str, end_str, name, description, color, meta_str, recurrence, recurrence_end_str) = row
            
            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)
            meta = json.loads(meta_str) if meta_str else {}
            recurrence_end = datetime.fromisoformat(recurrence_end_str) if recurrence_end_str else None
            
            # Recurrence could be simple string or JSON dict
            if recurrence and (recurrence.startswith('{') or recurrence.startswith('[')):
                try:
                    recurrence = json.loads(recurrence)
                except json.JSONDecodeError:
                    pass # Keep as string
            
            event = Event(
                start_dt=start_dt,
                end_dt=end_dt,
                name=name,
                description=description,
                color=color or "blue",
                meta=meta,
                event_id=event_id,
                recurrence=recurrence,
                recurrence_end=recurrence_end
            )
            events.append(event)
        
        conn.close()
        return self._expand_recurring_events(events, start_range, end_range) if start_range and end_range else events
    
    def _expand_recurring_events(self, events: List[Event], start_range: datetime, end_range: datetime) -> List[Event]:
        expanded = []
        for event in events:
            if not event.recurrence:
                # Add normal events if they overlap
                if event.intersects(start_range, end_range):
                    expanded.append(event)
                continue
            
            # Wrapper for exception handling
            exceptions = set(event.meta.get('exceptions', []))
            
            # Use recurrence engine
            # Convert simple recurrence to rule dict if string
            rule = event.recurrence_rule
            if not rule:
                 # Fallback just in case
                 if event.intersects(start_range, end_range):
                     expanded.append(event)
                 continue
                 
            # Add recurrence_end to rule if exists
            if event.recurrence_end:
                rule['until'] = event.recurrence_end
            
            occurrences = expand_recurrence(rule, event.start_dt, start_range, end_range)
            
            duration = event.duration
            
            for occ in occurrences:
                # Check exceptions
                date_str = occ.strftime("%Y-%m-%d")
                if date_str in exceptions:
                   continue
                   
                instance = Event(
                    start_dt=occ,
                    end_dt=occ + duration,
                    name=event.name,
                    description=event.description,
                    color=event.color,
                    meta=event.meta, # Inherit meta
                    event_id=event.id, # Shared ID
                    recurrence=event.recurrence,
                    recurrence_end=event.recurrence_end
                )
                instance.original_start = occ
                expanded.append(instance)
                    
        return expanded
                    
        return expanded

    def delete_event(self, event_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
    
    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        columns = "id, start_dt, end_dt, name, description, color, meta"
        cursor.execute(f"SELECT {columns} FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
             (event_id, start_str, end_str, name, description, color, meta_str) = row
             
             return Event(
                start_dt=datetime.fromisoformat(start_str),
                end_dt=datetime.fromisoformat(end_str),
                name=name,
                description=description,
                color=color or "blue",
                meta=json.loads(meta_str) if meta_str else {},
                event_id=event_id
            )
        return None