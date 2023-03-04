from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('auth')
        cls.group = Group.objects.create(
            title='группа',
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='пост в котором больше пятнадцати символов',
        )

    def test_group_have_correct_object_names(self):
        """у группы корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_post_have_correct_object_names(self):
        """у поста корректно работает __str__."""
        self.assertEqual(self.post.text[:15], str(self.post))
