from articles.models import Article, ArticleViews
from django_redis import get_redis_connection
from blog_counter.celery_app import celery_app

redis_conn = get_redis_connection("default")

@celery_app.task
def async_update_article(article_id, user_id):
    # 异步更新数据库(通过celery)
    try:
        article = Article.objects.get(id=article_id)
        view_count = redis_conn.get(f"article_{article_id}_totals") 
        if view_count:
            article.view_count = int(view_count)
        user_count = redis_conn.hlen(f"article_{article_id}_users")
        if user_count:
            article.user_count = int(user_count)
        article.save()

        # 创建ArticleViews记录
        ArticleViews.objects.create(article_id=article_id, user_id=user_id)
        return '异步更新数据库成功'
    except Article.DoesNotExist as e:
        raise e
    except Exception as e:
        return '异步更新数据库失败'