from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост в котором больше пятнадцати символов',
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у группы корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_post_have_correct_object_names(self):
        """Проверяем, что у поста корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))
