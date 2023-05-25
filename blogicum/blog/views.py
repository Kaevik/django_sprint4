from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_list_or_404, get_object_or_404
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.core.exceptions import PermissionDenied

from .forms import CreatePostForm, CreateCommentForm
from .models import Post, Comment
from .utils import PostsQuerySetMixin, PostsEditMixin

User = get_user_model()

PAGINATED_BY = 10


class PostDeleteView(PostsEditMixin, LoginRequiredMixin, DeleteView):

    success_url = reverse_lazy('blog:index')

    def get_object(self):
        obj = super().get_object()
        if obj.author != self.request.user:
            raise PermissionDenied()
        return obj


class PostUpdateView(PostsEditMixin, LoginRequiredMixin, UpdateView):
    form_class = CreatePostForm

    def get_object(self):
        obj = super().get_object()
        if obj.author != self.request.user:
            raise PermissionDenied()
        return obj


class PostCreateView(PostsEditMixin, LoginRequiredMixin, CreateView):
    form_class = CreatePostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            kwargs={
                'username': self.request.user.username,
            })


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CreateCommentForm

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            raise PermissionDenied()

        form.instance.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_pk'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Comment.objects.get(
                pk=self.kwargs['comment_pk']).author:

            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CreateCommentForm
    pk_url_kwarg = 'comment_pk'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Comment.objects.get(
                pk=self.kwargs['comment_pk']).author:

            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.request.user != form.instance.author:
            raise PermissionDenied()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class AuthorProfileListView(PostsQuerySetMixin, ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = PAGINATED_BY

    def get_queryset(self):
        if self.request.user.username == self.kwargs['username']:
            return Post.objects.select_related(
                'category',
                'author',
                'location').filter(author__username=self.kwargs['username'])

        return super().get_queryset().filter(
            author__username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class BlogIndexListView(PostsQuerySetMixin, ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = PAGINATED_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Лента записей'
        return context

    def get_queryset(self):
        return super().get_queryset()


class BlogCategoryListView(PostsQuerySetMixin, ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    allow_empty = False
    paginate_by = PAGINATED_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = context['post_list'][0].category
        return context

    def get_queryset(self):
        return get_list_or_404(
            super().get_queryset(),
            category__slug=self.kwargs['category_slug']
        )


class PostDetailView(PostsQuerySetMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CreateCommentForm()
        context['comments'] = Comment.objects.filter(
            post__pk=self.kwargs['pk'])
        return context

    def get_queryset(self):
        return super().get_queryset().prefetch_related('comments__author')
