from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Article(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    user_count = models.IntegerField(default=0, verbose_name='文章被不同用户阅读的次数')
    view_count = models.IntegerField(default=0, verbose_name='文章被阅读的次数')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title



class ArticleViews(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} read {self.article.title}"

