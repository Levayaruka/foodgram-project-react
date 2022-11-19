from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.models import CustomUser, Subscription
from recipes.models import (
    Recipe, Tag, RecipeTag,
    Cart, Favorite,
    Ingredient, RecipeIngredient
)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class RecipeIngredientShortSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name',
                  'last_name', 'password', 'is_subscribed']
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        else:
            return (
                Subscription.objects.filter(
                    user=request.user,
                ).exists()
                and request.user.is_authenticated
            )

    def create(self, validated_data):
        user = CustomUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(many=True,
        source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Cart.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Favorite


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return True
        else:
            return (
                Subscription.objects.filter(
                    user=request.user,
                    author__id=obj.author.id
                ).exists()
                and request.user.is_authenticated
            )

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        try:
            recipes_limit = int(
                self.context.get('request').query_params['recipes_limit']
            )
            recipes = Recipe.objects.filter(author=obj.author)[:recipes_limit]
        except Exception:
            recipes = Recipe.objects.filter(author=obj.author)
        serializer = RecipeShortSerializer(recipes, many=True,)
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Cart


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientShortSerializer(
        source='recipe_ingredient',
        many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'author', 'ingredients', 'tags',
                  'image', 'name', 'text', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        current_user = self.context['request'].user
        if Favorite.objects.filter(
                user=current_user,
                recipe=obj).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        current_user = self.context['request'].user
        if Cart.objects.filter(
                user=current_user,
                recipe=obj).exists():
            return True
        return False

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть больше 0')
            check_ingredient = Ingredient.objects.filter(
                id=ingredient['ingredient']['id'])
            if check_ingredient in ingredients_list:
                raise serializers.ValidationError(
                    'Продукты не могут повторяться')
            ingredients_list.append(check_ingredient)
        return value

    def add_ingredients_and_tags(self, tags, ingredients, recipe):
        for tag in tags:
            recipe.tags.add(tag)
            recipe.save()
        for ingredient in ingredients:
            if not RecipeIngredient.objects.filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe).exists():
                ingredientinrecipe = RecipeIngredient.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe)
                ingredientinrecipe.amount = ingredient['amount']
                ingredientinrecipe.save()
            else:
                RecipeIngredient.objects.filter(
                    recipe=recipe).delete()
                recipe.delete()
                raise serializers.ValidationError(
                    'Ингредиенты в рецепте не могут повторяться')
        return recipe

    def create(self, validated_data):
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        author = validated_data.get('author')
        ingredients = validated_data.pop('recipe_ingredient')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time
        )
        return self.add_ingredients_and_tags(tags, ingredients, recipe)

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredient')
        tags = validated_data.pop('tags')
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance = self.add_ingredients_and_tags(
            tags, ingredients, instance)
        super().update(instance, validated_data)
        instance.save()
        return instance
