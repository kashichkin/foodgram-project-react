import re

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.forms import ValidationError

#from users.models import User

User = get_user_model()


def validate_color(value):
    """Проверяет цвет тега на уникальность и соответствие hex-color."""
    if (
        Tag.objects.filter(color=value.upper()).exists()
        or Tag.objects.filter(color=value.lower()).exists()
    ):
        raise ValidationError('Такой цвет уже занят другим тегом.')
    reg = re.compile(r'^#([a-f0-9]{6}|[A-F0-9]{6})$')
    if not reg.match(value):
        raise ValidationError(
            'Введите правильный 6-значный код hex-color в одном регистре.'
        )


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        verbose_name='Название',
        help_text='Название тэга',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='HEX-код',
        help_text='HEX-код для обозначения цвета тэга',
        max_length=7,
        unique=True,
        validators=[validate_color]
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        help_text='Имя для URL',
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(
        verbose_name='Ингредиент',
        help_text='Название ингредиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        help_text='Единица измерения количества ингредиента',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецептов."""

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги для рецепта',
        help_text='Теги по рецепту',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        help_text='Автор публикации рецепта',
        null=True,
        on_delete=models.SET_NULL,
        related_name='recipes'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        help_text='Ингредиенты для приготовления блюда',
        through='IngredientAmount',
        related_name='recipes'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200)
    image = models.ImageField(
        verbose_name='Фотография блюда',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        help_text='Время приготовления блюда',
        default=1,
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    """
    Вспомогательная модель для просмотра количества
    ингредиентов в рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        verbose_name='Ингредиент',
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        help_text='Необходимое количество данного ингредиента',
    )

    class Meta:
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe',
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient} - {self.amount}'


class FavoriteReceipe(models.Model):
    """Модель избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Рецепты в избранном'

    def __str__(self) -> str:
        return f'{self.recipe} - {self.user}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart',
            )
        ]

    def shopping_list_text(self, request):
        """Формирует список покупок."""

        ingredients_to_buy = IngredientAmount.objects.filter(
            recipe__in_shopping_cart__user=self.request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(
                    amount_sum=models.Sum('amount')
        ).order_by('ingredient__name').distinct()

        shopping_list_text = 'Список продуктов для покупки.\n'

        for index, ing in enumerate(ingredients_to_buy, 1):
            ingredient = ing['ingredient__name'].capitalize()
            amount = ing['amount_sum']
            measure = ing['ingredient__measurement_unit']
            if index < 10:
                intend = 2
            else:
                intend = 1
            new_line = (
                f'\n{index}.{" " * intend}{ingredient} - {amount} {measure}.'
            )
            shopping_list_text += new_line
        return shopping_list_text

    def __str__(self):
        return f'{self.user} - {self.recipe}'