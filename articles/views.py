from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from articles.models import Article, ArticleViews
from blog_counter.celery_task import async_update_article
from django.views import View
from .service import ArticleDataService, StatsDataService

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
        """
        1、获取缓存
            1.1、命中，直接返回
            1.2、没命中
                从数据库查询，再写入到缓存（确保数据库和缓存一致）
        2、更新访问记录
            更新缓存，异步celery更新数据库
        """
        try:
            if request.user.is_authenticated:
                user_id = request.user.id
                response_data = {}

                hit_flag = True
                # 获取数据，是不是取决于'is_cache'
                views_data = ArticleDataService.get_article_views_data(article_id, user_id)
                if not views_data['is_cache']:
                    # 代表没命中
                    hit_flag = False
                    article = get_object_or_404(Article, id=article_id)
                    user_view_count = ArticleViews.objects.filter(article_id=article_id, user_id=user_id).count()
                    views_data = {
                        'title': article.title,
                        'content': article.content,
                        'view_count': article.view_count,
                        'user_count': article.user_count,
                        'user_view_count': user_view_count,
                    }

                # 同步缓存
                ArticleDataService.set_article_views_data(article_id, user_id, db_data=views_data)

                response_data.update({
                    'title': views_data['title'],
                    'content': views_data['content'],
                    'view_count': views_data['view_count'],
                    'user_count': views_data['user_count'],
                    'user_view_count': views_data['user_view_count'],
                })

                # redis新增文章访问
                views_data = ArticleDataService.incr_article_views_data(article_id, user_id)
                response_data.update({
                    'view_count': views_data['view_count'],
                    'user_count': views_data['user_count'],
                    'user_view_count': views_data['user_view_count'],
                })

                # 增加api调用次数
                StatsDataService.incr_api_call_data(hit_flag)

                return JsonResponse({
                    'user_count': response_data['user_count'],
                    'view_count': response_data['view_count'],
                    'user_view_count': response_data['user_view_count'],
                    'title': response_data['title'],
                    'content': response_data['content'],
                })
            else:
                return HttpResponse("请先登录!")
        except Exception as e:
            StatsDataService.incr_api_call_data(hit_flag=False)
            raise e


class ArticleDataView(View):
    def get(self, request, article_id):
        data = ArticleDataService.get_article_views_data(article_id, request.user.id)
        return JsonResponse({
                'user_count': data['user_count'],
                'view_count': data['view_count'],
                'user_view_count': data['user_view_count'],
            })


class CacheStatsView(View):
    def get(self, request):
        stats = StatsDataService.get_cache_stats()
        return JsonResponse(stats)


class ApiStatsView(View):
    def get(self, request):
        stats = StatsDataService.get_api_call_data()
        return JsonResponse(stats)






    
