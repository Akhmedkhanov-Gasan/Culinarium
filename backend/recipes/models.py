from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    cooking_time = models.PositiveIntegerField(help_text="Time in minutes")
    servings = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="recipes")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
    )
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["title"]

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    class UnitChoices(models.TextChoices):
        GRAM = "g", "г"
        KILOGRAM = "kg", "кг"
        MILLILITER = "ml", "мл"
        LITER = "l", "л"
        PIECE = "piece", "шт"
        TABLESPOON = "tbsp", "ст. л."
        TEASPOON = "tsp", "ч. л."
        PINCH = "pinch", "щепотка"

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    unit = models.CharField(
        max_length=20,
        choices=UnitChoices.choices,
        blank=True,
    )
    note = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        unique_together = ["recipe", "ingredient"]
        ordering = ["ingredient__name"]

    def __str__(self):
        parts = [self.ingredient.name]

        if self.amount is not None:
            parts.append(f"{self.amount:g}")

        if self.unit:
            parts.append(self.get_unit_display())

        if self.note:
            parts.append(f"({self.note})")

        return " ".join(parts)

