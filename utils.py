   

from datetime import datetime, timedelta, timezone


                                        
SNAP_STEP_MINUTES = 15


def snap_to_grid(dt: datetime) -> datetime:
       
    total_minutes = dt.hour * 60 + dt.minute
    snapped_minutes = round(total_minutes / SNAP_STEP_MINUTES) * SNAP_STEP_MINUTES
    
    hours = snapped_minutes // 60
    minutes = snapped_minutes % 60
    
                          
    if hours >= 24:
        dt = dt + timedelta(days=1)
        hours = 0
    
    return dt.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def snap_minutes(minutes: float) -> int:
                                               
    return int(round(minutes / SNAP_STEP_MINUTES) * SNAP_STEP_MINUTES)


def get_day_start(dt: datetime) -> datetime:
                                  
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(dt: datetime) -> datetime:
                                                 
    return get_day_start(dt) + timedelta(days=1)


def get_week_days(reference_date: datetime, num_days: int = 7) -> list[datetime]:
       
    start_date = get_day_start(reference_date)
    return [start_date + timedelta(days=i) for i in range(num_days)]


def pixels_to_minutes(pixels: float, pixels_per_minute: float) -> float:
                                       
    return pixels / pixels_per_minute


def minutes_to_pixels(minutes: float, pixels_per_minute: float) -> float:
                                       
    return minutes * pixels_per_minute


def get_local_timezone() -> timezone:
                                
    return datetime.now().astimezone().tzinfo