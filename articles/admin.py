from django.contrib import admin
from .models import Article, FeedSource

admin.site.register(FeedSource)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')
