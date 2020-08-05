from django.core.cache import cache
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Post, Group, Follow
from django.core.files import File

User = get_user_model()


class TestPost(TestCase):

    def setUp(self):
        self.auth_client = Client()
        self.client_logout = Client()
        self.user = User.objects.create_user(
            username='Barney',
        )
        self.other_user = User.objects.create_user(
            username='Lola',
        )
        self.auth_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup'
        )

    def test_profile(self):
        response = self.client_logout.get(
            reverse('profile', kwargs=dict(username=self.user.username)))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        cache.clear()
        response = self.auth_client.post(reverse('new_post'),
                                         data={'text': 'post for test'})
        self.assertEqual(response.status_code, 302)
        response = self.auth_client.get(reverse('index'))
        self.assertContains(response, 'post for test', status_code=200)

    def test_new_post_logout(self):
        response = self.client_logout.post(reverse('new_post'),
                                           data={'text': 'text for test'})
        posts = Post.objects.all()
        for post in posts:
            self.assertNotEqual(post.text, 'text for test')
        self.assertRedirects(response, '/auth/login/?next=/new/', 302)

    def test_post_published(self):
        cache.clear()
        with open('media/posts/25990_002.jpg', 'rb') as img:
            post = Post.objects.create(text='test text', author=self.user,
                                       group=self.group, image=File(img))
        self.check_all_page(post.id, post.text, post.author, post.group)

    def test_post_edit(self):
        cache.clear()
        with open('media/posts/25990_002.jpg', 'rb') as img:
            post = Post.objects.create(text='test text', author=self.user,
                                       group=self.group, image=File(img))
        edit_text = 'edit test text'
        post_id = post.id
        new_group = Group.objects.create(
            title='Рафаелло',
            slug='rafaello'
        )
        self.auth_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': post_id,
                }
            ),
            data={'group': new_group.id, 'text': edit_text}
        )
        self.check_all_page(post.id, edit_text, post.author, new_group)

    def check_all_page(self, post_id, text, author, group):
        for url in (
                reverse('index'),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('post', kwargs={
                    'username': self.user.username,
                    'post_id': post_id,
                }),
        ):
            response = self.auth_client.get(url)
            self.assertContains(response, 'img')
            if 'paginator' in response.context:
                posts = response.context['paginator'].object_list[0]
                self.assertEqual(Post.objects.count(), 1)
            else:
                posts = response.context['post']
            self.assertEqual(posts.text, text)
            self.assertEqual(posts.author, author)
            self.assertEqual(posts.group, group)

    def test_404(self):
        response = self.client.get('/not-found/')
        self.assertEqual(response.status_code, 404)

    def test_cache_index(self):
        response = self.auth_client.get(reverse('index'))
        self.auth_client.post(
            reverse('new_post'),
            data={
                'text': 'cache test',
                'group': self.group.id
            }
        )
        self.assertNotContains(response, 'cache test')

    def test_follow_and_unfollow(self):
        before_follow = Follow.objects.all().count()
        Follow.objects.create(
            user=User.objects.get(
                username=self.user),
            author=User.objects.get(
                username=self.other_user.username))

        follower = Follow.objects.filter(
            user=User.objects.get(
                username=self.user),
            author=User.objects.get(
                username=self.other_user.username))
        after_follow = Follow.objects.all().count()
        self.assertEqual(before_follow + 1, after_follow)
        follower.delete()
        after_unfollow = Follow.objects.all().count()
        self.assertEqual(after_follow - 1, after_unfollow)

    def test_post_following(self):
        Post.objects.create(text='Follower text', author=self.other_user)
        response = self.auth_client.get(reverse('follow_index'), follow=True)
        self.assertNotContains(response, 'Follower text')
        self.auth_client.post(
            reverse('profile_follow',
                    kwargs={
                        'username': self.other_user,
                    }),
        )
        response = self.auth_client.get(reverse('follow_index'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Follower text')

    def test_add_comment_logout(self):
        post = Post.objects.create(text='Follower text',
                                   author=self.other_user)
        response = self.client_logout.post(
            reverse('add_comment',
                    kwargs={
                        'username': self.other_user,
                        'post_id': post.id
                    }),
            data={
                'text': 'comment test',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'comment test')

