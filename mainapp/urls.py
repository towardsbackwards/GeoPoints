from django.urls import path
from .views import PointsView, MinScore, MinLength

app_name = "points"

urlpatterns = [
    path('points/', PointsView.as_view()),
    path('points/<int:from>/min_length/<int:to>', MinLength.as_view()),
    path('points/<int:from>/min_score/<int:to>', MinScore.as_view())
]