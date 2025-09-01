from django.http import JsonResponse


def healthz(_):
    return JsonResponse({"ok": True, "service": "django-app"})
