from django.contrib import admin

from .models import Article, ArticleViews

# Register your models here.
admin.site.register(Article)
admin.site.register(ArticleViews)
