import logging
from math import log
from django.db.models import F
from articles.models import Article, ArticleViews
from django_redis import get_redis_connection
from blog_counter.celery_app import celery_app

redis_conn = get_redis_connection("default")

@celery_app.task
def async_update_article(article_id, user_id):
    """
    在进行异常分级处理的时候

    有个问题关于async_update_article
    如果使用Redis进行更新的话，假设Redis出现问题
    DB是拿不到数据的，所以要进行更新
    """
    # 异步更新数据库(通过celery)
    try:
        is_exists = ArticleViews.objects.filter(article_id=article_id, user_id=user_id).exists()
        
        if not is_exists:
            Article.objects.filter(id=article_id).update(user_count=F('user_count') + 1)

        # 默认新增
        Article.objects.filter(id=article_id).update(view_count=F('view_count') + 1)
        ArticleViews.objects.create(
            article_id=article_id,
            user_id=user_id,
        )
        logging.info(f"异步更新数据库成功")
        return '异步更新数据库成功'
    except Exception as e:
        logging.error(f"异步更新数据库失败: {e}")
        return '异步更新数据库失败: {}'.format(e)