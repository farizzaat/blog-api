from datetime import date, timedelta
from typing import Any
from django.db.models import (
    QuerySet, Count, Avg, Min, Max, Q, F, Value, CharField, Case, When, Exists, OuterRef, Subquery
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone

from apps.blog.models import Category, Tag, Post, Comment
from apps.auths.models import User

# --- Константы из ТЗ ---
NEWEST_LIMIT = 5
PAGE_SIZE = 10
POPULAR_HOT_THRESHOLD = 10
POPULAR_NORMAL_THRESHOLD = 3
EDIT_HOUR_LIMIT = timedelta(hours=1)
UNCATEGORIZED_LABEL = "Uncategorized"
TOP_AUTHORS_LIMIT = 5
FEED_LIMIT = 50
NEWEST_TAGS_LIMIT = 20


# ==========================================
# Level 1 — First Queries
# ==========================================

def categories_by_name() -> QuerySet[Category]:
    """All categories, sorted by name A -> Z."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Published posts, newest first."""
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")


def newest_published_posts() -> QuerySet[Post]:
    """The 5 newest published posts."""
    return published_posts()[:NEWEST_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """The post with this slug, or None if there is no such post."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Number of active users. Staff users are not counted."""
    return User.objects.filter(is_active=True, is_staff=False).count()


def has_drafts() -> bool:
    """True if there is at least one draft post."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """One page of published posts, newest first (10 per page)."""
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return published_posts()[start:end]


# ==========================================
# Level 2 — Field Lookups
# ==========================================

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Posts whose title contains word. Letter case does not matter."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Users whose email ends with @ + domain."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Posts that have no category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Categories whose slug is in the list slugs."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Posts created in this month of this year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Posts created in the last days days."""
    since = timezone.now() - timedelta(days=days)
    return Post.objects.filter(created_at__gte=since)


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Posts created from start to end (inclusive of both days)."""
    next_day = end + timedelta(days=1)
    return Post.objects.filter(created_at__gte=start, created_at__lt=next_day)


# ==========================================
# Level 3 — Queries Across Relations
# ==========================================

def author_published_posts(email: str) -> QuerySet[Post]:
    """Published posts of the author with this email (case-insensitive)."""
    return Post.objects.filter(
        status=Post.Status.PUBLISHED,
        author__email__iexact=email
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Posts that have the tag with this slug."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Comments on posts of the category with this slug."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Users who have at least one published post (unique)."""
    return User.objects.filter(post__status=Post.Status.PUBLISHED).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Posts that have no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Users who have never written a comment."""
    return User.objects.exclude(comment__isnull=False).distinct()


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Posts that have both tags."""
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug)


# ==========================================
# Level 4 — Q and F
# ==========================================

def search_posts(text: str) -> QuerySet[Post]:
    """Posts that have text in title or body (case-insensitive)."""
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text)
    )


def published_posts_missing_info() -> QuerySet[Post]:
    """Published posts that have no category or no tags (unique)."""
    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).filter(
        Q(category__isnull=True) | Q(tags__isnull=True)
    ).distinct()


def edited_posts() -> QuerySet[Post]:
    """Posts edited more than 1 hour after creation."""
    return Post.objects.filter(updated_at__gt=F("created_at") + EDIT_HOUR_LIMIT)


def comments_by_post_author() -> QuerySet[Comment]:
    """Comments written by the post author under their own post."""
    return Comment.objects.filter(author=F("post__author"))


def comments_before_post() -> QuerySet[Comment]:
    """Comments created before their post (should be empty)."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))


# ==========================================
# Level 5 — values and values_list
# ==========================================

def published_authors_emails() -> list[str]:
    """Emails of authors who have published posts (unique, sorted A -> Z)."""
    return list(
        User.objects.filter(post__status=Post.Status.PUBLISHED)
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Dicts for published posts with keys: title, author_email, category_name."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(
            author_email=F("author__email"),
            category_name=Coalesce("category__name", Value(UNCATEGORIZED_LABEL))
        )
        .values("title", "author_email", "category_name")
    )


# ==========================================
# Level 6 — aggregate
# ==========================================

def posts_stats() -> dict[str, Any]:
    """Stats: total, published, drafts, first_post_at, last_post_at in 1 query."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at")
    )


def average_comments_per_post() -> float:
    """Average comments per published post (rounded to 2 decimals)."""
    stats = Post.objects.filter(status=Post.Status.PUBLISHED).annotate(
        c_count=Count("comment")
    ).aggregate(avg=Avg("c_count"))
    
    avg_val = stats["avg"]
    return round(avg_val, 2) if avg_val is not None else 0.0


# ==========================================
# Level 7 — annotate
# ==========================================

def categories_with_post_count() -> QuerySet[Category]:
    """Every category with post_count (most posts first, then by name)."""
    return Category.objects.annotate(
        post_count=Count("post")
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Every category with published_count (including 0)."""
    return Category.objects.annotate(
        published_count=Count("post", filter=Q(post__status=Post.Status.PUBLISHED))
    ).order_by("-published_count", "name")


def top_authors() -> QuerySet[User]:
    """Top 5 users by published post count."""
    return User.objects.annotate(
        published_count=Count("post", filter=Q(post__status=Post.Status.PUBLISHED))
    ).order_by("-published_count")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Tags used in at least min_posts posts, with post_count."""
    return Tag.objects.annotate(
        post_count=Count("post")
    ).filter(post_count__gte=min_posts).order_by("-post_count")


def posts_per_status() -> list[dict[str, Any]]:
    """Number of posts for each status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Every user with correct post_count and comment_count."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comment", distinct=True)
    )


# ==========================================
# Level 8 — Database Functions and Conditions
# ==========================================

def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Users whose full name contains text (case-insensitive)."""
    return User.objects.annotate(
        full_name=Concat("first_name", Value(" "), "last_name", output_field=CharField())
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Published posts per month, oldest first."""
    return list(
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Posts annotated with comment_count and popularity category."""
    from django.db.models import Case, When
    return Post.objects.annotate(
        comment_count=Count("comment")
    ).annotate(
        popularity=Case(
            When(comment_count__gte=POPULAR_HOT_THRESHOLD, then=Value("hot")),
            When(comment_count__gte=POPULAR_NORMAL_THRESHOLD, then=Value("normal")),
            default=Value("quiet"),
            output_field=CharField()
        )
    )


# ==========================================
# Level 9 — Changing Data
# ==========================================

def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Return tag with name, create if missing. Returns (tag, created)."""
    tag_slug = slugify(name)
    return Tag.objects.get_or_create(slug=tag_slug, defaults={"name": name})


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than specified days. Returns count."""
    threshold = timezone.now() - timedelta(days=days)
    updated_count = Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=threshold
    ).update(
        status=Post.Status.PUBLISHED,
        updated_at=timezone.now()
    )
    return updated_count


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add tag to every post of category. Returns total posts in category."""
    posts = Post.objects.filter(category__slug=category_slug)
    tag = Tag.objects.filter(slug=tag_slug).first()
    if tag:
        for post in posts:
            post.tags.add(tag)
    return posts.count()


def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move posts from source category to target, delete source. Returns count."""
    target_cat = Category.objects.filter(slug=target_slug).first()
    source_cat = Category.objects.filter(slug=source_slug).first()
    if not source_cat or not target_cat:
        return 0
    
    posts = Post.objects.filter(category=source_cat)
    count = posts.count()
    posts.update(category=target_cat)
    source_cat.delete()
    return count


def delete_inactive_users_comments() -> int:
    """Delete all comments written by inactive users. Returns count."""
    _, deleted_info = Comment.objects.filter(author__is_active=False).delete()
    return deleted_info.get("blog.Comment", 0)


# ==========================================
# Level 10 — select_related and prefetch_related
# ==========================================

def published_feed() -> list[str]:
    """50 newest published posts as 'title | author email | category name' (1 query)."""
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .order_by("-created_at")[:FEED_LIMIT]
    )
    feed = []
    for p in posts:
        cat_name = p.category.name if p.category else UNCATEGORIZED_LABEL
        feed.append(f"{p.title} | {p.author.email} | {cat_name}")
    return feed


def newest_posts_with_tags() -> list[str]:
    """20 newest posts as 'title: tag1, tag2' (at most 2 queries)."""
    posts = (
        Post.objects.order_by("-created_at")
        .prefetch_related("tags")[:NEWEST_TAGS_LIMIT]
    )
    result = []
    for p in posts:
        tag_names = ", ".join([t.name for t in p.tags.all()])
        result.append(f"{p.title}: {tag_names}")
    return result


def categories_with_published_posts() -> dict[str, list[str]]:
    """Dict of category name to list of published post titles (at most 2 queries)."""
    from django.db.models import Prefetch
    published_prefetch = Prefetch(
        "post_set",
        queryset=Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at"),
        to_attr="pub_posts"
    )
    categories = Category.objects.prefetch_related(published_prefetch).order_by("name")
    
    result = {}
    for cat in categories:
        result[cat.name] = [p.title for p in cat.pub_posts]
    return result


# ==========================================
# Level 11 — Subquery and Exists
# ==========================================

def posts_with_last_comment() -> QuerySet[Post]:
    """Published posts annotated with last_comment body."""
    from django.db.models import Subquery
    latest_comment = Comment.objects.filter(
        post=OuterRef("pk")
    ).order_by("-created_at").values("body")[:1]

    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).annotate(
        last_comment=Subquery(latest_comment)
    )


def posts_with_staff_comments() -> QuerySet[Post]:
    """Posts with at least one staff comment (using Exists)."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"),
        author__is_staff=True
    )
    return Post.objects.filter(Exists(staff_comments))


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Users whose newest post is a draft."""
    from django.db.models import OuterRef, Subquery
    latest_post_status = Post.objects.filter(
        author=OuterRef("pk")
    ).order_by("-created_at").values("status")[:1]

    return User.objects.annotate(
        latest_post_status=Subquery(latest_post_status)
    ).filter(latest_post_status=Post.Status.DRAFT)


# --- Словарь для команды управления ---
QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}