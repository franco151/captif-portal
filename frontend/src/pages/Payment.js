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
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  CircularProgress,
  Divider,
} from '@mui/material';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import SecurityIcon from '@mui/icons-material/Security';
import PhoneIcon from '@mui/icons-material/Phone';
import planService from '../services/plan.service';
import paymentService from '../services/payment.service';

// Données de démonstration (à remplacer par un appel API)
const getPlanDetails = (planId) => {
  const plans = {
    1: { name: 'Basique', price: 9.99, duration: 30 },
    2: { name: 'Standard', price: 19.99, duration: 30 },
    3: { name: 'Premium', price: 29.99, duration: 30 },
  };
  return plans[planId] || null;
};

const steps = ['Vérification', 'Paiement', 'Confirmation'];

function Payment() {
  const navigate = useNavigate();
  const { planId } = useParams();
  const [activeStep, setActiveStep] = useState(0);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    cardNumber: '',
    cardHolder: '',
    expiryDate: '',
    cvv: '',
    phoneNumber: '',
  });

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

  const handleChange = (e) => {
    const { name, value } = e.target;
    let formattedValue = value;

    // Formatage des champs
    switch (name) {
      case 'cardNumber':
        formattedValue = value.replace(/\s/g, '').replace(/(\d{4})/g, '$1 ').trim();
        break;
      case 'expiryDate':
        formattedValue = value
          .replace(/\D/g, '')
          .replace(/(\d{2})(\d{0,2})/, '$1/$2')
          .substring(0, 5);
        break;
      case 'cvv':
        formattedValue = value.replace(/\D/g, '').substring(0, 3);
        break;
      case 'phoneNumber':
        formattedValue = value.replace(/\D/g, '').replace(/(\d{2})(?=\d)/g, '$1 ').trim();
        break;
      default:
        break;
    }

    setFormData({
      ...formData,
      [name]: formattedValue,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validation basique
    if (!formData.cardNumber || !formData.cardHolder || !formData.expiryDate || !formData.cvv || !formData.phoneNumber) {
      setError('Veuillez remplir tous les champs');
      setLoading(false);
      return;
    }

    try {
      // Préparation des données de paiement
      const paymentData = {
        card_number: formData.cardNumber.replace(/\s/g, ''),
        card_holder: formData.cardHolder,
        expiry_date: formData.expiryDate,
        cvv: formData.cvv,
        phone_number: formData.phoneNumber.replace(/\s/g, ''),
      };

      // Création du paiement
      const payment = await paymentService.createPayment(planId, paymentData);
      
      // Vérification du statut du paiement
      const status = await paymentService.getPaymentStatus(payment.id);
      
      if (status.status === 'success') {
        setActiveStep(2);
        setTimeout(() => {
          navigate('/success');
        }, 2000);
      } else {
        setError('Le paiement a échoué. Veuillez réessayer.');
      }
    } catch (err) {
      setError(err.message || 'Erreur lors du paiement. Veuillez réessayer.');
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
            Paiement sécurisé
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Plan {plan.name} - {plan.price}€ pour {plan.duration} jours
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SecurityIcon sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="body1">
                Vos informations de paiement sont sécurisées
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Nous utilisons un cryptage SSL pour protéger vos données
            </Typography>
          </CardContent>
        </Card>

        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Informations de contact</Typography>
              </Box>
              <TextField
                required
                fullWidth
                label="Numéro de téléphone"
                name="phoneNumber"
                value={formData.phoneNumber}
                onChange={handleChange}
                placeholder="06 12 34 56 78"
                inputProps={{ maxLength: 14 }}
                disabled={loading}
                helperText="Ce numéro sera utilisé pour vous envoyer vos identifiants de connexion"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CreditCardIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Informations de paiement</Typography>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Numéro de carte"
                name="cardNumber"
                value={formData.cardNumber}
                onChange={handleChange}
                placeholder="1234 5678 9012 3456"
                inputProps={{ maxLength: 19 }}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Nom sur la carte"
                name="cardHolder"
                value={formData.cardHolder}
                onChange={handleChange}
                placeholder="JEAN DUPONT"
                disabled={loading}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                required
                fullWidth
                label="Date d'expiration"
                name="expiryDate"
                value={formData.expiryDate}
                onChange={handleChange}
                placeholder="MM/AA"
                inputProps={{ maxLength: 5 }}
                disabled={loading}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                required
                fullWidth
                label="CVV"
                name="cvv"
                value={formData.cvv}
                onChange={handleChange}
                placeholder="123"
                inputProps={{ maxLength: 3 }}
                disabled={loading}
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/plans')}
              disabled={loading}
            >
              Retour aux plans
            </Button>
            <Button
              type="submit"
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <CreditCardIcon />}
              disabled={loading}
            >
              {loading ? 'Traitement...' : `Payer ${plan.price}€`}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}

export default Payment; 