from distutils.util import strtobool

import django_filters
from recipes.models import Recipe
from rest_framework import filters


class RecipeFilter(django_filters.FilterSet):
    CHOICES = (
        ('0', 'False'),
        ('1', 'True')
    )
    # в версиях django 3+ дефолтные значения boolean - 2 и 3, а не 1 и 0
    # фронт отправляет именно 1 и 0, а не True и False
    author = django_filters.CharFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.TypedChoiceFilter(
        choices=CHOICES,
        coerce=strtobool,
        method='get_is_favorited'
    )
    is_in_shopping_cart = django_filters.TypedChoiceFilter(
        choices=CHOICES,
        coerce=strtobool,
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favoriterecipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(recipeincart__user=self.request.user)
        return queryset


class IngredientFilter(filters.SearchFilter):
    search_param = 'name'
