from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

from reviews.constans import (
    MIN_SCORE, MAX_SCORE, MIN_YEAR_PUB, NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH, CHAR_FIELD_MAX_LENGTH, SLUG_FIELD_MAX_LENGTH
)
from reviews.validators import validate_max_year


class UserRoles(models.TextChoices):

    USER = 'user', 'Пользователь'
    MODERATOR = 'moderator', 'Модератор'
    ADMINISTRATOR = 'admin', 'Администратор'


max_length = max(len(role) for role in UserRoles.choices)


class YamdbUser(AbstractUser):

    username = models.SlugField('Никнейм пользователя',
                                max_length=NAME_MAX_LENGTH,
                                unique=True)
    first_name = models.CharField('Имя пользователя',
                                  max_length=NAME_MAX_LENGTH,
                                  blank=True,)
    last_name = models.CharField('Фамилия',
                                 max_length=NAME_MAX_LENGTH,
                                 blank=True,)
    email = models.EmailField('Электронная почта',
                              unique=True,
                              max_length=EMAIL_MAX_LENGTH)
    bio = models.TextField('Биография', blank=True)
    confirmation_code = models.CharField('Код рeгистрации',
                                         max_length=NAME_MAX_LENGTH,
                                         blank=True)
    role = models.CharField('Роль пользователя',
                            choices=UserRoles.choices,
                            max_length=max_length,
                            default=UserRoles.USER)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:50]

    @property
    def is_admin(self):
        return (self.is_superuser
                or self.is_staff
                or self.role == UserRoles.ADMINISTRATOR.value)

    @property
    def is_moderator(self):
        return (self.role == UserRoles.MODERATOR.value
                or self.is_superuser)


class NameSlug(models.Model):
    name = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, verbose_name='имя'
    )
    slug = models.SlugField(
        max_length=SLUG_FIELD_MAX_LENGTH, verbose_name='идентификатор',
        unique=True
    )

    class Meta:
        abstract = True
        ordering = ('name',)
        verbose_name = 'имя и идентификатор'
        verbose_name_plural = 'Имена и идентификаторы'

    def __str__(self):
        return self.name


class Category(NameSlug):

    class Meta(NameSlug.Meta):
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Genre(NameSlug):

    class Meta(NameSlug.Meta):
        verbose_name = 'жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    year = models.SmallIntegerField(
        validators=[MinValueValidator(
            MIN_YEAR_PUB,
            message=f'Год выпуска не может быть раньше {MIN_YEAR_PUB}'
        ), validate_max_year],
        verbose_name='год выпуска',
        db_index=True
    )
    description = models.TextField(blank=True, default='')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.text[:20]


class TextAuthorPubDate(models.Model):
    text = models.TextField(verbose_name='текст')
    author = models.ForeignKey(
        YamdbUser, on_delete=models.CASCADE, related_name='%(class)ss',
        verbose_name='автор'
    )
    pub_date = models.DateTimeField(
        verbose_name='время публикации', auto_now_add=True, db_index=True
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:20]


class Review(TextAuthorPubDate):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='reviews',
        verbose_name='произведение'
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='оценка произведения',
        validators=[MinValueValidator(MIN_SCORE), MaxValueValidator(MAX_SCORE)]
    )

    class Meta(TextAuthorPubDate.Meta):
        verbose_name = 'отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = (
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='unique_title_author'
            ),
        )


class Comment(TextAuthorPubDate):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments',
        verbose_name='отзыв'
    )

    class Meta(TextAuthorPubDate.Meta):
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
