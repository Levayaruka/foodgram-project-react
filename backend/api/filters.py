from distutils.util import strtobool

import django_filters
from recipes.models import Favorite, Cart, Recipe
from rest_framework import filters


class RecipeFilter(django_filters.FilterSet):
    CHOICES = (
        ('0', 'False'),
        ('1', 'True')
    ) 
    #в новых версиях Джанго boolean игнорирует 1 и 0, посылаемые фронтом
    #поэтому нужна константа и данная реализация
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
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        favorites_pk = Favorite.objects.filter(
            user=self.request.user).values_list('pk', flat=True)
        return queryset.filter(favoriterecipe__in=favorites_pk)

    def get_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        carts_pk = Cart.objects.filter(
            user=self.request.user).values_list('pk', flat=True)
        return queryset.filter(recipeincart__in=carts_pk)


class IngredientFilter(filters.SearchFilter):
    search_param = 'name'
