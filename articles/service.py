from turtle import title
from django_redis import get_redis_connection


class ArticleDataService:
    def incr_article_views_data(article_id, user_id):
        redis_conn = get_redis_connection("default")
        pl = redis_conn.pipeline() 

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

        return {
            'view_count': int(stats.get(b'view_count', 0)),
            'user_count': int(stats.get(b'user_count', 0)),
            'user_view_count': int(user_view) or 0,
        }
    
    def set_article_views_data(article_id, user_id, db_data):
        # 从数据库写到缓存
        redis_conn = get_redis_connection("default")
        pl = redis_conn.pipeline()
    
        pl.hset(f"article:{article_id}:meta", mapping={
            'title': db_data.get('title'),
            'content': db_data.get('content'),
        })
        pl.expire(f"article:{article_id}:meta", 60 * 60 * 24)

        view_count = db_data.get('view_count')
        user_count = db_data.get('user_count')
        if view_count and user_count:
            pl.hset(f"article:{article_id}:stats", mapping={
                'view_count': view_count,
                'user_count': user_count,
            })
            pl.expire(f"article:{article_id}:stats", 60 * 60 * 24)

        user_view_count = db_data.get('user_view_count')
        if user_view_count:
            pl.hset(f"article:{article_id}:users", mapping={
                f"user_{user_id}": user_view_count,
            })
            pl.expire(f"article:{article_id}:users", 60 * 60 * 24)

        pl.execute()


    def get_article_views_data(article_id, user_id):
        redis_conn = get_redis_connection("default")

        meta_data = redis_conn.hgetall(f"article:{article_id}:meta")
        stats_data = redis_conn.hgetall(f"article:{article_id}:stats")
        user_data = redis_conn.hgetall(f"article:{article_id}:users")

        view_count = stats_data.get(b'view_count', 0)
        user_count = stats_data.get(b'user_count', 0)
        user_view_count = user_data.get(f"user_{user_id}".encode('utf-8'), 0)

        title = meta_data.get(b'title', b'').decode('utf-8')
        content = meta_data.get(b'content', b'').decode('utf-8')

        return {
            'title': title,
            'content': content,
            'view_count': int(view_count),
            'user_count': int(user_count),
            'user_view_count': int(user_view_count),
        }

class StatsDataService:
    def incr_api_call_data(hit_flag):
        redis_conn = get_redis_connection("default")
        redis_conn.incr("article_detail_api_total_call")
        if hit_flag:
            redis_conn.incr("article_list_api_real_call")

    def get_api_call_data():
        redis_conn = get_redis_connection("default")

        total_call = redis_conn.get("article_detail_api_total_call")
        real_call = redis_conn.get("article_list_api_real_call")

        hit_rate = 0
        if total_call and real_call:
            hit_rate = int(real_call) / int(total_call)

        return {
            'total_call': int(total_call),
            'real_call': int(real_call),
            'api_hit_rate': f"{hit_rate:.2%}",
        }

    def get_cache_stats():
        # 缓存命中信息
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

