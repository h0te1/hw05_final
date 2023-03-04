from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('user')
        cls.group = Group.objects.create(
            title='Группа 1',
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.revers_and_args = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_edit', (self.post.id,)),
            ('posts:post_create', None),
        )

    def test_pages_response_template(self):
        """соответствие reverse и template"""
        template_response_code = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
        )
        for name, args, template in template_response_code:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertTemplateUsed(response, template)

    def test_url_to_template(self):
        """соответствие reverse и url"""
        revers_args_template = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.user.username,),
             f'/profile/{self.user.username}/'),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_edit', (self.post.id,),
             f'/posts/{self.post.id}/edit/'),
            ('posts:post_create', None, '/create/'),
        )
        for name, args, url in revers_args_template:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), url)

    def test_urls_to_author(self):
        """все url доступны автору"""
        for name, args in self.revers_and_args:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)

    def test_urls_to_logined_user(self):
        """не все url доступны не автору"""
        not_author = User.objects.create(username='not_author')
        self.authorized_client.force_login(not_author)
        for name, args in self.revers_and_args:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                if name == 'posts:post_edit':
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_urls_to_guest_client(self):
        """все url доступны незарегестрированному пользователю"""
        redirect_list = [
            'posts:post_edit',
            'posts:post_create'
        ]
        for name, args in self.revers_and_args:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                if name in redirect_list:
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)

    def test_unexisting_page_404(self):
        """Страница /unexisting_page/ возвращает 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
