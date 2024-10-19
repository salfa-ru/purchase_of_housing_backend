from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clean up outdated realties and schedule the next run."

    def handle(self, *args, **options):

        print ("Деактивация устаревших объявлений и регистрация такой-же HOURLY задачи")
        from realty.tasks import plan_mass_deactivation, expire_all_outdated_realties
        expire_all_outdated_realties()
        plan_mass_deactivation()
