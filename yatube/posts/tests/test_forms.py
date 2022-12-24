import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser_YP')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """
        Тест что при отправке валидной формы со страницы создания
        поста reverse('posts:create_post') создаётся новая запись в базе данных
        """
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='test_img.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                author=self.user,
                text='Тестовый пост',
            ).exists()
        )

    def test_edit_post(self):
        """
        Тест: при отправке валидной формы со страницы редактирования
        поста reverse('posts:post_edit', args=('post_id',))
        происходит изменение поста с post_id в базе данных.
        """
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='test_img.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                author=self.user,
                text='Тестовый пост',
                image='posts/test_img.gif',
            ).exists()
        )

    def test_guest_user_cant_create_post(self):
        """
        Тест: не авторизированный пользователь не может публиковать запись.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст в форму поста',
            'group': self.group.id,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                group=self.group,
                author=self.user,
                text='Текст в форму поста'
            ).exists()
        )

    def test_post_detail_add_new_comment(self):
        """Тест создания пользователем комментария"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'тестовый коммент',
            'author': self.user,
            'post': self.post,
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='тестовый коммент').exists()
        )

    def test_guest_cant_comment(self):
        """Тест гость не может комментаровать"""
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'тестовый коммент',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Comment.objects.filter(
            text='тестовый коммент').exists()
        )
