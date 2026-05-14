from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from asgiref.sync import sync_to_async

from recipes.services import (
    format_recipe_for_message,
    format_recipe_list_for_message,
    get_active_recipes,
    search_recipes_from_ingredient_query,
    get_active_recipe_by_id,
)

from bot.state import (
    WAITING_FOR_INGREDIENTS,
    clear_user_state,
    get_user_state,
    set_user_state,
)

BUTTON_ALL_RECIPES = "Все рецепты"
BUTTON_SEARCH_BY_INGREDIENTS = "Поиск по ингредиентам"
BUTTON_HELP = "Помощь"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Culinarium — бот для поиска рецептов из домашней базы.\n\n"
        "Выбери действие на клавиатуре ниже или используй команды:\n"
        "/recipes — список рецептов\n"
        "/recipe 1 — открыть рецепт по id\n"
        "/search куриное, картошка — поиск по ингредиентам",
        reply_markup=build_main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Для работы с ботом нажмите на кнопки 'Все рецепты' или 'Поиск по ингредиентам' \n"
    )


async def recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipes_list = await get_active_recipes_list()

    if not recipes_list:
        await update.message.reply_text("Рецепты не найдены.")
        return

    await update.message.reply_text(
        "Выбери рецепт:",
        reply_markup=build_recipe_keyboard(recipes_list),
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()

    if not query:
        await update.message.reply_text(
            "Напиши ингредиенты после команды.\n"
            "Например: /search куриное, картошка"
        )
        return

    recipes_list = await get_search_recipes_list(query)

    if not recipes_list:
        await update.message.reply_text("Рецепты не найдены.")
        return

    await update.message.reply_text(
        "Нашел рецепты. Выбери нужный:",
        reply_markup=build_recipe_keyboard(recipes_list),
    )


async def recipe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # print("Callback data:", query.data)
    await query.answer()

    recipe_id = int(query.data.split(":", 1)[1])
    message = await get_recipe_message(recipe_id)

    await query.message.reply_text(message)


def build_recipe_keyboard(recipes):
    keyboard = [
        [InlineKeyboardButton(recipe.title, callback_data=f"recipe:{recipe.id}")]
        for recipe in recipes
    ]

    return InlineKeyboardMarkup(keyboard)


class Command(BaseCommand):
    help = "Run Telegram bot"

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")

        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("recipes", recipes))
        application.add_handler(CommandHandler("search", search))
        application.add_handler(CommandHandler("recipe", recipe))
        application.add_handler(CallbackQueryHandler(recipe_callback, pattern=r"^recipe:\d+$"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

        self.stdout.write(self.style.SUCCESS("Bot started"))

        application.run_polling(allowed_updates=Update.ALL_TYPES)

# @sync_to_async
# def get_recipes_message():
#     recipe_queryset = get_active_recipes()
#     return format_recipe_list_for_message(recipe_queryset)

@sync_to_async
def get_recipe_message(recipe_id):
    recipe = get_active_recipe_by_id(recipe_id)
    return format_recipe_for_message(recipe)


# @sync_to_async
# def get_search_message(query):
#     recipe_queryset = search_recipes_from_ingredient_query(query)
#     recipes_list = list(recipe_queryset)
#
#     if not recipes_list:
#         return "Рецепты не найдены."
#
#     if len(recipes_list) == 1:
#         return format_recipe_for_message(recipes_list[0])
#
#     return format_recipe_list_for_message(recipes_list)


@sync_to_async
def get_active_recipes_list():
    return list(get_active_recipes())


@sync_to_async
def get_search_recipes_list(query):
    return list(search_recipes_from_ingredient_query(query))


@sync_to_async
def set_user_state_async(user_id, state):
    set_user_state(user_id, state)


@sync_to_async
def get_user_state_async(user_id):
    return get_user_state(user_id)


@sync_to_async
def clear_user_state_async(user_id):
    clear_user_state(user_id)


async def recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Укажи id рецепта.\n"
            "Например: /recipe 1"
        )
        return

    try:
        recipe_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Id рецепта должен быть числом.\n"
            "Например: /recipe 1"
        )
        return

    message = await get_recipe_message(recipe_id)
    await update.message.reply_text(message)


def build_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BUTTON_ALL_RECIPES, BUTTON_SEARCH_BY_INGREDIENTS],
            [BUTTON_HELP],
        ],
        resize_keyboard=True,
    )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == BUTTON_ALL_RECIPES:
        await recipes(update, context)
        return

    if text == BUTTON_HELP:
        await help_command(update, context)
        return

    if text == BUTTON_SEARCH_BY_INGREDIENTS:
        await set_user_state_async(user_id, WAITING_FOR_INGREDIENTS)
        await update.message.reply_text(
            "Напиши ингредиенты через запятую.\n"
            "Например: куриное, картошка"
        )
        return

    state = await get_user_state_async(user_id)

    if state == WAITING_FOR_INGREDIENTS:
        await clear_user_state_async(user_id)

        recipes_list = await get_search_recipes_list(text)

        if not recipes_list:
            await update.message.reply_text("Рецепты не найдены.")
            return

        await update.message.reply_text(
            "Нашел рецепты. Выбери нужный:",
            reply_markup=build_recipe_keyboard(recipes_list),
        )
        return

    await update.message.reply_text(
        "Не понял сообщение. Выбери действие на клавиатуре или используй /help."
    )
