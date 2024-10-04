from common.constants import RECIPE, USER
from utils.pdf_gen import get_pdf


def get_shopping_list(user):
    data = {}
    shopping_cart = user.shopping_cart.prefetch_related(
        USER, RECIPE
    )
    ingredients_in_recipes = [
        i.recipe.recipe_ingredients.all() for i in shopping_cart
    ]
    for ingredients in ingredients_in_recipes:
        for ingredient in ingredients:
            if ingredient.ingredient not in data:
                data[ingredient.ingredient] = 0
            data[ingredient.ingredient] += ingredient.amount
    file = get_pdf(data)
    return file
