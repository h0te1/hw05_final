import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=('Группа 1'),
            slug='slug1',
        )
        cls.group_2 = Group.objects.create(
            title=('Группа 2'),
            slug='slug2',
        )
        cls.user = User.objects.create_user('Nikita')
        cls.post = Post.objects.create(
            author=cls.user,
            text='пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Новая записть создаётся"""
        Post.objects.all().delete()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.first()
        self.assertTrue(Post.objects.count() == 1)
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.user.username,)))
        self.assertEqual(post_1.author, self.user)
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(post_1.group.id, form_data['group'])

    def test_guest_new_post(self):
        """неавторизоанный не может создавать посты"""
        count_posts_1 = Post.objects.count()
        form_data = {
            'text': 'Пост от неавторизованного пользователя',
            'group': self.group.id
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Пост от неавторизованного пользователя').exists())
        count_posts_2 = Post.objects.count()
        self.assertEqual(count_posts_1, count_posts_2)

    def test_authorized_edit_post(self):
        """авторизованный может редактировать"""
        form_data = {
            'text': 'Измененный текст',
            'group': self.group_2.id,
        }
        post_2 = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        edited = Post.objects.first()
        response = self.client.get(reverse(
            'posts:group_list', args=(self.group.slug,)))
        self.assertEqual(post_2.status_code, 200)
        self.assertEqual(edited.text, form_data['text'])
        self.assertEqual(edited.author, self.post.author)
        self.assertEqual(edited.id, self.post.id)
        self.assertEqual(edited.group, self.group_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.context.get('page_obj').object_list), 0)
        self.assertTrue(Post.objects.count() == 1)
