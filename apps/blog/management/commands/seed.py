import time
import random
from typing import Any
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Tag, Post, Comment
from apps.auths.models import User

# Константы из ТЗ
SEED_PASSWORD = "SecureSeedPassword123!"
DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

CATEGORIES = [
    "Python", "Django", "DevOps", "Databases", 
    "Frontend", "Architecture", "Security", "Testing"
]

TAGS = [
    "API", "Async", "ORM", "Docker", "Kubernetes", 
    "PostgreSQL", "Redis", "Celery", "pytest", "Git", 
    "CI/CD", "Linux", "Security", "Performance", "WebSockets", 
    "GraphQL", "Microservices", "Refactoring", "Logging", "Tailwind"
]


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create")
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create")
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        fake = Faker()

        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        # Валидация аргументов из ТЗ
        if users_count < 0 or posts_count < 0 or comments_count < 0:
            raise CommandError("Number of users, posts, and comments cannot be negative.")

        if (posts_count > 0 or comments_count > 0) and users_count == 0 and User.objects.count() == 0:
            raise CommandError("Cannot create posts or comments without users.")

        if comments_count > 0:
            published_posts_exist = Post.objects.filter(status=Post.Status.PUBLISHED).exists()
            if posts_count == 0 and not published_posts_exist and clear:
                raise CommandError("Cannot create comments because there are no published posts.")

        # Очистка данных (--clear)
        if clear:
            self.stdout.write("Clearing existing data...")
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            # Удаляем всех, кроме суперпользователей
            User.objects.filter(is_superuser=False).delete()

        # 1. Создание категорий (проверка на существование)
        created_categories = []
        for cat_name in CATEGORIES:
            cat_slug = slugify(cat_name)
            category, created = Category.objects.get_or_create(
                slug=cat_slug,
                defaults={"name": cat_name}
            )
            created_categories.append(category)
        self.stdout.write(self.style.SUCCESS(f"Categories: {len(CATEGORIES)} processed"))

        # 2. Создание тегов
        created_tags = []
        for tag_name in TAGS:
            tag_slug = slugify(tag_name)
            tag, created = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={"name": tag_name}
            )
            created_tags.append(tag)
        self.stdout.write(self.style.SUCCESS(f"Tags: {len(TAGS)} processed"))

        # 3. Создание пользователей с bulk_create и уникальными email
        existing_emails = set(User.objects.values_list("email", flat=True))
        users_to_create = []
        
        hashed_password = make_password(SEED_PASSWORD)
        
        created_users_counter = 0
        while len(users_to_create) < users_count:
            first_name = fake.first_name()
            last_name = fake.last_name()
            base_email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            email = base_email
            counter = 1
            while email in existing_emails:
                email = f"{first_name.lower()}.{last_name.lower()}{counter}@example.com"
                counter += 1
            existing_emails.add(email)

            # Распределение: немного staff, часть неактивных
            is_staff = fake.boolean(chance_of_getting_true=10)
            is_active = fake.boolean(chance_of_getting_true=90)

            users_to_create.append(
                User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_staff=is_staff,
                    is_active=is_active,
                )
            )

        if users_to_create:
            User.objects.bulk_create(users_to_create)
            created_users_counter = len(users_to_create)

        all_users = list(User.objects.all())
        self.stdout.write(self.style.SUCCESS(f"Users: {created_users_counter} created"))

        # 4. Создание постов через bulk_create
        used_slugs = set(Post.objects.values_list("slug", flat=True))
        posts_to_create = []
        
        for _ in range(posts_count):
            if not all_users:
                break
            author = fake.random_element(all_users)
            title = fake.sentence().rstrip(".")
            
            # Уникальный slug с суффиксом при совпадении
            base_slug = slugify(title)
            slug = base_slug
            suffix = 1
            while slug in used_slugs:
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            used_slugs.add(slug)

            # Около 70% published, 30% draft
            status = random.choices(
                [Post.Status.PUBLISHED, Post.Status.DRAFT],
                weights=[0.7, 0.3],
                k=1
            )[0]

            # Около 10% без категории
            has_category = fake.boolean(chance_of_getting_true=90)
            category = fake.random_element(created_categories) if (has_category and created_categories) else None

            body = "\n\n".join(fake.paragraphs(nb=3))

            posts_to_create.append(
                Post(
                    author=author,
                    title=title,
                    slug=slug,
                    body=body,
                    category=category,
                    status=status,
                )
            )

        created_posts = []
        if posts_to_create:
            Post.objects.bulk_create(posts_to_create)
            created_posts = list(Post.objects.all().order_by("-id")[:posts_count])

        # Привязка тегов (0-5 случайных тегов через .tags.set)
        for post in created_posts:
            if created_tags:
                selected_tags = fake.random_elements(
                    elements=created_tags,
                    length=fake.random_int(min=0, max=min(5, len(created_tags))),
                    unique=True
                )
                post.tags.set(selected_tags)

        self.stdout.write(self.style.SUCCESS(f"Posts: {len(created_posts)} created"))

        # 5. Создание комментариев (только на опубликованные посты)
        published_posts = [p for p in created_posts if p.status == Post.Status.PUBLISHED]
        comments_to_create = []

        if published_posts and all_users:
            for _ in range(comments_count):
                post = fake.random_element(published_posts)
                author = fake.random_element(all_users)
                body = " ".join(fake.sentences(nb=fake.random_int(min=1, max=3)))

                comments_to_create.append(
                    Comment(
                        post=post,
                        author=author,
                        body=body,
                    )
                )

            if comments_to_create:
                Comment.objects.bulk_create(comments_to_create)

        self.stdout.write(self.style.SUCCESS(f"Comments: {len(comments_to_create)} created"))

        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed_time:.2f} seconds"))