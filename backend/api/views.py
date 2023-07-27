from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (FavoriteReceipe, Ingredient,
                            Recipe, ShoppingCart,
                            Tag, User)
from users.models import Follow

from .filters import RecipeFilter, IngredientFilter
from .permission import IsAuthorOrAuthenticatedOrReadOnly, IsSubscribeOnly
from .serializers import (FavouriteRecipeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, TagSerializer,
                          UserSerializer, RecipeReadSerializer)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс взаимодействия с моделью Tags. Вьюсет для списка тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ModelViewSet):
    """Класс взаимодействия с Ingredients. Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientFilter]
    search_fields = ('^name', )
    pagination_class = None


class UsersViewSet(DjoserUserViewSet):
    """Класс взаимодействия с Users. Вьюсет для пользователя."""

    http_method_names = ['GET', 'POST', 'HEAD', 'DELETE']
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Дает доступ к определенным эндпоинтам только аутентифицированным
        пользователям и разрешает метод delete только для своих подписок."""

        if self.request.method == 'DELETE':
            return [IsSubscribeOnly()]
        if self.action in ['me', 'subscriptions', 'subscribe']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request):
        """Просмотр своих подписок."""

        user = self.request.user
        user_following = User.objects.filter(following__user=user)
        page = self.paginate_queryset(user_following)
        serializer = FollowSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'], detail=True,
    )
    def subscribe(self, request, id=None):
        """Подписка и отписка на других пользователей."""

        user = self.request.user
        following = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = FollowSerializer(
                following, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=following)
            return Response(serializer.data, status=HTTP_201_CREATED)

        if request.method == 'DELETE':
            serializer = FollowSerializer(
                following, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.filter(user=user, following=following).delete()
            return Response(status=HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Класс взаимодействия с моделью Recipes. Вьюсет для рецептов."""

    http_method_names = ['GET', 'POST', 'HEAD', 'PATCH', 'DELETE']
    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('ingredients', 'tags').all()
    )
    permission_classes = [IsAuthorOrAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""

        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление и удаление рецепта в избанное."""

        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavouriteRecipeSerializer(
            recipe, data=request.data,
            context={
                'request': request,
                'action_name': 'favorite'
            }
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            FavoriteReceipe.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=HTTP_201_CREATED)
        if request.method == 'DELETE':
            FavoriteReceipe.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок."""

        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavouriteRecipeSerializer(
            recipe, data=request.data,
            context={
                'request': request,
                'action_name': 'shopping_cart'
            }
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=HTTP_201_CREATED)
        if request.method == 'DELETE':
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'], detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Отдает пользователю список для покупок в виде текстового файла."""

        shopping_list_text = ShoppingCart.shopping_list_text(self, request)
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        response.write(shopping_list_text)
        return response        
