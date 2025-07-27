# blog_counter

##  init
python manage.py migrate
python manage.py createsuperuser

### 启动redis
redis-server  # 6379 给项目使用
redis-server --port 6380 # 6380 给celery使用

### 启动celery
celery -A blog_counter.celery_app worker -l info

## api
文章详情接口：http://127.0.0.1:8000/articles/1/
文章列表接口：http://127.0.0.1:8000/articles/
文章详情的缓存接口：http://127.0.0.1:8000/articles/cache_stats/
文章详情的api调用接口：http://127.0.0.1:8000/articles/api_stats/

redis-cli CONFIG RESETSTAT # 清空redis命中率