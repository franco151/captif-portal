from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
import base64

class WiFiCredentials(models.Model):
    class Meta:
        app_label = 'portal'

    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    payment = models.OneToOneField('payments.Payment', on_delete=models.CASCADE, related_name='wificredentials', null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"user_{get_random_string(8)}"
        if not self.password:
            self.password = get_random_string(12)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
        self.generate_qr_code()

    def generate_qr_code(self):
        if not self.qr_code:
            # Créer le contenu du QR code
            wifi_config = f"WIFI:T:WPA;S:BestConnect;P:{self.password};;"
            
            # Générer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wifi_config)
            qr.make(fit=True)

            # Créer l'image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Sauvegarder l'image
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f'qr_code_{self.username}.png'
            self.qr_code.save(filename, File(buffer), save=False)
            self.save()

    def get_qr_code_base64(self):
        if self.qr_code:
            with open(self.qr_code.path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        return None

    def __str__(self):
        return f"WiFiCredentials({self.username})"

class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.price}€" 