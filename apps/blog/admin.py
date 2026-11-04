from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin
from .models import Category, Tag, Post, Comment


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'posts_count')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(posts_count=Count('post'))

    def posts_count(self, obj):
        return obj.posts_count
    posts_count.short_description = 'Posts Count'


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'posts_count')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(posts_count=Count('post'))

    def posts_count(self, obj):
        return obj.posts_count
    posts_count.short_description = 'Posts Count'


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'status')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    search_fields = ('body',)