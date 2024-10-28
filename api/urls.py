from django.urls import include, path
from rest_framework import routers

from api.views import (UsersViewSet, CategoryViewSet,
                       GenreViewSet, TitleViewSet,
                       ReviewViewSet, CommentViewSet,
                       singup, token_jwt)

v1_router = routers.DefaultRouter()
v1_router.register(
    r'categories',
    CategoryViewSet,
    basename='categories'
)
v1_router.register(
    r'genres',
    GenreViewSet,
    basename='genres'
)
v1_router.register(
    r'titles',
    TitleViewSet,
    basename='titles'
)
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)
v1_router.register(
    'users',
    UsersViewSet,
    basename='users'
)

auth_patterns = [
    path('signup/', singup, name='sign_up'),
    path('token/', token_jwt, name='get_token'),
]

v1_urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include(auth_patterns)),
]

urlpatterns = [
    path('v1/', include(v1_urlpatterns)),
]
