from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('signup/', views.admin_signup, name='admin_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password/change/', login_required(auth_views.PasswordChangeView.as_view(
        template_name='password_change.html',
        success_url=reverse_lazy('password_change_done')
    )), name='password_change'),
    path('password/change/done/', login_required(auth_views.PasswordChangeDoneView.as_view(
        template_name='password_change_done.html'
    )), name='password_change_done'),
    path('me/', views.my_meals, name='my_meals'),
    path('', views.dashboard, name='dashboard'),
    path('daily-meals/', views.daily_meals, name='daily_meals'),
    path('manage-price/', views.manage_price, name='manage_price'),
    path('manage-payments/', views.manage_payments, name='manage_payments'),
    path('manage-members/', views.manage_members, name='manage_members'),
]
