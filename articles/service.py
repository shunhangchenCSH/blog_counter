class ArticleDataService:
    def incr_article_views_data(article_id, user_id):
        # 连接redis
        redis_conn = get_redis_connection("default")
        pl = redis_conn.pipeline()            
        # 用户层
        # example: article_1_users: {user_1: 1, user_2: 1}
        pl.hincrby(f"article_{article_id}_users", f"user_{user_id}", 1)
        # 文章层
        # example: article_1_totals: 100
        pl.incr(f"article_{article_id}_totals")
        pl.execute()


    def get_article_views_data(article_id, user_id):
        redis_conn = get_redis_connection("default")
        view_count = redis_conn.get(f"article_{article_id}_totals")
        user_count = redis_conn.hlen(f"article_{article_id}_users")
        user_view_count = redis_conn.hget(f"article_{article_id}_users", f"user_{user_id}")

        return {
            'view_count': int(view_count),
            'user_count': int(user_count),
            'user_view_count': int(user_view_count),
        }
