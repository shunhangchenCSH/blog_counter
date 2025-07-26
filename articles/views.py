from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from articles.models import Article, ArticleViews
from django_redis import get_redis_connection
from blog_counter.celery_task import async_update_article
from django.views import View

# Create your views here.


class ArticleListView(View):
    def get(self, request):
        articles = Article.objects.all().values('id', 'title', 'content', 'view_count', 'user_count')
        articles_list = list(articles)  
        return JsonResponse({
            'articles': articles_list,
        })


class ArticleDetailView(View):
    def get(self, request, article_id):
        try:
            article = get_object_or_404(Article, id=article_id)        

            if request.user.is_authenticated:
                user_id = request.user.id

                # redis新增文章访问
                ArticleDataService.incr_article_views_data(article_id, user_id)

                # 异步更新数据库
                async_update_article.delay(article_id, user_id)

                # 查询redis 或者 数据库
                data = ArticleDataService.get_article_views_data(article_id, request.user.id)
                view_count = data['view_count'] or article.view_count
                user_count = data['user_count'] or article.user_count
                user_view_count = data['user_view_count'] or ArticleViews.objects.filter(article_id=article_id, user_id=user_id).count()

            return JsonResponse({
                'user_count': user_count,
                'view_count': view_count,
                'user_view_count': user_view_count,
                'title': article.title,
                'content': article.content,
            })
        except Exception as e:
            raise e


class ArticleDataView(View):
    def get(self, request, article_id):
        data = ArticleDataService.get_article_views_data(article_id, request.user.id)
        return JsonResponse({
                'user_count': data['user_count'],
                'view_count': data['view_count'],
                'user_view_count': data['user_view_count'],
            })



    



    
