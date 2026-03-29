from django.urls import path
from .views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('register/', RegisterView.as_view()),   # signup
    path('login/', TokenObtainPairView.as_view()),  # login → JWT token
]