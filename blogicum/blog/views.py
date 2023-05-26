from typing import Any
from django import http
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView)
from django.core.exceptions import PermissionDenied

from .forms import CreatePostForm, CreateCommentForm
from .models import Post, Comment, Category
from .utils import PostsQuerySetMixin, PostsEditMixin, CommentEditMixin

User = get_user_model()

PAGINATED_BY = 10


class PostDeleteView(PostsEditMixin, LoginRequiredMixin, DeleteView):

    success_url = reverse_lazy('blog:index')

    def delete(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if self.request.user != post.author:
            return redirect('blog:index')

        return super().delete(request, *args, **kwargs)


class PostUpdateView(PostsEditMixin, LoginRequiredMixin, UpdateView):
    form_class = CreatePostForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Post.objects.get(pk=self.kwargs['pk']).author:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

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

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not self.request.user.is_authenticated:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            raise PermissionDenied()

        form.instance.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentDeleteView(CommentEditMixin, LoginRequiredMixin, DeleteView):

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        if self.request.user != comment.author:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().delete(request, *args, **kwargs)


class CommentUpdateView(CommentEditMixin, LoginRequiredMixin, UpdateView):
    form_class = CreateCommentForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user != Comment.objects.get(
                pk=self.kwargs['comment_pk']).author:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.user != form.instance.author:
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
    paginate_by = PAGINATED_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context

    def get_queryset(self):
        return super().get_queryset().filter(
            category__slug=self.kwargs['category_slug'])


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
