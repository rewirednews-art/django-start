import feedparser
import logging
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone

from articles.models import FeedSource, Article

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch RSS feeds from FeedSource objects and store new articles."

    def handle(self, *args, **options):
        sources = FeedSource.objects.all()

        if not sources:
            self.stdout.write(
                self.style.WARNING("No FeedSource entries found.")
            )
            return

        from django.contrib.auth import get_user_model

        User = get_user_model()

        for source in sources:
            self.stdout.write(
                f"Fetching feed: {source.name} ({source.url})"
            )

            try:
                feed = feedparser.parse(source.url)
            except Exception as e:
                logger.error(
                    "Error fetching %s: %s",
                    source.url,
                    e,
                )
                continue

            if feed.get("bozo"):
                logger.warning(
                    "Malformed feed at %s",
                    source.url,
                )
                continue

            for entry in feed.get("entries", []):
                title = entry.get("title", "").strip()

                if not title:
                    continue

                # RSS/Atom permalink
                permalink = entry.get("link", "").strip()

                # RSS excerpt/description.
                description = (
                    entry.get("description")
                    or entry.get("summary")
                    or ""
                ).strip()

                # Full article content supplied by the RSS feed.
                content = ""

                feed_content = entry.get("content")

                if feed_content and isinstance(feed_content, list):
                    content = feed_content[0].get("value", "").strip()

                # Fall back to summary/description if the feed does not
                # provide a full-content element.
                if not content:
                    content = (
                        entry.get("summary")
                        or entry.get("description")
                        or ""
                    ).strip()

                # RSS published date, falling back to Atom updated date.
                pub_date = None

                if entry.get("published_parsed"):
                    try:
                        pub_date = datetime(
                            *entry.published_parsed[:6],
                            tzinfo=dt_timezone.utc,
                        )
                    except (TypeError, ValueError):
                        logger.warning(
                            "Could not parse published date for: %s",
                            title,
                        )

                elif entry.get("updated_parsed"):
                    try:
                        pub_date = datetime(
                            *entry.updated_parsed[:6],
                            tzinfo=dt_timezone.utc,
                        )
                    except (TypeError, ValueError):
                        logger.warning(
                            "Could not parse updated date for: %s",
                            title,
                        )

                slug = slugify(title)

                # Ensure uniqueness of slug; append counter if needed.
                base_slug = slug
                counter = 1

                while Article.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Use first author name if available.
                author_name = entry.get("author")

                # Use a generic system user if no author;
                # fall back to first superuser, then first user.
                if author_name:
                    user, _ = User.objects.get_or_create(
                        username=author_name
                    )
                else:
                    user = User.objects.filter(
                        is_superuser=True
                    ).first()

                    if not user:
                        user = User.objects.first()

                if not user:
                    self.stdout.write(
                        self.style.ERROR(
                            "No users exist. Cannot create article: "
                            f"{title}"
                        )
                    )
                    continue

                # Create article if it doesn't already exist
                # (preserving the existing title/author behavior).
                if not Article.objects.filter(
                    title=title,
                    author=user,
                ).exists():

                    article = Article.objects.create(
                        title=title,
                        slug=slug,
                        author=user,
                        content=content,
                        description=description,
                        pubDate=pub_date,
                        permalink=permalink,
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created article: {title}"
                        )
                    )

                else:
                    self.stdout.write(
                        f"Skipping existing article: {title}"
                    )

            # Update last_fetched timestamp.
            source.last_fetched = timezone.now()
            source.save()

        self.stdout.write(
            self.style.SUCCESS("Feed fetching completed.")
        )
