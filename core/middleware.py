import time
from django.http import JsonResponse

# Very simple in-memory rate limiter for demonstration only
REQUEST_LOG = {}

class SimpleRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ['/auth/firebase/verify/', '/auth/firebase/log_otp_sent/'] and request.method == 'POST':
            ip = request.META.get('REMOTE_ADDR')
            now = time.time()
            window = 60
            limit = 10
            times = REQUEST_LOG.get(ip, [])
            times = [t for t in times if now - t < window]
            if len(times) >= limit:
                return JsonResponse({'error': 'rate_limited'}, status=429)
            times.append(now)
            REQUEST_LOG[ip] = times
        return self.get_response(request)
