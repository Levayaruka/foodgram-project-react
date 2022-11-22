from http import HTTPStatus
from os import path

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import CustomUser, Subscription

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer)

app_path = path.realpath(path.dirname(__file__))
font_path = path.join(app_path, 'arial.ttf')


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class ListRetrieveViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    pass


class ListCreateDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    pass


class TagsViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny, )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageLimitPagination


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, IngredientFilter)
    pagination_class = None
    search_fields = ('^name', )


class SubscriptionViewSet(ListRetrieveViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscribeViewSet(CreateDestroyViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        author_id = self.kwargs.get('user_id')
        author = get_object_or_404(CustomUser, id=author_id)
        if author == request.user:
            return Response(
                'Вы не можете подписаться на себя',
                status=HTTPStatus.BAD_REQUEST
            )
        if Subscription.objects.filter(
                author=author, user=self.request.user).exists():
            return Response(
                'Вы уже подписаны на данного автора',
                status=HTTPStatus.BAD_REQUEST
            )
        Subscription.objects.create(author=author, user=self.request.user)
        return Response(status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs.get('user_id')
        author = get_object_or_404(CustomUser, id=author_id)
        get_object_or_404(
            Subscription,
            author=author,
            user=self.request.user
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(user=self.request.user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class DownloadShoppingCartViewSet(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    @staticmethod
    def canvas_method(shopping_list):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename = "shopping_list.pdf"')
        begin_position_x, begin_position_y = 150, 700
        sheet = canvas.Canvas(response, pagesize=A4)
        pdfmetrics.registerFont(
            TTFont('arial', font_path)
        )
        sheet.setFont('arial', 28)
        sheet.setTitle('Список покупок')
        sheet.drawString(
            begin_position_x,
            begin_position_y + 35,
            'Список покупок: '
        )
        sheet.setFont('arial', 18)
        for number, item in enumerate(shopping_list, start=1):
            if begin_position_y < 150:
                begin_position_y = 750
                sheet.showPage()
                sheet.setFont('arial', 18)
            sheet.drawString(
                begin_position_x,
                begin_position_y,
                f'{number}.  {item["ingredient__name"]} - '
                f'{item["ingredient_total"]}'
                f' {item["ingredient__measurement_unit"]}'
            )
            begin_position_y -= 30
        sheet.showPage()
        sheet.save()
        return response

    def get(self, request):
        result = RecipeIngredient.objects.filter(
            recipe__recipeincart__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').order_by(
                'ingredient__name').annotate(ingredient_total=Sum('amount'))
        return self.canvas_method(result)


class ShoppingCartViewSet(CreateDestroyViewSet):
    serializer_class = ShoppingCartSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            Cart.objects.create(user=self.request.user, recipe=recipe)
        except ValidationError:
            return Response(
                'Рецепт уже есть в списке ваших покупок',
                status=HTTPStatus.BAD_REQUEST
            )
        serializer = RecipeShortSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            Cart, user=self.request.user, recipe=recipe).delete()
        return Response(status=HTTPStatus.NO_CONTENT)
