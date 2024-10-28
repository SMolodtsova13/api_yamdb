from http.client import BAD_REQUEST, OK

from django.db.models import Avg
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets, status, mixins
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

# from api_yamdb.settings import DOMAIN_NAME
from api.filters import TitleFilter
from api.permissions import (
    IsAdminOrReadOnly, IsAdmin, IsAuthorOrAdminOrModerator
)
from api.serializers import (
    CategorySerializer, GenreSerializer, TitleSerializer, ReviewSerializer,
    CommentSerializer, SignUpSerializer, GetTokenSerializer,
    YamdbUserSerializer, YamdbUserSerializerWithoutRole,
    TitleCreateUpdateSerializer
)
from reviews.constans import RESERVE_USERNAME
from reviews.models import Category, Genre, Title, Review

User = get_user_model()


class CategoryGenreMixinViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'


class CategoryViewSet(CategoryGenreMixinViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CategoryGenreMixinViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleMixinViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')


class TitleViewSet(TitleMixinViewSet):
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')
    ).order_by(*Title._meta.ordering)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ('year', 'rating')
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.action in {'create', 'partial_update'}:
            return TitleCreateUpdateSerializer
        return TitleSerializer


class ReviewCommentMixinViewSet(TitleMixinViewSet):
    permission_classes = (
        IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrModerator
    )


class ReviewViewSet(ReviewCommentMixinViewSet):
    serializer_class = ReviewSerializer

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(ReviewCommentMixinViewSet):
    serializer_class = CommentSerializer

    def get_review(self):
        return get_object_or_404(
            Review,
            id=self.kwargs['review_id'],
            title_id=self.kwargs['title_id']
        )

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())


@api_view(('POST',))
@permission_classes((permissions.AllowAny,))
def singup(request):
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = request.data['username']
    email = request.data['email']
    user, is_created = User.objects.get_or_create(username=username,
                                                  email=email)

    confirmation_code = default_token_generator.make_token(user)
    send_mail('Код подтверждения регистрации',
              f'Ваш код подтвержения: {confirmation_code}',
              settings.DEFAULT_FROM_EMAIL,
              [user.email],
              fail_silently=False)
    return Response(request.data, status=status.HTTP_200_OK)


@api_view(('POST',))
@permission_classes((permissions.AllowAny,))
def token_jwt(request):
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(User,
                             username=serializer.validated_data['username'])
    if default_token_generator.check_token(
        user, serializer.validated_data['confirmation_code']
    ):
        token = AccessToken.for_user(user)
        return Response({'token': str(token)}, status=OK)
    return Response(serializer.errors, status=BAD_REQUEST)


class UsersViewSet(viewsets.ModelViewSet):
    serializer_class = YamdbUserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'username'
    search_fields = ('username',)

    @action(detail=False, methods=['patch'], url_path='me',
            url_name=RESERVE_USERNAME, permission_classes=(IsAuthenticated,))
    def patch(self, request):
        # Использование partial позволяет сериализовать только те данные,
        # которые были переданы в request.data,
        # и игнорировать все остальные поля объекта.
        serializer = YamdbUserSerializerWithoutRole(request.user,
                                                    data=request.data,
                                                    partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, url_path='me', url_name=RESERVE_USERNAME,
            permission_classes=(IsAuthenticated,))
    def get(self, request):
        # partial=True используется для того,
        # чтобы избежать проверки на наличие данных в запросе,
        # так как метод GET не должен требовать никакие данные для валидации.
        serializer = YamdbUserSerializer(request.user,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid()
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        if request.method == 'PUT':
            raise MethodNotAllowed(method='PUT',
                                   detail='Метод запрещен!')
        return super().update(request, *args, **kwargs)
