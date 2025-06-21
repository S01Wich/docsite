from django.urls import path
from . import views

app_name = 'templates_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('fill/<int:pk>/', views.fill_template, name='fill_template'),
]