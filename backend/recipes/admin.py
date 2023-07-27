from django.contrib import admin

from .models import (FavoriteReceipe, Ingredient, IngredientAmount,
                     Recipe, ShoppingCart, Tag)


class IngredientAdmin(admin.ModelAdmin):
    """Админ панель управления ингредиентами."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Админ панель управления тегами."""
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class IngredientAmountAdmin(admin.ModelAdmin):
    """Отображение ингредиентов в админке."""
    list_display = ('amount', 'ingredient', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')


class IngredientInline(admin.TabularInline):
    """Отображение ингредиентов в рецептах в админ панели."""
    model = IngredientAmount
    extra = 1
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Админ панель управления рецептами."""
    list_display = ('name', 'author', 'in_favourite_count')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('name', 'author__username', 'tags__name')
    inlines = (IngredientInline,)
    readonly_fields = ('in_favourite_count', )
    empty_value_display = '-пусто-'

    def in_favourite_count(self, recipe):
        """Подсчитывает сколько раз рецепт добавлен в избранное."""
        return recipe.favourite.count()

    in_favourite_count.short_description = 'В избранном'


class FavoriteReceipeAdmin(admin.ModelAdmin):
    """Админ панель управления подписками."""
    list_display = ('pk', 'user', 'recipe',)
    list_filter = ('user__username', 'recipe__name',)
    search_fields = ('user__username', 'recipe__name')
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ панель списка покупок."""
    list_display = ('pk', 'user', 'recipe',)
    list_filter = ('user__username', 'recipe_name',)
    search_fields = ('user__username', 'recipe__name' )
    empty_value_display = '-пусто-'

admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientAmount, IngredientAmountAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(FavoriteReceipe, FavoriteReceipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)