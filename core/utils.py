from django.conf import settings
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


def require_verified_student(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_verified_student:
            return JsonResponse({'error': 'unauthorized'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapped
