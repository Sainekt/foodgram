import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = 'Import data from Json files into the database'

    def handle(self, *args, **kwargs):
        path = settings.BASE_DIR / 'static' / 'data'
        try:
            data_ingredients = (
                path / 'ingredients.json'
            )
            self.import_ingredients(data_ingredients)
            data_tags = (
                path / 'tags.json'
            )
            self.import_tags(data_tags)

        except Exception as e:
            raise CommandError(f'Error importing data: {e}')

        self.stdout.write(self.style.SUCCESS('Successfully imported data'))

    def get_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def import_ingredients(self, file_path):
        data = self.get_file(file_path)
        with transaction.atomic():
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )

    def import_tags(self, file_path):
        data = self.get_file(file_path)
        with transaction.atomic():
            for item in data:
                Tag.objects.create(
                    name=item['name'],
                    slug=item['slug']
                )
