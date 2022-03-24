from django.http.response import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientNameFilter, RecipeFilter
from .models import (Favorite, Follow, Ingredient, IngredientInRecipe,
                     Purchase, Recipe, Tag, User)
from .paginators import CustomPagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (FavoritesSerializer, CreateUpdateRecipeSerializer,
                          IngredientSerializer, PurchaseSerializer,
                          ListRecipeSerializer, ShowFollowerSerializer,
                          TagSerializer, UserSerializer, PurchaseRecipeSerializer)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = UserSerializer
    permission_classes = (IsOwnerOrAdminOrReadOnly,)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response({
                'errors': 'Вы не можете подписываться на самого себя.'
            }, status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response({
                'errors': 'Вы уже подписаны на данного пользователя.'
            }, status=status.HTTP_400_BAD_REQUEST)
        follow = Follow.objects.create(user=user, author=author)
        serializer = ShowFollowerSerializer(
            follow, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        subscribe = get_object_or_404(
            Follow, user=user, author=author
        )
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = ShowFollowerSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientsViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    filterset_class = IngredientNameFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if (self.action == 'list' or self.action == 'retrieve'):
            return ListRecipeSerializer
        return CreateUpdateRecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def recipe_post_method(self, AnyModel, user, pk):
        if AnyModel.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список.'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        AnyModel.objects.create(user=user, recipe=recipe)
        serializer = PurchaseRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def recipe_delete_method(self, AnyModel, user, pk):
        obj = AnyModel.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален.'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.recipe_post_method(
                Favorite, request.user, pk
            )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.recipe_delete_method(
            Favorite, request.user, pk
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.recipe_post_method(
                Purchase, request.user, pk
            )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.recipe_delete_method(
            Purchase, request.user, pk
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__purchases__user=user).values(
                'ingredient__name',
                'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (
            f'Список покупок({user.first_name})\n'
            f'{timezone.localtime().strftime("%d/%m/%Y %H:%M")}\n\n'
        )
        for ing in ingredients:
            shopping_list += (f'{ing["ingredient__name"]}: {ing["amount"]} '
                              f'{ing["ingredient__measurement_unit"]}\n')
        shopping_list += '\nFoodgram'
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
