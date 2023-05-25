from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include, URLPattern
from django.conf import settings


handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

urlpatterns: list[URLPattern] = [
    path('pages/', include('pages.urls', namespace='pages')),
    path('', include('blog.urls', namespace='blog')),
    path('', include('users.urls', namespace='users')),
    path('admin/', admin.site.urls),
    
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
