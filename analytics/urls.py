from django.urls import path
from .views import FetchCFProfile,FetchCFSubmissions, TopicAnalysis, Weak_and_Strong_Topics,RatingAnalysis, RecommendationView


urlpatterns = [
    path('cf-profile/', FetchCFProfile.as_view()),  # API endpoint
    path('cf-submissions/', FetchCFSubmissions.as_view()),
    path('topic-analysis/', TopicAnalysis.as_view()),
    path('weak-and-strong-topics/', Weak_and_Strong_Topics.as_view()),
    path('rating-analysis/', RatingAnalysis.as_view()),
    path('recommendations/', RecommendationView.as_view())
]