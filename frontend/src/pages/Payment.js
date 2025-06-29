import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Container,
  Grid,
  Alert,
  AlertTitle,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Avatar,
  InputAdornment,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SecurityIcon from '@mui/icons-material/Security';
import PhoneIcon from '@mui/icons-material/Phone';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import QrCodeIcon from '@mui/icons-material/QrCode';
import VerifiedIcon from '@mui/icons-material/Verified';
import SmsIcon from '@mui/icons-material/Sms';
import planService from '../services/plan.service';
import paymentService from '../services/payment.service';
import DownloadIcon from '@mui/icons-material/Download';

const steps = ['Vérification', 'Paiement', 'Confirmation'];

function Payment() {
  const navigate = useNavigate();
  const { planId } = useParams();
  const [activeStep, setActiveStep] = useState(0);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [transactionReference, setTransactionReference] = useState('');
  const [wifiCredentials, setWifiCredentials] = useState(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const data = await planService.getPlanById(planId);
        setPlan(data);
      } catch (err) {
        setError(err.message || 'Erreur lors du chargement du plan');
        setTimeout(() => navigate('/plans'), 3000);
      }
    };

    fetchPlan();
  }, [planId, navigate]);

  const handleNext = () => {
    if (activeStep === 0) {
      setActiveStep(1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    } else {
      navigate('/plans');
    }
  };

  const verifyTransaction = async () => {
    if (!transactionReference.trim()) {
      setError('Veuillez entrer la référence de transaction');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await paymentService.verifyTransactionReference(
        transactionReference,
        planId
      );

      if (response.success) {
        setWifiCredentials({
          username: response.username,
          password: response.password,
          expiration: response.expiration_date,
          qr_code: response.qr_code
        });
        setActiveStep(2);
      } else {
        setError(response.message || 'Référence de transaction invalide');
      }
    } catch (err) {
      setError(err.message || 'Erreur lors de la vérification');
    } finally {
      setLoading(false);
    }
  };

  if (!plan) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Détails du forfait
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h4" color="primary" gutterBottom>
                  {plan.name}
                </Typography>
                <Typography variant="h5" gutterBottom>
                  {plan.price} Ar
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Durée: {plan.duration} jours
                </Typography>
                {plan.description && (
                  <Typography variant="body2" sx={{ mt: 2 }}>
                    {plan.description}
                  </Typography>
                )}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="body1">
                  Paiement sécurisé via Mobile Money
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Après vérification de votre forfait, vous procéderez au paiement via votre opérateur mobile.
              </Typography>
            </CardContent>
          </Card>
        );

      case 1:
        return (
          <Box>
            {/* En-tête avec informations importantes */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <AlertTitle>Instructions de paiement</AlertTitle>
              <Typography variant="body2">
                Montant à payer : <strong>{plan.price} Ar</strong> pour le forfait {plan.name}
                <br />
                Numéro de destination : <strong>034 72 49 715</strong>
              </Typography>
            </Alert>

            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Choisissez votre opérateur</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Sélectionnez votre opérateur mobile et suivez les étapes ci-dessous pour effectuer le transfert.
                </Typography>

                {/* Instructions Telma améliorées */}
                <Accordion>
                  <AccordionSummary 
                    expandIcon={<ExpandMoreIcon />}
                    sx={{ bgcolor: 'primary.50' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>T</Typography>
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>TELMA - MVola</Typography>
                        <Typography variant="caption" color="text.secondary">Service de transfert d'argent</Typography>
                      </Box>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ p: 2 }}>
                      <Typography variant="h6" color="primary" gutterBottom>
                        📱 Étapes à suivre :
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          1️⃣ Composez le code USSD :
                        </Typography>
                        
                        <Paper sx={{ 
                          p: { xs: 1, sm: 2 }, 
                          bgcolor: 'primary.50', 
                          border: '2px solid', 
                          borderColor: 'primary.main',
                          overflow: 'auto'
                        }}>
                          <Typography 
                            variant="h4" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              textAlign: 'center', 
                              color: 'primary.main',
                              fontSize: { xs: '0.9rem', sm: '1.1rem', md: '1.25rem' },
                              wordBreak: 'break-all',
                              overflowWrap: 'break-word'
                            }}
                          >
                            #111*1*2*0347249715*{plan.price}*[CODE]#
                          </Typography>
                        </Paper>
                      </Box>

                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          2️⃣ Confirmez la transaction :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          • Vérifiez le montant : {plan.price} Ar
                          <br />• Vérifiez le numéro : 034 72 49 715
                          <br />• Entrez votre code PIN MVola
                        </Typography>
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          3️⃣ Récupérez votre référence :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Vous recevrez un SMS avec une référence de transaction (ex: TXREF12345)
                        </Typography>
                      </Box>

                      <Alert severity="success" variant="outlined">
                        <Typography variant="caption">
                          💡 Astuce : Gardez votre téléphone à portée de main pour recevoir le SMS de confirmation
                        </Typography>
                      </Alert>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                {/* Instructions Airtel améliorées */}
                <Accordion>
                  <AccordionSummary 
                    expandIcon={<ExpandMoreIcon />}
                    sx={{ bgcolor: 'error.50' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'error.main', width: 32, height: 32 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold' }}>A</Typography>
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>AIRTEL - Airtel Money</Typography>
                        <Typography variant="caption" color="text.secondary">Service de transfert d'argent</Typography>
                      </Box>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ p: 2 }}>
                      <Typography variant="h6" color="error" gutterBottom>
                        📱 Étapes à suivre :
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          1️⃣ Composez le code USSD :
                        </Typography>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 2 }, 
                          bgcolor: 'error.50', 
                          border: '2px solid', 
                          borderColor: 'error.main',
                          overflow: 'auto'
                        }}>
                          <Typography 
                            variant="h4" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              textAlign: 'center', 
                              color: 'error.main',
                              fontSize: { xs: '0.9rem', sm: '1.1rem', md: '1.25rem' },
                              wordBreak: 'break-all',
                              overflowWrap: 'break-word'
                            }}
                          >
                            *555*1*0347249715*{plan.price}#
                          </Typography>
                        </Paper>
                      </Box>

                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          2️⃣ Suivez les instructions :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          • Sélectionnez "Transfert d'argent"
                          <br />• Confirmez le montant : {plan.price} Ar
                          <br />• Confirmez le numéro : 034 72 49 715
                          <br />• Entrez votre code PIN Airtel Money
                        </Typography>
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          3️⃣ Récupérez votre référence :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Vous recevrez un SMS avec une référence de transaction
                        </Typography>
                      </Box>

                      <Alert severity="warning" variant="outlined">
                        <Typography variant="caption">
                          ⚠️ Important : Assurez-vous d'avoir suffisamment de solde sur votre compte Airtel Money
                        </Typography>
                      </Alert>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                {/* Instructions Orange améliorées */}
                <Accordion>
                  <AccordionSummary 
                    expandIcon={<ExpandMoreIcon />}
                    sx={{ bgcolor: 'warning.50' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'warning.main', width: 32, height: 32 }}>
                        <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'white' }}>O</Typography>
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>ORANGE - Orange Money</Typography>
                        <Typography variant="caption" color="text.secondary">Service de transfert d'argent</Typography>
                      </Box>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ p: 2 }}>
                      <Typography variant="h6" color="warning.main" gutterBottom>
                        📱 Étapes à suivre :
                      </Typography>
                      
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          1️⃣ Composez le code USSD :
                        </Typography>
                        <Paper sx={{ 
                          p: { xs: 1, sm: 2 }, 
                          bgcolor: 'warning.50', 
                          border: '2px solid', 
                          borderColor: 'warning.main',
                          overflow: 'auto'
                        }}>
                          <Typography 
                            variant="h4" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              textAlign: 'center', 
                              color: 'warning.main',
                              fontSize: { xs: '0.9rem', sm: '1.1rem', md: '1.25rem' },
                              wordBreak: 'break-all',
                              overflowWrap: 'break-word'
                            }}
                          >
                            #144*1*1*0347249715*{plan.price}#
                          </Typography>
                        </Paper>
                      </Box>

                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          2️⃣ Confirmez la transaction :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          • Vérifiez les informations affichées
                          <br />• Montant : {plan.price} Ar
                          <br />• Destinataire : 034 72 49 715
                          <br />• Entrez votre code PIN Orange Money
                        </Typography>
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                          3️⃣ Récupérez votre référence :
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Un SMS de confirmation sera envoyé avec votre référence de transaction
                        </Typography>
                      </Box>

                      <Alert severity="info" variant="outlined">
                        <Typography variant="caption">
                          ℹ️ Note : Le transfert peut prendre quelques minutes pour être traité
                        </Typography>
                      </Alert>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>

            {/* Section de vérification améliorée */}
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <VerifiedIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6">Vérification du paiement</Typography>
                </Box>
                
                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    <strong>Après avoir effectué le transfert :</strong>
                    <br />1. Vous recevrez un SMS de confirmation de votre opérateur
                    <br />2. Ce SMS contient une référence de transaction unique
                    <br />3. Entrez cette référence ci-dessous pour activer votre forfait
                    <br /><strong>4. Après la vérification, vous obtiendrez un ticket (reçu) que vous pourrez télécharger ou capturer</strong>
                  </Typography>
                </Alert>
                
                <TextField
                  fullWidth
                  label="Référence de transaction"
                  value={transactionReference}
                  onChange={(e) => setTransactionReference(e.target.value.toUpperCase())}
                  placeholder="Ex: TXREF12345, MP240123456, etc."
                  sx={{ mb: 3 }}
                  disabled={loading}
                  helperText="Saisissez exactement la référence trouvée dans votre SMS de confirmation"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SmsIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
                
                <Button
                  fullWidth
                  variant="contained"
                  onClick={verifyTransaction}
                  disabled={loading || !transactionReference.trim()}
                  startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
                  size="large"
                  sx={{ py: 1.5 }}
                >
                  {loading ? 'Vérification en cours...' : 'Vérifier et Activer le Forfait'}
                </Button>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
                  Votre paiement est sécurisé et vos données sont protégées
                </Typography>
              </CardContent>
            </Card>
          </Box>
        );

      case 2:
        return (
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom color="success.main">
                Paiement confirmé !
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                Votre forfait {plan.name} a été activé avec succès.
              </Typography>
              
              {/* Nouvelle section pour le ticket */}
              <Alert severity="success" sx={{ mb: 3, textAlign: 'left' }}>
                <Typography variant="body2">
                  <strong>🎫 Votre ticket (reçu) est maintenant disponible :</strong>
                  <br />• Vous pouvez le télécharger en cliquant sur le bouton "Télécharger le ticket"
                  <br />• Ou faire une capture d'écran de cette page pour conserver une copie
                  <br />• Ce ticket contient tous les détails de votre achat et vos identifiants WiFi
                </Typography>
              </Alert>
              
              // ... existing code for wifiCredentials ...
              
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3, flexWrap: 'wrap' }}>
                {/* Nouveau bouton de téléchargement */}
                <Button
                  variant="contained"
                  color="success"
                  onClick={() => {
                    // Fonction pour télécharger le ticket
                    const ticketData = {
                      plan: plan.name,
                      price: plan.price,
                      duration: plan.duration,
                      date: new Date().toLocaleDateString('fr-FR'),
                      credentials: wifiCredentials
                    };
                    // Ici vous pouvez implémenter la logique de téléchargement
                    console.log('Téléchargement du ticket:', ticketData);
                  }}
                  startIcon={<DownloadIcon />}
                >
                  Télécharger le Ticket
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={() => navigate('/portal')}
                  startIcon={<QrCodeIcon />}
                >
                  Aller au Portail
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate('/plans')}
                >
                  Nouveaux Forfaits
                </Button>
              </Box>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {steps[activeStep]}
          </Typography>
          {activeStep < 2 && (
            <Typography variant="subtitle1" color="text.secondary">
              Plan {plan.name} - {plan.price} Ar pour {plan.duration} jours
            </Typography>
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {renderStepContent()}

        {activeStep < 2 && (
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              onClick={handleBack}
              disabled={loading}
            >
              {activeStep === 0 ? 'Retour aux plans' : 'Précédent'}
            </Button>
            {activeStep === 0 && (
              <Button
                variant="contained"
                onClick={handleNext}
                size="large"
              >
                Continuer
              </Button>
            )}
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default Payment;