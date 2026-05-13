from django.db.models import Count, Q

from .models import Ingredient, Recipe


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


def parse_ingredient_query(query):
    return [
        item.strip()
        for item in query.split(",")
        if item.strip()
    ]


def find_ingredients_by_query(query):
    ingredient_queries = parse_ingredient_query(query)

    if not ingredient_queries:
        return Ingredient.objects.none()

    filters = Q()

    for ingredient_query in ingredient_queries:
        filters |= Q(name__icontains=ingredient_query)

    return Ingredient.objects.filter(filters).order_by("name")


def search_recipes_from_ingredient_query(query):
    ingredients = find_ingredients_by_query(query)

    if not ingredients.exists():
        return Recipe.objects.none()

    return (
        get_active_recipes()
        .filter(recipe_ingredients__ingredient__in=ingredients)
        .annotate(matched_ingredients=Count("recipe_ingredients__ingredient", distinct=True))
        .order_by("-matched_ingredients", "title")
        .distinct()
    )


def format_recipe_for_message(recipe):
    if recipe is None:
        return "Рецепт не найден."

    recipe_ingredients = recipe.recipe_ingredients.select_related("ingredient")

    lines = [
        recipe.title,
        "",
    ]

    if recipe.description:
        lines.extend([recipe.description, ""])

    lines.append("Ингредиенты:")

    for item in recipe_ingredients:
        ingredient_line = f"- {item.ingredient.name}"

        amount_parts = []

        if item.amount is not None:
            amount_parts.append(f"{item.amount:g}")

        if item.unit:
            amount_parts.append(item.get_unit_display())

        if amount_parts:
            ingredient_line += f" — {' '.join(amount_parts)}"

        if item.note:
            ingredient_line += f" ({item.note})"

        lines.append(ingredient_line)

    lines.extend([
        "",
        "Приготовление:",
        recipe.instructions,
    ])

    return "\n".join(lines)


def format_recipe_list_for_message(recipes):
    recipes = list(recipes)

    if not recipes:
        return "Рецепты не найдены."

    lines = ["Найденные рецепты:"]

    for index, recipe in enumerate(recipes, start=1):
        details = []

        if recipe.cooking_time:
            details.append(f"{recipe.cooking_time} мин")

        if recipe.servings:
            details.append(f"{recipe.servings} порц.")

        recipe_line = f"{index}. {recipe.title}"

        if details:
            recipe_line += f" — {', '.join(details)}"

        lines.append(recipe_line)

    return "\n".join(lines)
