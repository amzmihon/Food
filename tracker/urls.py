from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('daily-meals/', views.daily_meals, name='daily_meals'),
    path('manage-price/', views.manage_price, name='manage_price'),
    path('manage-payments/', views.manage_payments, name='manage_payments'),
    path('manage-members/', views.manage_members, name='manage_members'),
]
