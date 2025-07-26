from django.urls import path
from . import views


urlpatterns = [
    path("", views.ArticleListView.as_view(), name='index'),
    path("<int:article_id>/", views.ArticleDetailView.as_view(), name='articles_detail'),
    path("<int:article_id>/views_data/", views.ArticleDataView.as_view(), name='views_data'),
]
