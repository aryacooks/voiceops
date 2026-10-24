from datetime import date, timedelta
from .config import TODAY
from .data import table

def parse(value):
    return date.fromisoformat(str(value)[:10])
def is_business_day(day):
    return day.weekday() != 6 and day.isoformat() not in set(table('holidays')['date'])
def add_business_days(start, days):
    day = parse(start)
    direction = 1 if int(days) >= 0 else -1
    remaining = abs(int(days))
    while remaining:
        day += timedelta(days=direction)
        if is_business_day(day):
            remaining -= 1
    return day

def date_calc(op, start=None, days=0, end=None):
    start = parse(start) if start else TODAY
    if op == 'today': return {'date': TODAY.isoformat()}
    if op == 'add_business_days': result = add_business_days(start, days)
    elif op == 'add_calendar_days': result = start + timedelta(days=int(days))
    elif op == 'calendar_days_between':
        return {'days': (parse(end or TODAY) - start).days}
    elif op == 'business_days_between':
        finish = parse(end or TODAY)
        direction = 1 if finish >= start else -1
        day, count = start, 0
        while day != finish:
            day += timedelta(days=direction)
            count += direction * int(is_business_day(day))
        return {'days': count}
    else: raise ValueError('Unknown date operation')
    return {'date': result.isoformat(), 'spoken_date': result.strftime('%d %B %Y'),
            'counting': 'start excluded; Mon–Sat minus holidays for business days'}
