from django import template

register = template.Library()

WEEKDAY_MAP = {
    "mon": "Mon",
    "tue": "Tue",
    "wed": "Wed",
    "thu": "Thu",
    "fri": "Fri",
    "sat": "Sat",
    "sun": "Sun",
}

MONTH_MAP = {
    "1": "Jan", "2": "Feb", "3": "Mar", "4": "Apr",
    "5": "May", "6": "Jun", "7": "Jul", "8": "Aug",
    "9": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}

@register.filter
def weekday_labels(csv_value: str) -> str:
    if not csv_value:
        return ""
    items = [x.strip() for x in csv_value.split(",") if x.strip()]
    return ", ".join(WEEKDAY_MAP.get(x, x) for x in items)

@register.filter
def month_labels(csv_value: str) -> str:
    if not csv_value:
        return ""
    items = [x.strip() for x in csv_value.split(",") if x.strip()]
    return ", ".join(MONTH_MAP.get(x, x) for x in items)

@register.filter
def time_labels(csv_value: str) -> str:
    """
    Convert "08:00,20:00" -> "8:00 AM, 8:00 PM"
    """
    if not csv_value:
        return ""
    items = [x.strip() for x in csv_value.split(",") if x.strip()]
    out = []
    for t in items:
        try:
            hh, mm = t.split(":")
            h = int(hh)
            ampm = "PM" if h >= 12 else "AM"
            h = h % 12
            if h == 0:
                h = 12
            out.append(f"{h}:{mm} {ampm}")
        except Exception:
            out.append(t)
    return ", ".join(out)
