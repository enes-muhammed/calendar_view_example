
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union

def expand_recurrence(
    rule: Dict,
    start_dt: datetime,
    range_start: datetime,
    range_end: datetime
) -> List[datetime]:
    """
    Expands a recurrence rule into a list of datetimes within a range.
    
    rule: {
        'freq': 'daily' | 'weekly' | 'monthly' | 'yearly',
        'interval': int (default 1),
        'by_day': List[str] (e.g. ['MO', 'TU']) or List[int] (0-6), optional,
        'until': datetime, optional,
        'count': int, optional
    }
    """
    freq = rule.get('freq')
    if not freq:
        return []

    interval = int(rule.get('interval', 1))
    if interval < 1: interval = 1
    
    until = rule.get('until') # datetime
    count = rule.get('count') # int
    
    by_day = rule.get('by_day')
    # Normalize by_day to integers 0(Mon)-6(Sun)
    target_weekdays = []
    if by_day:
        day_map = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
        for d in by_day:
            if isinstance(d, int):
                target_weekdays.append(d)
            elif isinstance(d, str) and d.upper() in day_map:
                target_weekdays.append(day_map[d.upper()])
    
    occurrences = []
    current = start_dt
    
    # Safety limit
    hard_limit = range_end + timedelta(days=365*2) 
    loop_count = 0
    generated_count = 0
    
    while True:
        # Check end conditions
        if until and current > until:
            break
        if count and generated_count >= count:
            break
        if current > hard_limit: # Safety break
            break
            
        # Check range overlap (optimization: start checking only when near range)
        # But we need to generate in order to track 'count' correctly.
        
        # If freq is WEEKLY and we have target_weekdays, we might have multiple hits in one interval?
        # Standard RRULE: WEEKLY;INTERVAL=2;BYDAY=TU,TH 
        # Means every 2 weeks, on Tue and Thu.
        # The 'current' tracks the "interval start". Inside that interval, we check days.
        
        if freq == 'weekly' and target_weekdays:
            # For this interval week, find valid days
            # Steps:
            # 1. Provide candidates in this week based on current (which is start of this interval iteration)
            # Actually, standard behavior:
            # If start_dt is Monday, and rule is Monthly, current jumps month by month.
            # If Weekly, current jumps week by week.
            
            # We need to align 'current' to the start of the week? 
            # Or just check days in the week starting from 'current'?
            # Usually strict RRULE aligns to week start. 
            # Let's keep it simple: 'current' is the anchor. 
            # If strict RRULE compliance isn't required, we can iterate days.
            
            # Simple approach for "Weekly on X, Y":
            # We find the Monday of the current week.
            monday = current - timedelta(days=current.weekday())
            
            week_hits = []
            for wd_idx in sorted(target_weekdays):
                candidate = monday + timedelta(days=wd_idx)
                
                # Current logic flaw: if start_dt is Wed, and BYDAY=MO,
                # The first instance should probably be next Monday if it's AFTER start_dt?
                # Or does it include the Mon before?
                # "Every week on Mon" implies the Mon of that week.
                # If start_dt > candidate, skip?
                # Only include if candidate >= start_dt (start date is inclusive foundation)
                
                # Careful: 'current' advances by 'interval' weeks.
                # If interval=2, we skip a week.
                
                if candidate >= start_dt:
                     # Check end conditions for this specific day hit
                    if until and candidate > until:
                        continue
                        
                    week_hits.append(candidate)
            
            # Add hits to occurrences
            for hit in week_hits:
                if count and generated_count >= count:
                    break
                
                if hit >= range_start and hit < range_end:
                    occurrences.append(hit)
                
                if hit >= start_dt: # Logically always true inside loop, but for 'count' tracking logic
                     generated_count += 1
            
            # Move to next interval
            current += timedelta(weeks=interval)
            
        else:
            # Daily, Monthly, Yearly OR Weekly without specific days (defaults to same day)
            
            if current >= start_dt:
                # Add if in range
                if current >= range_start and current < range_end:
                    occurrences.append(current)
                
                generated_count += 1
            
            # Advance
            if freq == 'daily':
                current += timedelta(days=interval)
            elif freq == 'weekly':
                current += timedelta(weeks=interval)
            elif freq == 'monthly':
                # Add interval months
                y, m = current.year, current.month
                m += interval
                
                # Calculate year increment
                y += (m - 1) // 12
                m = (m - 1) % 12 + 1
                
                # Handle day clamping (e.g. Jan 31 -> Feb 28)
                d = min(current.day, [31, 29 if y%4==0 and (y%100!=0 or y%400==0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1])
                try:
                    current = current.replace(year=y, month=m, day=d)
                except ValueError:
                    # Should be covered by min check, but fallback
                    current = current.replace(day=1) + timedelta(days=32)
                    current = current.replace(day=1) - timedelta(days=1)

            elif freq == 'yearly':
                try:
                    current = current.replace(year=current.year + interval)
                except ValueError:
                    # Leap year 29 Feb -> 28 Feb
                    current = current.replace(year=current.year + interval, day=28)
            else:
                break
                
        # Optimization break if we passed range_end and don't need to count
        if not count and current >= range_end:
            break
            
        loop_count += 1
        if loop_count > 10000: # Infinite loop guard
            break
            
    return occurrences
