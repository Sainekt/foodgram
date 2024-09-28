import random

from recipes.models import Recipe


def check_unique(link):
    try:
        Recipe.objects.get(short_link=link)
    except Recipe.DoesNotExist:
        return link
    return False


def get_link():
    dictionary = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz234567890"
    length = 10
    link = False
    while not link:
        link = check_unique(
            ''.join(random.choice(dictionary) for _ in range(length))
        )
    return link
