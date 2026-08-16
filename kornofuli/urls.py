"""
URL configuration for kornofuli project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.views.static import serve
import re


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('exams/', include('exams.urls')),
    path('reports/', include('reports.urls')),
    path('',include('home.urls'))
]

# Media ফাইল (শিক্ষক ছবি, gallery) — dev/prod যেকোনো পরিবেশে serve হবে।
# Django 6-এর static() DEBUG=False-এ ফাঁকা list ফেরত দেয় (No-op), তাই সরাসরি
# serve view দিয়ে pattern বানানো হয়েছে। বাস্তব production-এ nginx/caddy থাকলে
# এই ব্লক মুছে দিলেই চলবে।
media_url = settings.MEDIA_URL.lstrip('/')
urlpatterns += [
    re_path(
        r'^%s(?P<path>.*)$' % re.escape(media_url),
        serve,
        kwargs={'document_root': settings.MEDIA_ROOT}
    ),
]

# PWA/static ফাইল (manifest, icons, sw.js) — media-র মতোই serve হবে।
static_url = settings.STATIC_URL.lstrip('/')
urlpatterns += [
    re_path(
        r'^%s(?P<path>.*)$' % re.escape(static_url),
        serve,
        kwargs={'document_root': settings.BASE_DIR / 'static'}
    ),
]

