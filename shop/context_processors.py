from django.utils import timezone
import calendar

def global_date_context(request):
    now = timezone.now()
    return {
        'current_utc': now, # UTC время
        'current_local': timezone.localtime(now), # Время в таймзоне из settings.py
        'user_tz': timezone.get_current_timezone_name(),
        'text_calendar': calendar.TextCalendar().formatmonth(now.year, now.month),
    }