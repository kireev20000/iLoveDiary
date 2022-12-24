# posts/tests/test_urls.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestUser_YP')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        group = Group.objects.create(
            title='Test Группа',
            slug='test-slug',
            description='Описание'
        )
        Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=group,
        )

    def test_post_detail_url_exists(self):
        """Проверка доступности страниц любому пользователю."""
        url_names = [
            '/',
            '/group/test-slug/',
            '/profile/TestUser_YP/',
            '/posts/1/',
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_exists_authorized(self):
        """Проверка доступности страниц авторизованному пользователю"""
        url_names = [
            '/',
            '/group/test-slug/',
            '/posts/1/',
            '/profile/TestUser_YP/',
            '/create/',

        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_exists_for_author(self):
        """Проверка доступности страниц только автору."""
        url_names = [
            '/posts/1/edit',
        ]

        for url in url_names:
            with self.subTest(url=url):
                post_user = get_object_or_404(User, username='TestUser_YP')
                if post_user == self.authorized_client:
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestUser_YP/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_404_is_exists(self):
        response = self.guest_client.get('/some_page_lolo/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
