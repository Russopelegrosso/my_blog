from django.shortcuts import render, get_object_or_404, redirect
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group,
                                          'page': page,
                                          'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            data = form.save(commit=False)
            data.author_id = request.user.id
            data.save()
            return redirect('index')
    return render(request, 'new_post.html',
                  {'form': form,
                   'header_name': 'Добавить запись'})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    profiles = author.posts.all()
    paginator = Paginator(profiles, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count = paginator.count
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user,
                                 author=author).exists():
            following = True
    follower_count = author.follower.count()
    following_count = author.following.count()
    return render(request,
                  'profile.html', {'page': page,
                                   'paginator': paginator,
                                   'following': following,
                                   'count': count,
                                   'follower_count': follower_count,
                                   'following_count': following_count,
                                   'author': author})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    count = post.author.posts.count()
    form = CommentForm()
    items = post.comments.all()
    return render(request, 'post.html', {'post': post, 'author': post.author,
                                         'count': count, 'form': form,
                                         'items': items, 'view': True})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(data=request.POST or None, files=request.FILES or None,
                    instance=post)
    if post.author == request.user:
        if request.method == 'POST':
            if form.is_valid():
                post = form.save(commit=False)
                post.save()
                return redirect('post', username=username,
                                post_id=post.id)
    return render(request, 'new_post.html',
                  {'form': form,
                   'header_name': 'Редактировать запись',
                   'post': post,
                   'edit_mode': True})


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            data = form.save(commit=False)
            data.post = post
            data.author = request.user
            data.save()
            return redirect('post', username=username, post_id=post_id)
    return render(request, 'comments.html',
                  {'form': form})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('profile', username=username)
