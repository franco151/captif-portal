#!/usr/bin/env python3
import serial
import time
import re
import requests
import json
from datetime import datetime
import logging

# Configuration du modem GSM
SERIAL_PORT = '/dev/ttyUSB0'  # Port série du modem
BAUD_RATE = 9600
API_ENDPOINT = 'http://localhost:8000/api/sms-transaction/'
API_TOKEN = 'votre_token_api'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSReader:
    def __init__(self):
        self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        self.setup_modem()
    
    def setup_modem(self):
        """Configuration initiale du modem"""
        commands = [
            'AT',  # Test de connexion
            'AT+CMGF=1',  # Mode texte pour SMS
            'AT+CNMI=1,2,0,0,0',  # Notification automatique des SMS
            'AT+CPMS="SM"',  # Utiliser la mémoire SIM
        ]
        
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(1)
    
    def send_command(self, command):
        """Envoyer une commande AT au modem"""
        self.ser.write((command + '\r\n').encode())
        response = self.ser.read(100).decode('utf-8', errors='ignore')
        logger.info(f"Command: {command}, Response: {response.strip()}")
        return response
    
    def parse_operator_sms(self, message):
        """Parser le SMS de l'opérateur (à adapter selon votre opérateur)"""
        # Exemple pour Orange Money Madagascar
        patterns = {
            'amount': r'(\d+(?:\.\d{2})?)\s*Ar',
            'reference': r'Ref[:\s]*(\w+)',
            'phone': r'(?:de|from)[:\s]*(\+?\d{10,15})'
        }
        
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                result[key] = match.group(1)
        
        return result
    
    def process_sms(self, sender, message):
        """Traiter un SMS reçu"""
        # Vérifier si c'est un SMS de l'opérateur
        operator_numbers = ['1515', '1234', 'ORANGE']  # À adapter
        
        if sender not in operator_numbers:
            return
        
        # Parser le message
        parsed_data = self.parse_operator_sms(message)
        
        if all(key in parsed_data for key in ['amount', 'reference', 'phone']):
            # Envoyer à l'API Django
            self.send_to_api(parsed_data, message)
    
    def send_to_api(self, data, raw_message):
        """Envoyer les données à l'API Django"""
        payload = {
            'reference': data['reference'],
            'phone_number': data['phone'],
            'amount': float(data['amount']),
            'operator_message': raw_message
        }
        
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(API_ENDPOINT, 
                                   json=payload, 
                                   headers=headers)
            if response.status_code == 201:
                logger.info(f"Transaction envoyée avec succès: {data['reference']}")
            else:
                logger.error(f"Erreur API: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi à l'API: {e}")
    
    def listen_for_sms(self):
        """Écouter en continu les SMS entrants"""
        logger.info("Démarrage de l'écoute SMS...")
        
        while True:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    
                    # Détecter un nouveau SMS
                    if '+