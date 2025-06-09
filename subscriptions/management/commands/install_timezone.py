from django.core.management.base import BaseCommand
import subprocess
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Installe les tables de fuseaux horaires MySQL'

    def handle(self, *args, **options):
        # Chemin vers le fichier timezone.sql dans le dossier mysql
        mysql_dir = os.path.join(settings.BASE_DIR, 'mysql')
        timezone_file = os.path.join(mysql_dir, 'timezone.sql')

        # Créer le dossier mysql s'il n'existe pas
        if not os.path.exists(mysql_dir):
            os.makedirs(mysql_dir)

        # Télécharger le fichier timezone.sql
        self.stdout.write('Téléchargement des tables de fuseaux horaires...')
        subprocess.run([
            'curl',
            'https://raw.githubusercontent.com/mysql/mysql-server/master/mysql-test/std_data/zoneinfo.sql',
            '-o',
            timezone_file
        ])

        # Importer les tables dans MySQL
        self.stdout.write('Importation des tables de fuseaux horaires...')
        subprocess.run([
            'mysql',
            '-u', settings.DATABASES['default']['USER'],
            '-p' + settings.DATABASES['default']['PASSWORD'],
            settings.DATABASES['default']['NAME'],
            '<',
            timezone_file
        ], shell=True)

        self.stdout.write(self.style.SUCCESS('Tables de fuseaux horaires installées avec succès!')) 