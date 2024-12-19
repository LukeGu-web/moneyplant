from django.utils import timezone
from django.conf import settings
import pytz


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get timezone from request headers, default to settings.TIME_ZONE if not provided
        timezone_header = request.headers.get('X-Timezone', settings.TIME_ZONE)

        try:
            # Validate and activate the timezone
            user_timezone = pytz.timezone(timezone_header)
            timezone.activate(user_timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to default timezone if an invalid timezone is provided
            default_timezone = pytz.timezone(settings.TIME_ZONE)
            timezone.activate(default_timezone)

        response = self.get_response(request)

        # Always deactivate the timezone after the request
        timezone.deactivate()

        return response
