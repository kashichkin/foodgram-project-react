import csv

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            file_name = 'recipes/data/ingredients.csv'
            with open(file_name, 'r', encoding='utf-8') as file:
                print(file)
                file_reader = csv.reader(file, delimiter=',')
                upload_list = [Ingredient(*raw) for raw in file_reader]
                Ingredient.objects.bulk_create(upload_list)
                self.stdout.write(
                    self.style.SUCCESS('Ингредиенты успешно загружены')
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('Ошибка')
            )
            raise CommandError(
                'В директории recipes/data нет файла'
            )
