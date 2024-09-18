from django.core.management.base import BaseCommand, CommandError
import json
from django.conf import settings
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import data from Json files into the database'

    def handle(self, *args, **kwargs):
        try:
            data_path = (
                settings.BASE_DIR / 'static' / 'data' / 'ingredients.json'
            )
            self.parse_json(data_path)

        except Exception as e:
            raise CommandError(f'Error importing data: {e}')

        self.stdout.write(self.style.SUCCESS('Successfully imported data'))

    def parse_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        with transaction.atomic():
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
