from rest_framework.serializers import (ModelSerializer, CharField,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)

from django.conf import settings
from recipes.models import Ingredient, IngredientInRecipesAmount, Recipe, Tag
from users.models import Follow, User
from .fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .validators import validate_username


class IngredientSerializer(ModelSerializer):
    """Сериализатор объектов типа Ingredients. Список ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class IngredientsInRecipeReadSerializer(ModelSerializer):
    """Сериализатор ингредиентов в рецептах."""

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipesAmount
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class TagSerializer(ModelSerializer):
    """Сериализация объектов типа Tags. Список тегов."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class UserSerializer(ModelSerializer):
    """Сериализация объектов типа User. Просмотр пользователя."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):

        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.follower.filter(author=obj).exists()
        )


class UserCreateSerializer(ModelSerializer):
    """Сериализатор создания объекта типа User."""
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            validate_username
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ],
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',)
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False},
        }

    def validate(self, value):
        email = value['email']
        username = value['username']
        if (User.objects.filter(email=email).exists()
                and not User.objects.filter(username=username).exists()):
            raise serializers.ValidationError(
                'Попробуйте указать другую электронную почту.'
            )
        if (User.objects.filter(username=username).exists()
                and not User.objects.filter(email=email).exists()):
            raise serializers.ValidationError(
                'Попробуйте указать другое имя пользователя.'
            )
        return value


class ShoppingListFavoiriteSerializer(ModelSerializer):
    """Сериализация объектов типа shoppingLists. Лист покупок."""

    image = Base64ImageField(read_only=True)
    name = ReadOnlyField()
    cooking_time = ReadOnlyField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class FollowSerializer(ModelSerializer):
    """Сериализация объектов типа Follow. Проверка подписки."""

    email = ReadOnlyField(source='author.email')
    id = ReadOnlyField(source='author.id')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Follow.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                'Нельзя подписаться на пользователя повторно!'
            )
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get(
            'recipes_limit', settings.RECIPES_LIMIT
        )
        queryset = Recipe.objects.filter(author=obj.author)[:int(limit)]
        return ShoppingListFavoiriteSerializer(queryset, many=True).data


class IngredientsInRecipeWriteSerializer(ModelSerializer):
    """Сериализатор добавления ингредиента в рецепт."""
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipesAmount
        fields = (
            'id',
            'amount',
        )


class RecipesReadSerializer(ModelSerializer):
    """Сериализация объектов типа Recipes. Чтение рецептов."""

    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    ingredients = IngredientsInRecipeReadSerializer(
        required=True, many=True, source='recipe'
    )
    tags = TagSerializer(
        many=True
    )
    author = UserSerializer(
        read_only=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.favorite_recipes.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.shopping_recipes.filter(user=user).exists()
        )


class RecipesWriteSerializer(ModelSerializer):
    """Сериализация объектов типа Recipes. Запись рецептов."""

    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientsInRecipeWriteSerializer(many=True,
                                                     source='recipe')
    image = Base64ImageField()
    name = CharField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, data):
        """Валидация ингредиентов при заполнении рецепта."""
        ingredients = data['recipe']
        cooking_time = data['cooking_time']
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise ValidationError({
                    'Ингредиенты должны быть уникальными'
                })
            ingredients_list.append(ingredient_id)
            amount = ingredient['amount']
            if int(amount) == settings.ZERO_MIN_VALUE:
                raise ValidationError({
                    'Количество ингридиента не может быть = 0'
                })
        if int(cooking_time) == settings.ZERO_MIN_VALUE:
            raise ValidationError({
                'Время приготовления не может быть = 0!'
            })
        return data

    def validate_name(self, value):
        if len(value) > 200:
            raise ValidationError({
                'Название рецепта должно содержать не более 200 символов!'
            })
        return value

    def create_update_ingredient(self, ingredients, recipe):
        IngredientInRecipesAmount.objects.bulk_create(
            [IngredientInRecipesAmount(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount'),
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe')
        user = self.context.get('request').user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        self.create_update_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if (
            request.user.is_authenticated
            and request.user.id == instance.author_id
        ):
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags)
            ingredients = validated_data.pop('recipe')
            instance.ingredients.clear()
            self.create_update_ingredient(ingredients, instance)
            return super().update(instance, validated_data)
        return instance
