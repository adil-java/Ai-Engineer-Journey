from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(request):
    return JsonResponse({"status": "ok"})


admin.site.site_header = "WhoFix · approval inbox"
admin.site.site_title = "WhoFix"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    # Phase 6: path("webhooks/github/", ...)
]
