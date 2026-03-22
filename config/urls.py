""" URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import settings
from .views import CustomAuthToken, Error500TestView, send_test_email, download_media

ADMIN_SITE_TITLE = 'eMensageria OpenSource'

admin.site.site_header = ADMIN_SITE_TITLE
admin.site.site_title = ADMIN_SITE_TITLE
admin.site.index_title = ADMIN_SITE_TITLE

urlpatterns = [
    path('api-token-auth/', CustomAuthToken.as_view()),
    path('esocial/', include("apps.esocial.urls", namespace='esocial')),
    path('test-error/', Error500TestView.as_view(), name='test_error'),
    path('enviar-email-teste/', send_test_email, name='enviar_email_teste'),
    path('media/<path:file_path>', download_media, name='download_media'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns.append(path('', admin.site.urls))
