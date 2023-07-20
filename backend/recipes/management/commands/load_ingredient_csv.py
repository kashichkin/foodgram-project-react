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
                upload_list = []
                for row in file_reader:
                    name, measurement_unit = row
                    new = Ingredient(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                    if new not in upload_list:
                        upload_list.append(new)
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
