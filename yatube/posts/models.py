from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='название',
        help_text='Выберите группу для этого поста',
    )
    slug = models.SlugField(
        verbose_name='то, что будет в url',
        unique=True,
    )
    description = models.TextField(
        verbose_name='описание',
    )

    class Meta:
        verbose_name = 'Группа'

    def __str__(self):
        return f'{self.title}'


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
        blank=False,
        null=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
        help_text='вы можете вставить картинку'
    )
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)
        default_related_name = 'posts'
        verbose_name = 'пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return f'{self.text[:15]}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='комментарии',
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='комментарий',
        help_text='Введите текст',
        blank=False,
        null=True,
    )
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="follower",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="following",
    )
