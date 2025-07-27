from django_redis import get_redis_connection
import logging
import redis
from django.shortcuts import get_object_or_404
from articles.models import Article, ArticleViews
from blog_counter.celery_task import async_update_article


class ArticleDataService:
    def incr_article_views_data(article_id, user_id):
        redis_conn = get_redis_connection("default")
        pl = redis_conn.pipeline() 
        try:
            # 检查用户是否已存在
            pl.hexists(f"article:{article_id}:users", f"user_{user_id}")
            is_exists = pl.execute()[0]
            if not is_exists:
                pl.hincrby(f"article:{article_id}:stats", "user_count", 1)

            # 用户层
            # example: article:1:users: {user_1: 3, user_2: 2}
            pl.hincrby(f"article:{article_id}:users", f"user_{user_id}", 1)

            # 文章层
            # example: article:1:stats: {view_count: 10, user_count: 2}
            pl.hincrby(f"article:{article_id}:stats", "view_count", 1)

            # 返回新增后的结果
            pl.hgetall(f"article:{article_id}:stats")
            pl.hget(f"article:{article_id}:users", f"user_{user_id}")
            stats, user_view = pl.execute()[-2:]

            # 异步更新数据库
            async_update_article.delay(article_id, user_id)

            view_count = int(stats.get(b'view_count', 0))
            user_count = int(stats.get(b'user_count', 0))
            user_view_count = int(user_view) or 0
            
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")
            # 异常降级处理
            try:
                # 异步更新数据库
                async_update_article.delay(article_id, user_id)
                view_count = Article.objects.get(id=article_id).view_count
                user_count = Article.objects.get(id=article_id).user_count
                user_view_count = ArticleViews.objects.filter(article_id=article_id, user_id=user_id).count()
            except Exception as e:
                logging.error(f"DB and Redis error: {e}")
                raise e
        
        return {
            'view_count': view_count,
            'user_count': user_count,
            'user_view_count': user_view_count,
        }
    
    def set_article_views_data(article_id, user_id, db_data):
        try:
            # 从数据库写到缓存
            redis_conn = get_redis_connection("default")
            pl = redis_conn.pipeline()

            # 先redis获取数据和db查询数据 对比再进行写入
            pl.hgetall(f"article:{article_id}:stats")
            pl.hgetall(f"article:{article_id}:users")
            stats, users = pl.execute()[-2:]

            view_count = int(stats.get(b'view_count', 0))
            user_count = int(stats.get(b'user_count', 0))
        
            if view_count != db_data.get('view_count') or \
                user_count != db_data.get('user_count'):
                pl.hset(f"article:{article_id}:stats", mapping={
                    'view_count': db_data.get('view_count'),
                    'user_count': db_data.get('user_count'),
                })
                pl.expire(f"article:{article_id}:stats", 60 * 60 * 24)

            user_view_count = int(users.get(f"user_{user_id}".encode('utf-8'), 0))
            if user_view_count != db_data.get('user_view_count'):
                pl.hset(f"article:{article_id}:users", mapping={
                    f"user_{user_id}": db_data.get('user_view_count'),
                })
                pl.expire(f"article:{article_id}:users", 60 * 60 * 24)

            pl.hset(f"article:{article_id}:meta", mapping={
                'title': db_data.get('title'),
                'content': db_data.get('content'),
            })
            pl.expire(f"article:{article_id}:meta", 60 * 60 * 24)
            pl.execute()
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")


    def get_article_views_data(article_id, user_id):
        try:
            redis_conn = get_redis_connection("default")
            meta_data = redis_conn.hgetall(f"article:{article_id}:meta")
            stats_data = redis_conn.hgetall(f"article:{article_id}:stats")
            user_data = redis_conn.hgetall(f"article:{article_id}:users")

            title = meta_data.get(b'title', b'').decode('utf-8')
            content = meta_data.get(b'content', b'').decode('utf-8')
            view_count = int(stats_data.get(b'view_count', 0))
            user_count = int(stats_data.get(b'user_count', 0))
            user_view_count = int(user_data.get(f"user_{user_id}".encode('utf-8'), 0))
            # 缓存数据
            is_cache = True
            if not view_count or not user_count or not user_view_count:
                is_cache = False
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")
            # 异常降级处理
            try:
                article = get_object_or_404(Article, id=article_id)

                title = article.title
                content = article.content
                view_count = article.view_count
                user_count = article.user_count
                user_view_count = ArticleViews.objects.filter(article_id=article_id, user_id=user_id).count()
                # 数据库数据
                is_cache = False
            except Exception as e:
                logging.error(f"DB and Redis error: {e}")

        return {
            'is_cache': is_cache,
            'title': title,
            'content': content,
            'view_count': int(view_count),
            'user_count': int(user_count),
            'user_view_count': int(user_view_count),
        }

class StatsDataService:
    def incr_api_call_data(hit_flag):
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.incr("article_detail_api_total_call")
            if hit_flag:
                redis_conn.incr("article_list_api_real_call")
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")

    def get_api_call_data():
        try:
            redis_conn = get_redis_connection("default")

            total_call = redis_conn.get("article_detail_api_total_call") or 0
            real_call = redis_conn.get("article_list_api_real_call") or 0
            hit_rate = 0
            if total_call and real_call:
                hit_rate = int(real_call) / int(total_call)

            return {
                'total_call': int(total_call),
                'real_call': int(real_call),
                'api_hit_rate': f"{hit_rate:.2%}",
            }
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")
            return 'Redis Error'

    def get_cache_stats():
        # 缓存命中信息
        try:
            redis_conn = get_redis_connection("default")
            info = redis_conn.info("stats")
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)

            total = keyspace_hits + keyspace_misses
            hit_rate = keyspace_hits / total if total > 0 else 0
            return {
                'keyspace_hits': keyspace_hits,
                'keyspace_misses': keyspace_misses,
                'cache_hit_rate': f"{hit_rate:.2%}",
            }
        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error: {e}")
            return 'Redis Error'
