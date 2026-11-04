import json
from django.db.models import Count
from apps.blog.models import Post, Comment, Category
from apps.auths.models import User

def environment_callback(request):
    """Возвращает бэйдж окружения в правом верхнем углу"""
    return ["LOCAL", "info"]

def drafts_badge(request):
    """Количество черновиков для бейджа в сайдбаре"""
    count = Post.objects.filter(status="draft").count()
    return count if count > 0 else None

def dashboard_callback(request, context):
    """Формирует полную статистику для кастомного дашборда"""
    
    # 1. Подсчет данных через БД (.count()), без циклов в Python
    total_users = User.objects.count()
    published_posts = Post.objects.filter(status="published").count()
    draft_posts = Post.objects.filter(status="draft").count()
    total_comments = Comment.objects.count()
    total_posts = published_posts + draft_posts

    # Прогресс-бары (доли в процентах)
    published_pct = round((published_posts / total_posts * 100) if total_posts > 0 else 0, 1)
    draft_pct = round((draft_posts / total_posts * 100) if total_posts > 0 else 0, 1)

    # 2. Данные для графика по категориям (posts per category)
    categories_data = Category.objects.annotate(posts_count=Count("post"))
    chart_labels = [cat.name for cat in categories_data]
    chart_data = [cat.posts_count for cat in categories_data]

    # Chart.js формат в виде JSON-строки
    posts_per_category_chart = json.dumps({
        "labels": chart_labels,
        "datasets": [{
            "label": "Posts per Category",
            "data": chart_data,
        }]
    })

    # 3. Топ-5 авторов по количеству постов
    top_authors = (
        User.objects.annotate(posts_count=Count("post"))
        .filter(posts_count__gt=0)
        .order_by("-posts_count")[:5]
    )

    # Передаем всё в контекст шаблона
    context.update({
        # Карточки KPI
        "kpi": [
            {"title": "Total Users", "metric": total_users, "icon": "group"},
            {"title": "Published Posts", "metric": published_posts, "icon": "article"},
            {"title": "Drafts", "metric": draft_posts, "icon": "edit_note"},
            {"title": "Comments", "metric": total_comments, "icon": "comment"},
        ],
        # График
        "posts_per_category_chart": posts_per_category_chart,
        # Таблица топ авторов
        "top_authors": top_authors,
        # Прогресс-бары
        "stats_progress": {
            "published_count": published_posts,
            "published_pct": published_pct,
            "draft_count": draft_posts,
            "draft_pct": draft_pct,
        }
    })
    
    return context