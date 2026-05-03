from django.urls import path
from . import views   # ✅ correct import

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_resume, name='upload'),
    path('history/', views.history_page, name='history'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
]