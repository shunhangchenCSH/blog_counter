from django.utils.deprecation import MiddlewareMixin
from articles.models import Article
from articles.services import ArticleViewsService

# class ArticleDetailMiddleware(MiddlewareMixin):
#     async def process_request(self, request):
#         if request.path.startswith('/articles/'):
#             article_id = request.path.split('/')[-2]
#             print("article_id:", article_id)
#             try:
#                 article = await sync_to_async(Article.objects.get)(id=article_id)
#                 await ArticleViews.objects.acreate(
#                     article=article,
#                     user=request.user
#                 )
#             except Article.DoesNotExist:
#                 pass
#             return None

            
