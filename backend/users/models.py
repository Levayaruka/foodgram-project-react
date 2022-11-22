from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ADMIN = 'admin'
    USER = 'user'

    CHOICES = (
        (USER, 'user'),
        (ADMIN, 'admin'),
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты')
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Имя пользователя')
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя')
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия')
    role = models.CharField(
        max_length=150,
        choices=CHOICES,
        default=USER)
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль')
    is_subscribed = models.BooleanField(
        verbose_name='Подписан',
        default=False)

    class Meta:
        ordering = ('id', )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    USERNAME_FIELD = 'email'
    # -согласно документации django, необходимо использовать
    # константу 'USERNAME_FIELD' как обозначение поля уникального
    # идентификатора в кастомной модели пользователя.
    # с фронта для аутентификации запрашивается именно email,
    # в документации описывается, что его можно использовать
    # https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#django.contrib.auth.models.CustomUser.USERNAME_FIELD
    # -пишется после перечисления полей

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'user'), name='unique_subscription'),
        )
