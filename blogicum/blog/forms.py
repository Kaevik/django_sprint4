import datetime as dt

from django import forms
from django.utils import timezone

from .models import Post, Comment


class CreatePostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_date'].initial = dt.datetime.now(tz=timezone.utc)

    class Meta:
        model = Post
        fields = (
            'title',
            'image',
            'text',
            'pub_date',
            'location',
            'category',
            'is_published',
        )
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CreateCommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text', )
