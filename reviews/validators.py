import re

from django.core.exceptions import ValidationError
from django.utils import timezone

from reviews.constans import (
    NAME_MAX_LENGTH, RESERVE_USERNAME, EMAIL_MAX_LENGTH
)


def validate_username(username):
    pattern = r'^[\w.@+-]+\Z'

    if len(username) > NAME_MAX_LENGTH:
        raise ValidationError(
            f'Длина username больше допустимого - {NAME_MAX_LENGTH}!'
        )

    if username == RESERVE_USERNAME:
        raise ValidationError(
            f'Запрещено использовать username - {RESERVE_USERNAME}!'
        )

    if not re.match(pattern, username):
        forbidden_characters = re.findall(pattern, username)
        raise ValidationError(f'Логин содержит недопустимые символы: '
                              f'{forbidden_characters}')
    return username


def validate_email(email):
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValidationError(
            f'Длина email больше допустимого - {EMAIL_MAX_LENGTH}!'
        )
    return email


def validate_max_year(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(f'Год не может быть больше {current_year}.')
