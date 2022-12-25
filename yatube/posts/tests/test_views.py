import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser_YP')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.upload = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.upload,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': (reverse('posts:index')),
            'posts/group_list.html': (reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'})),
            'posts/profile.html': reverse('posts:profile', args=[
                get_object_or_404(User, username='TestUser_YP')]),
            'posts/post_detail.html': (reverse(
                'posts:post_detail', kwargs={'post_id': '1'})),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(response.context['author'], self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context.get('post'), self.post)

    def test_create_post_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_right_group_exists(self):
        """Проверка создания поста в index, group, profile"""
        urls_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for url in urls_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 1)
                self.assertEqual(response.context['page_obj'][0], self.post)
                self.assertEqual(
                    response.context['page_obj'][0].image,
                    self.post.image
                )

    def test_post_does_not_appear_in_diff_group(self):
        """
        Тест что пост не попал в группу, для которой не был предназначен.
        """
        Group.objects.create(slug='test-slug_2')
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug_2'}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_index_cache(self):
        """Тест работоспособности кэша."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='тестовый пост',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_old.content, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_old.content, response_new.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser_YP')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='описание группы'
        )
        cls.post = Post.objects.bulk_create(
            [
                Post(
                    text=f'текст поста {i}',
                    author=cls.user,
                    group=cls.group
                )
                for i in range(0, 13)
            ]
        )
        cls.url_names_keys = [reverse('posts:index'),
                              reverse('posts:group_list',
                                      kwargs={'slug': cls.group.slug}),
                              reverse('posts:profile', args=[cls.user]),
                              ]

    def test_first_page_contains(self):
        """Тест Пагинатора для Первой странцы"""
        post_on_page = (10 for _ in range(11))
        dict_urls_names = dict(zip(self.url_names_keys, post_on_page))
        for value, expected in dict_urls_names.items():
            with self.subTest(value=post_on_page):
                response = self.client.get(value + '?page=1')
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_contains_three_records(self):
        """Тест Пагинатора для Второй странцы"""
        posts_on_2d_page = (3 for _ in range(4))
        dict_urls_names = dict(zip(self.url_names_keys, posts_on_2d_page))
        for value, expected in dict_urls_names.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='TestUser_1')
        cls.user_following = User.objects.create_user(username='TestUser_2')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client = Client()
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Тест пользователь может подписаться на автора"""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Тест пользователь может отписаться"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_can_follower_see_new_posts(self):
        """Тест новые посты появляются в ленте подписок"""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)

    def test_user_cannot_follow_twice_same_author(self):
        """Тест один пользователь не может фоловить одного автора дважды"""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.count(), follower_count + 1)
