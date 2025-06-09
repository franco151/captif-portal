#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import stat

def ensure_media_permissions():
    """Vérifie et corrige les permissions du dossier media."""
    media_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
    qr_codes_dir = os.path.join(media_root, 'qr_codes')
    
    # Créer les dossiers s'ils n'existent pas
    os.makedirs(media_root, exist_ok=True)
    os.makedirs(qr_codes_dir, exist_ok=True)
    
    # Définir les permissions (lecture et écriture pour tous)
    permissions = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | \
                 stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | \
                 stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
    
    # Appliquer les permissions
    os.chmod(media_root, permissions)
    os.chmod(qr_codes_dir, permissions)

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BestConnect.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Vérifier et corriger les permissions du dossier media
    ensure_media_permissions()
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
