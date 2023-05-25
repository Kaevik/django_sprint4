from django.urls import path, URLPattern
from . import views

app_name: str = 'pages'

urlpatterns: list[URLPattern] = [
    path('about/', views.AboutTemplateView.as_view(), name='about'),
    path('rules/', views.RulesTemplateView.as_view(), name='rules'),
]
