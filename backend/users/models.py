from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ADMIN = 'admin'
    USER = 'user'

    CHOICES = (
        (USER, 'user'),
        (ADMIN, 'admin'),
    )
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=150, choices=CHOICES, default='user')
    password = models.CharField(max_length=150)
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == 'admin'


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
    )
