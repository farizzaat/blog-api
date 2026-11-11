from datetime import date
from typing import Any
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import CaptureQueriesContext
from django.db import connection

from apps.blog.queries import QUERIES
from apps.blog.models import Post, Category, Tag
from apps.auths.models import User

# Образцы аргументов для запросов, которым они требуются
SAMPLE_ARGUMENTS = {
    4: {"slug": Post.objects.first().slug if Post.objects.exists() else "test"},
    8: {"word": "django"},
    9: {"domain": "example.com"},
    11: {"slugs": list(Category.objects.values_list("slug", flat=True)[:2])},
    12: {"year": 2026, "month": 11},
    13: {"days": 365},
    14: {"start": date(2025, 1, 1), "end": date(2026, 12, 31)},
    15: {"email": User.objects.filter(post__status="published").values_list("email", flat=True).first() or "user@example.com"},
    16: {"tag_slug": Tag.objects.first().slug if Tag.objects.exists() else "python"},
    17: {"category_slug": Category.objects.first().slug if Category.objects.exists() else "django"},
    21: {"first_slug": "python", "second_slug": "django"},
    22: {"text": "django"},
    34: {"min_posts": 1},
    37: {"text": "a"},
    40: {"name": "New Awesome Tag"},
    41: {"days": 30},
    42: {"category_slug": "django", "tag_slug": "api"},
    43: {"source_slug": "old-cat", "target_slug": "new-cat"},
}

PREVIEW_ROWS = 5


class Command(BaseCommand):
    help = "Runs blog ORM queries and displays performance and results."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--number", type=int, help="Run a specific query number")
        parser.add_argument("--sql", action="store_true", help="Print SQL queries")

    def handle(self, *args: Any, **options: Any) -> None:
        number = options.get("number")
        print_sql = options.get("sql")

        queries_to_run = [number] if number is not None else [q for q in QUERIES.keys() if q not in range(40, 45)]

        for q_num in queries_to_run:
            if q_num not in QUERIES:
                raise CommandError(f"Query number {q_num} does not exist.")

            func = QUERIES[q_num]
            args_dict = SAMPLE_ARGUMENTS.get(q_num, {})

            with CaptureQueriesContext(connection) as context:
                result = func(**args_dict)
                # Вынуждаем QuerySet выполниться внутри контекста за счет превращения в список/ленту
                evaluated_result = result
                if hasattr(result, "__iter__") and not isinstance(result, (str, dict, tuple)):
                    evaluated_result = list(result)

            num_queries = len(context.captured_queries)

            self.stdout.write(f"\n{q_num} {func.__name__} — {num_queries} SQL query")
            if print_sql:
                for sql_item in context.captured_queries:
                    self.stdout.write(self.style.WARNING(sql_item["sql"]))

            # Красивый вывод результата согласно ТЗ
            if isinstance(evaluated_result, (list, tuple)):
                total_rows = len(evaluated_result)
                preview = evaluated_result[:PREVIEW_ROWS]
                self.stdout.write(f"Result (first {PREVIEW_ROWS} of {total_rows} rows): {preview}")
            else:
                self.stdout.write(f"Result: {evaluated_result}")