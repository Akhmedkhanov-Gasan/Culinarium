from django.db.models import Count, Q

from .models import Recipe


def get_active_recipes():
    return (
        Recipe.objects
        .filter(is_active=True)
        .select_related("category")
        .prefetch_related("tags", "recipe_ingredients__ingredient")
    )


def search_recipes(query):
    return (
        get_active_recipes()
        .filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(instructions__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(recipe_ingredients__ingredient__name__icontains=query)
        )
        .distinct()
    )


def search_recipes_by_ingredients(ingredient_names):
    return (
        get_active_recipes()
        .filter(recipe_ingredients__ingredient__name__in=ingredient_names)
        .annotate(matched_ingredients=Count("recipe_ingredients__ingredient"))
        .order_by("-matched_ingredients", "title")
        .distinct()
    )
