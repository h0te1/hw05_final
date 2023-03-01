import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Follow, User
from posts.forms import PostForm
from yatube.settings import PAGE_LIMIT

NUMBER_OF_POSTS = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='test_slug'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def context_help(self, otvet, page_object=True):
        if page_object is True:
            context_in = otvet.context.get('page_obj')[0]
        else:
            context_in = otvet.context.get('post')

        post_text_0 = context_in.text
        post_author_0 = context_in.author.username
        post_group_0 = context_in.group.title
        post_image_0 = context_in.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_image_0, self.post.image)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # проверяет контекст на главной странице
    def test_context_index(self):
        """Контекст в index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.context_help(otvet=response)

    # Проверяет контекст на странице групп
    def test_context_group_list(self):
        """Контекст в group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.context_help(otvet=response)
        self.assertEqual(response.context.get('group'), self.group)
        self.assertEqual(response.context.get('group').slug, 'test_slug')

    # Проверяет контекст на странице профиля
    def test_context_profile(self):
        """Контекст в profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,)))

        self.context_help(otvet=response)
        self.assertEqual(response.context.get('author'), self.user)

    # Проверяет содержимое страницы с деталями поста
    def test_post_detail(self):
        """тест на работоспособность post_detail"""
        response = self.authorized_client.get((
            reverse('posts:post_detail', args=(self.post.id,))
        ))
        self.context_help(otvet=response, page_object=False)

    # правильность типов полей формы для редактирования и создания поста
    def test_post_edit_context(self):
        """Шаблон редактирования и создания поста"""
        edit_and_create = {
            ('posts:post_edit', (self.post.id,)),
            ('posts:post_create', None)
        }
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for name, args in edit_and_create:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                form_form = response.context.get('form')
                self.assertIn('form', response.context)
                self.assertIsInstance(form_form, PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    # Пост не попал в другую группу
    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        Group.objects.create(
            title='Вторая группа',
            slug='test_slug_2'
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', args=('test_slug_2',)))

        self.assertEqual(
            len(response.context.get('page_obj').object_list), 0)

        post = self.post
        self.assertTrue(post.group)
        response = self.authorized_client.get(
            reverse('posts:group_list', args=('test_slug',)))
        self.context_help(otvet=response)

    def test_add_comment(self):
        self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            {'text': "тестовый комментарий"},
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertContains(response, 'тестовый комментарий')
        self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            {'text': "комментарий от гостя"},
            follow=True
        )
        response = self.client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertNotContains(response, 'комментарий от гостя')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title=('Заголовок тестовой группы'),
            slug='test_slug',
            description='Тестовое описание')
        cls.posts = []
        for number in range(NUMBER_OF_POSTS):
            cls.posts.append(Post(
                text=f'Тестовый пост {number}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.user = User.objects.create_user(username='mobpsycho100')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator(self):
        """Проверка обеих страниц паджинатора"""
        list_urls = (
            ('posts:index', None,),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author.username,)),
        )
        pages = (
            ('?page=1', PAGE_LIMIT),
            ('?page=2', NUMBER_OF_POSTS - PAGE_LIMIT)
        )
        for name, args in list_urls:
            with self.subTest(url=name):
                for page, lenght in pages:
                    response = self.authorized_client.get(
                        reverse(name, args=args) + page)
                    self.assertEqual(
                        len(response.context.get('page_obj').object_list
                            ), lenght)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name')
        cls.post = Post.objects.create(
            text='Тестовая запись для создания поста',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(id=self.post.id)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_state.content, third_state.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовая запись для тестирования ленты'
        )

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """Подписка"""
        self.client_auth_follower.get(
            reverse('posts:profile', args=(self.user_following.username,))
        )
        # Подписываемся
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        # Проверяем, что подписка существует
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Отписка"""
        self.client_auth_follower.get(
            reverse('posts:profile', args=(self.user_following.username,))
        )
        # Сначала подписываемся
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        self.assertEqual(Follow.objects.all().count(), 1)
        # Потом отписываемся
        Follow.objects.get(
            user=self.user_follower,
            author=self.user_following
        ).delete()
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        example = Post.objects.first()
        response = self.client_auth_follower.get(reverse('posts:follow_index'))
        post_in_follow = response.context['page_obj'][0]
        self.assertEqual(post_in_follow, example)
        # в качестве неподписанного пользователя проверяем собственную ленту
        response = self.client_auth_following.get(
            reverse('posts:follow_index'))
        lenght = len(response.context.get('page_obj').object_list)
        self.assertEqual(lenght, 0)
