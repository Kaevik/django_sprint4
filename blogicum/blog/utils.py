import datetime as dt

from django.utils import timezone

from .models import Post


class PostsQuerySetMixin:
    def get_queryset(self):
        return Post.objects.select_related(
            'category',
            'author',
            'location',
        ).prefetch_related(
            'comments',
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=dt.datetime.now(tz=timezone.utc)
        )


class PostsEditMixin:
    model = Post
    template_name = 'blog/create.html'
    queryset = Post.objects.select_related('author', 'location', 'category')
