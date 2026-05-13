from django.contrib import admin

from .models import Category, Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ["ingredient"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "cooking_time", "servings", "is_active"]
    list_filter = ["category", "tags", "is_active"]
    search_fields = ["title", "description", "instructions"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["category", "tags"]
    inlines = [RecipeIngredientInline]
