from pathlib import Path
from django.urls import reverse_lazy

from .conf import BLOG_DEBUG, BLOG_SECRET_KEY

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = BLOG_SECRET_KEY
DEBUG = BLOG_DEBUG

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "unfold",  
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.auths",
    "apps.blog",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # <--- Добавили путь для кастомного дашборда
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"


AUTH_USER_MODEL = "auths.User"


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Almaty"

USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Конфигурация Django Unfold
UNFOLD = {
    "SITE_TITLE": "Blog API Admin",
    "SITE_HEADER": "Blog API Management",
    "SITE_SUBHEADER": "Homework #2 Dashboard",
    "SITE_SYMBOL": "speed",
    
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },

    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",

    "SITE_DROPDOWN": [
        {
            "title": "GitHub Repository",
            "link": "https://github.com",
            "icon": "code",
        },
        {
            "title": "Unfold Docs",
            "link": "https://unfoldadmin.com",
            "icon": "book",
        },
    ],

    "COMMAND": {
        "show_history": True,
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": lambda request: reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": lambda request: reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": "Comments",
                        "icon": "comment",
                        "link": lambda request: reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "folder",
                        "link": lambda request: reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "label",
                        "link": lambda request: reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": lambda request: reverse_lazy("admin:auths_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "lock",
                        "link": lambda request: reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },

    "TABS": [
        {
            "models": [
                "blog.post",
            ],
            "items": [
                {
                    "title": "All Posts",
                    "link": lambda request: reverse_lazy("admin:blog_post_changelist"),
                },
                {
                    "title": "Published",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=published",
                },
                {
                    "title": "Drafts",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=draft",
                },
            ],
        },
    ],

    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
}