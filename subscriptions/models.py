from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
import os

class Plan(models.Model):
    DURATION_UNIT_CHOICES = [
        ('DAYS', 'Jours'),
        ('WEEKS', 'Semaines'),
        ('MONTHS', 'Mois'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField(help_text="Durée de l'abonnement")
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Forfait'
        verbose_name_plural = 'Forfaits'

    def __str__(self):
        return f"{self.name} - {self.duration} {self.get_duration_unit_display()} - {self.price} Ar"

    def get_duration_in_days(self):
        if self.duration_unit == 'DAYS':
            return self.duration
        elif self.duration_unit == 'WEEKS':
            return self.duration * 7
        elif self.duration_unit == 'MONTHS':
            return self.duration * 30
        return 0

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def generate_qr_code(self):
        print(f"[DEBUG] generate_qr_code called for user: {self.user.username}, subscription ID: {self.id}")
        
        # Vérifier si un QR code existe déjà DANS LA BASE ET SUR LE DISQUE
        if self.qr_code:
            qr_code_path = self.qr_code.path
            if os.path.exists(qr_code_path):
                print(f"[DEBUG] QR code file already exists at {qr_code_path} for subscription {self.id}.")
                return # Le QR code existe et le fichier est présent, on ne fait rien
            else:
                print(f"[DEBUG] QR code entry exists in DB but file missing at {qr_code_path}. Clearing DB entry.")
                # Si l'entrée existe en base mais pas le fichier, on l'efface pour régénérer
                self.qr_code.delete(save=False) # Supprime le fichier s'il existait (ici il n'existe pas, mais bonne pratique) et efface le champ en base
                self.qr_code = None # S'assurer que le champ est bien None

        # Créer le contenu du QR code (uniquement le nom d'utilisateur)
        qr_content = self.user.username
        print(f"[DEBUG] QR content: {qr_content}")
        
        # S'assurer que le dossier media/qr_codes existe
        qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        print(f"[DEBUG] QR codes directory: {qr_codes_dir}")
        os.makedirs(qr_codes_dir, exist_ok=True)
        print(f"[DEBUG] QR codes directory checked/created.")
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        print(f"[DEBUG] QR code generated.")
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        print(f"[DEBUG] QR code image created.")
        
        # Sauvegarder l'image dans un buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        print(f"[DEBUG] QR code image saved to buffer.")
        
        # Générer un nom de fichier unique
        # Utiliser user.pk au lieu de self.id car self.id pourrait être None si l'objet n'est pas encore sauvegardé
        # Cependant, dans save(), self.id devrait être défini. Gardons self.id pour la cohérence.
        filename = f'qr_code_{self.user.username}_{self.id}.png'
        print(f"[DEBUG] Generated filename: {filename}")
        
        # Sauvegarder le fichier
        try:
            self.qr_code.save(filename, File(buffer), save=False) # save=False car le save() final se fait après
            print(f"[DEBUG] qr_code.save called with filename: {filename}")
            # self.save() # Ne pas sauvegarder ici, la méthode save() appelante s'en chargera
            print(f"[DEBUG] QR code field updated in memory. File path should be: {self.qr_code.path}")
        except Exception as e:
            print(f"[DEBUG] Error during QR code file save: {e}")

    def generate_pdf(self):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="subscription_{self.user.username}.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # En-tête
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 50, "Reçu d'abonnement")
        
        # Informations utilisateur
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 100, f"Nom d'utilisateur: {self.user.username}")
        p.drawString(50, height - 120, f"Email: {self.user.email}")
        p.drawString(50, height - 140, f"Téléphone: {self.user.phone_number}")
        
        # Informations abonnement
        p.drawString(50, height - 180, f"Forfait: {self.plan.name}")
        p.drawString(50, height - 200, f"Prix: {self.plan.price} Ar")
        p.drawString(50, height - 220, f"Date de début: {self.start_date.strftime('%d/%m/%Y')}")
        p.drawString(50, height - 240, f"Date de fin: {self.end_date.strftime('%d/%m/%Y')}")
        
        # QR Code
        if self.qr_code:
            p.drawImage(self.qr_code.path, 50, height - 400, width=200, height=200)
        
        p.showPage()
        p.save()
        
        return response

    def check_status(self):
        """Vérifie et met à jour le statut de l'abonnement"""
        if self.is_active and self.end_date < timezone.now():
            self.is_active = False
            self.save(update_fields=['is_active'])
        return self.is_active

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Commenter l'appel à generate_qr_code ici
        # if is_new:
        #     print(f"[DEBUG] Calling generate_qr_code from save method for new subscription {self.id}")
        #     self.generate_qr_code() 