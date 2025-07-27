from django.urls import path
from . import views


urlpatterns = [
    path("", views.ArticleListView.as_view(), name='index'),
    path("<int:article_id>/", views.ArticleDetailView.as_view(), name='articles_detail'),
    path("cache_stats/", views.CacheStatsView.as_view(), name='cache_stats'),
    path("api_stats/", views.ApiStatsView.as_view(), name='api_stats'),
]
