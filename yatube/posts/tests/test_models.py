from django.test import TestCase

from ..models import Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser_YP')
        cls.group = Group.objects.create(
            title='Имя Группы Тест',
            slug='Тестовый Слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост который явно длиннее 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostsModelTest.group
        post = PostsModelTest.post
        self.assertEqual(self.group.__str__(), group.title)
        self.assertEqual(self.post.__str__(), post.text[:15])

    def test_labels(self):
        """verbose_name полей модели совпадает с ожидаемым."""
        verbose = self.post._meta.get_field('author').verbose_name
        self.assertEqual(verbose, 'Автор')

        verbose2 = self.group._meta.get_field('title').verbose_name
        self.assertEqual(verbose2, 'название группы')

    def test_help_text(self):
        """help_text полей модели совпадает с ожидаемым."""
        help_text = self.post._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Введите текст поста')

        help_text2 = self.group._meta.get_field('title').help_text
        self.assertEqual(help_text2, 'Введите название группы')
