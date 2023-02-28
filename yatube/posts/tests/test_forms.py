from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.group_2 = Group.objects.create(
            title=('Заголовок для 2 тестовой группы'),
            slug='test_slug_2',
            description='Тестовое описание 2'
        )
        cls.user = User.objects.create_user(username='Nikita')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Новая записть создаётся"""
        Post.objects.all().delete()
        count_posts = Post.objects.count()
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
        self.assertEqual(Post.objects.count(), count_posts + 1)
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
        count_posts_1 = Post.objects.count()
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
        count_posts_2 = Post.objects.count()
        self.assertEqual(post_2.status_code, 200)
        self.assertEqual(edited.text, form_data['text'])
        self.assertEqual(edited.author, self.post.author)
        self.assertEqual(edited.id, self.post.id)
        self.assertEqual(edited.group, self.group_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.context.get('page_obj').object_list), 0)
        self.assertEqual(count_posts_1, count_posts_2)
