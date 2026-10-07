from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Article(models.Model):
    """Model representing a news article or blog post."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    category = models.CharField(max_length=100, blank=True, help_text='RSS category if available')

    # RSS/feed metadata
    description = models.TextField(blank=True, default="")
    pubDate = models.DateTimeField(null=True, blank=True)
    permalink = models.URLField(max_length=2048, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.title


class FeedSource(models.Model):
    """Model representing an RSS feed source for news aggregation."""

    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(unique=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feed Source"
        verbose_name_plural = "Feed Sources"

    def __str__(self):
        return self.name
