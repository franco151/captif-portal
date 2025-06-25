# Créer ce fichier à la racine du projet

import serial
import time
import re
import django
import os
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from payments.models import SMSTransaction, Payment
from portal.models import WiFiCredentials
from subscriptions.models import Plan
from django.utils import timezone

class SMSHandler:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            self.send_command('AT')
            self.send_command('AT+CMGF=1')  # Mode texte SMS
            self.send_command('AT+CNMI=1,2,0,0,0')  # Notification SMS
            print("Modem GSM connecté et configuré")
            return True
        except Exception as e:
            print(f"Erreur connexion modem: {e}")
            return False
    
    def send_command(self, command):
        if self.ser:
            self.ser.write((command + '\r\n').encode())
            time.sleep(1)
            response = self.ser.read_all().decode()
            return response
    
    def read_sms(self):
        try:
            # Lire tous les SMS
            response = self.send_command('AT+CMGL="ALL"')
            return self.parse_sms(response)
        except Exception as e:
            print(f"Erreur lecture SMS: {e}")
            return []
    
    def parse_sms(self, response):
        sms_list = []
        lines = response.split('\n')
        
        for i, line in enumerate(lines):
            if '+CMGL:' in line:
                # Extraire les informations du SMS
                parts = line.split(',')
                if len(parts) >= 3:
                    sender = parts[2].strip('"')
                    if i + 1 < len(lines):
                        message = lines[i + 1].strip()
                        sms_list.append({
                            'sender': sender,
                            'message': message,
                            'timestamp': datetime.now()
                        })
        
        return sms_list
    
    def process_payment_sms(self, sms):
        """Traiter les SMS de confirmation de paiement"""
        message = sms['message']
        sender = sms['sender']
        
        # Patterns pour différents opérateurs malgaches
        patterns = {
            'AIRTEL': r'Vous avez reçu (\d+(?:\.\d+)?) Ar de (\d+).*Ref[érence]*:?\s*([A-Z0-9]+)',
            'TELMA': r'Transfert reçu.*Montant[:\s]*(\d+(?:\.\d+)?).*De[:\s]*(\d+).*Référence[:\s]*([A-Z0-9]+)',
            'ORANGE': r'Vous avez reçu (\d+(?:\.\d+)?) Ar.*de (\d+).*Transaction[:\s]*([A-Z0-9]+)'
        }
        
        for operator, pattern in patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                phone = match.group(2)
                reference = match.group(3)
                
                return {
                    'amount': amount,
                    'phone': phone,
                    'reference': reference,
                    'operator': operator,
                    'message': message
                }
        
        return None
    
    def create_wifi_credentials(self, payment):
        """Créer les identifiants WiFi après paiement confirmé"""
        try:
            # Calculer la date d'expiration
            duration_days = payment.plan.get_duration_in_days()
            expires_at = timezone.now() + timedelta(days=duration_days)
            
            # Créer les identifiants WiFi
            credentials = WiFiCredentials.objects.create(
                payment=payment,
                expires_at=expires_at
            )
            
            # Marquer le paiement comme réussi
            payment.status = 'SUCCESS'
            payment.save()
            
            print(f"Identifiants créés: {credentials.username}/{credentials.password}")
            return credentials
            
        except Exception as e:
            print(f"Erreur création identifiants: {e}")
            return None
    
    def run_monitoring(self):
        """Boucle principale de surveillance des SMS"""
        print("Démarrage surveillance SMS...")
        
        while True:
            try:
                sms_list = self.read_sms()
                
                for sms in sms_list:
                    payment_data = self.process_payment_sms(sms)
                    
                    if payment_data:
                        print(f"SMS de paiement détecté: {payment_data}")
                        
                        # Chercher une transaction en attente
                        try:
                            sms_transaction = SMSTransaction.objects.get(
                                phone_number=payment_data['phone'],
                                amount=payment_data['amount'],
                                status='PENDING'
                            )
                            
                            if not sms_transaction.is_expired():
                                # Créer le paiement
                                payment = Payment.objects.create(
                                    user_id=1,  # Utilisateur système ou créer dynamiquement
                                    plan=sms_transaction.plan,
                                    amount=payment_data['amount'],
                                    payment_method='MOBILE_MONEY',
                                    phone_number=payment_data['phone'],
                                    status='SUCCESS'
                                )
                                
                                # Lier la transaction SMS au paiement
                                sms_transaction.payment = payment
                                sms_transaction.reference = payment_data['reference']
                                sms_transaction.operator_message = payment_data['message']
                                sms_transaction.status = 'CONFIRMED'
                                sms_transaction.save()
                                
                                # Créer les identifiants WiFi
                                self.create_wifi_credentials(payment)
                                
                                print(f"Paiement confirmé pour {payment_data['phone']}")
                            
                        except SMSTransaction.DoesNotExist:
                            print(f"Aucune transaction en attente pour {payment_data['phone']}")
                
                time.sleep(5)  # Vérifier toutes les 5 secondes
                
            except Exception as e:
                print(f"Erreur surveillance: {e}")
                time.sleep(10)

if __name__ == "__main__":
    handler = SMSHandler()
    if handler.connect():
        handler.run_monitoring()


# Améliorer la classe SMSHandler existante

def parse_operator_sms(self, message):
    """Parser les SMS de confirmation selon votre opérateur"""
    # Exemple pour Orange Money Madagascar
    patterns = {
        'amount': r'(\d+(?:\.\d{2})?)\s*Ar',
        'reference': r'Ref[:\s]*(\w+)',
        'phone': r'(?:de|from)[:\s]*(\+?\d{10,15})',
        'transaction_id': r'ID[:\s]*(\w+)'
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1)
    
    return extracted

def process_incoming_sms(self, message):
    """Traiter les SMS entrants et notifier Django"""
    try:
        parsed_data = self.parse_operator_sms(message)
        
        if all(key in parsed_data for key in ['amount', 'reference', 'phone']):
            # Envoyer au webhook Django
            response = requests.post(
                'http://localhost:8000/api/process-sms-webhook/',
                json=parsed_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"Transaction confirmée: {parsed_data['reference']}")
            else:
                print(f"Erreur webhook: {response.text}")
                
    except Exception as e:
        print(f"Erreur traitement SMS: {e}")

def monitor_sms(self):
    """Boucle de surveillance des SMS"""
    while True:
        try:
            messages = self.read_sms()
            for msg in messages:
                self.process_incoming_sms(msg['content'])
                # Supprimer le SMS traité
                self.delete_sms(msg['index'])
            time.sleep(5)  # Vérifier toutes les 5 secondes
        except Exception as e:
            print(f"Erreur monitoring: {e}")
            time.sleep(10)