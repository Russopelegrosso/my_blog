from .models import Post, Comment
from django.forms.models import ModelForm


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Напишите текст поста',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Напишите комментарий',
        }
