import React, { useState, useEffect } from 'react';
import { paymentService } from '../services/payment.service';

const PaymentFlow = ({ selectedPlan, onSuccess }) => {
    const [step, setStep] = useState('phone'); // phone, payment, waiting, success
    const [phoneNumber, setPhoneNumber] = useState('');
    const [transaction, setTransaction] = useState(null);
    const [credentials, setCredentials] = useState(null);
    const [timeLeft, setTimeLeft] = useState(600); // 10 minutes

    // Polling pour vérifier le statut du paiement
    useEffect(() => {
        if (transaction && step === 'waiting') {
            const interval = setInterval(async () => {
                try {
                    const status = await paymentService.checkPaymentStatus(transaction.transaction_id);
                    
                    if (status.status === 'CONFIRMED') {
                        setCredentials(status.wifi_credentials);
                        setStep('success');
                        clearInterval(interval);
                    } else if (status.status === 'EXPIRED' || status.status === 'FAILED') {
                        setStep('phone');
                        clearInterval(interval);
                    }
                } catch (error) {
                    console.error('Erreur vérification statut:', error);
                }
            }, 3000); // Vérifier toutes les 3 secondes

            return () => clearInterval(interval);
        }
    }, [transaction, step]);

    // Compte à rebours
    useEffect(() => {
        if (step === 'waiting' && timeLeft > 0) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [step, timeLeft]);

    const handleInitiatePayment = async () => {
        try {
            const response = await paymentService.initiateSMSPayment({
                plan_id: selectedPlan.id,
                phone_number: phoneNumber
            });
            
            setTransaction(response);
            setStep('payment');
        } catch (error) {
            alert('Erreur lors de l\'initiation du paiement');
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="payment-flow">
            {step === 'phone' && (
                <div className="phone-step">
                    <h3>Numéro de téléphone</h3>
                    <p>Forfait sélectionné: {selectedPlan.name} - {selectedPlan.price} Ar</p>
                    <input
                        type="tel"
                        placeholder="Votre numéro de téléphone"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                    />
                    <button onClick={handleInitiatePayment}>Continuer</button>
                </div>
            )}

            {step === 'payment' && (
                <div className="payment-step">
                    <h3>Instructions de paiement</h3>
                    <div className="ussd-code">
                        <p>Composez ce code sur votre téléphone:</p>
                        <code>{transaction.ussd_code}</code>
                        <button onClick={() => navigator.clipboard.writeText(transaction.ussd_code)}>
                            Copier le code
                        </button>
                    </div>
                    <p>Référence: <strong>{transaction.reference}</strong></p>
                    <button onClick={() => setStep('waiting')}>J'ai effectué le paiement</button>
                </div>
            )}

            {step === 'waiting' && (
                <div className="waiting-step">
                    <h3>Vérification du paiement...</h3>
                    <div className="spinner">⏳</div>
                    <p>Temps restant: {formatTime(timeLeft)}</p>
                    <p>Référence: {transaction.reference}</p>
                    <small>Nous vérifions votre paiement automatiquement</small>
                </div>
            )}

            {step === 'success' && credentials && (
                <div className="success-step">
                    <h3>🎉 Paiement confirmé !</h3>
                    <div className="wifi-credentials">
                        <h4>Vos identifiants WiFi:</h4>
                        <p><strong>Nom d'utilisateur:</strong> {credentials.username}</p>
                        <p><strong>Mot de passe:</strong> {credentials.password}</p>
                        
                        <div className="qr-code">
                            <img 
                                src={`data:image/png;base64,${credentials.qr_code}`} 
                                alt="QR Code WiFi" 
                            />
                            <p>Scannez ce QR code pour vous connecter automatiquement</p>
                        </div>
                        
                        <div className="actions">
                            <button onClick={() => window.print()}>Imprimer</button>
                            <button onClick={() => {
                                // Télécharger les credentials
                                const element = document.createElement('a');
                                const file = new Blob([JSON.stringify(credentials, null, 2)], 
                                    {type: 'application/json'});
                                element.href = URL.createObjectURL(file);
                                element.download = `wifi-credentials-${credentials.username}.json`;
                                document.body.appendChild(element);
                                element.click();
                                document.body.removeChild(element);
                            }}>Télécharger</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaymentFlow;