"""
URL configuration for testdjereo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/stable/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from testdjereo import views as testdjereo_views

urlpatterns = [
    path("-/", include("django_alive.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", testdjereo_views.index, name="index"),
]

if settings.ENABLE_DEBUG_TOOLS:  # pragma: no cover
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
        *debug_toolbar_urls(),
    ]

if settings.IS_TESTING:  # pragma: no cover
    from testdjereo.tests.test_app import views as test_app_views

    urlpatterns += [
        path(
            "403/", test_app_views.permission_denied_view, name="permission-denied-view"
        ),
    ]
