import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Container,
  Grid,
  Typography,
  Chip,
  Paper,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge
} from '@mui/material';
import {
  Speed as SpeedIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  Wifi as WifiIcon,
  Security as SecurityIcon,
  Support as SupportIcon,
  Payment as PaymentIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function PlanCard({ plan, onSelectPlan }) {
  const isPopular = plan.name.toLowerCase().includes('populaire') || plan.price > 50000;
  
  const formatPrice = (price) => {
    return new Intl.NumberFormat('mg-MG', {
      style: 'currency',
      currency: 'MGA',
      minimumFractionDigits: 0
    }).format(price).replace('MGA', 'Ar');
  };

  const getDurationText = (duration, unit) => {
    const unitMap = {
      'DAYS': duration === 1 ? 'jour' : 'jours',
      'WEEKS': duration === 1 ? 'semaine' : 'semaines', 
      'MONTHS': duration === 1 ? 'mois' : 'mois'
    };
    return `${duration} ${unitMap[unit] || 'jours'}`;
  };

  const getFeatures = (plan) => {
    const features = [
      'Connexion internet illimitée',
      'Support technique 24h/24',
      'Installation gratuite'
    ];
    
    if (plan.price > 30000) {
      features.push('Vitesse prioritaire');
    }
    if (plan.price > 50000) {
      features.push('Support premium');
      features.push('Garantie de débit');
    }
    
    return features;
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        transition: 'all 0.3s ease',
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-8px)',
          boxShadow: '0 12px 24px rgba(0,0,0,0.15)'
        },
        ...(isPopular && {
          border: '3px solid',
          borderColor: 'primary.main',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
        })
      }}
      onClick={() => onSelectPlan(plan)}
    >
      {isPopular && (
        <Badge
          badgeContent={
            <Box sx={{ display: 'flex', alignItems: 'center', px: 1 }}>
              <StarIcon sx={{ fontSize: 16, mr: 0.5 }} />
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                POPULAIRE
              </Typography>
            </Box>
          }
          sx={{
            '& .MuiBadge-badge': {
              backgroundColor: 'primary.main',
              color: 'white',
              top: 16,
              right: 16,
              borderRadius: '12px',
              height: 'auto',
              minWidth: 'auto'
            }
          }}
        />
      )}
      
      <CardContent sx={{ flexGrow: 1, pt: isPopular ? 5 : 3, pb: 2 }}>
        <Typography 
          variant="h4" 
          component="h2" 
          gutterBottom
          sx={{ 
            fontWeight: 'bold',
            color: isPopular ? 'primary.main' : 'text.primary'
          }}
        >
          {plan.name}
        </Typography>
        
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ mb: 3, minHeight: '40px' }}
        >
          {plan.description}
        </Typography>
        
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Typography 
            variant="h2" 
            component="div" 
            color="primary.main"
            sx={{ fontWeight: 'bold', lineHeight: 1 }}
          >
            {formatPrice(plan.price)}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            pour {getDurationText(plan.duration, plan.duration_unit)}
          </Typography>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
            Inclus dans ce forfait :
          </Typography>
          <List dense>
            {getFeatures(plan).map((feature, index) => (
              <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                </ListItemIcon>
                <ListItemText 
                  primary={feature}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </CardContent>
      
      <CardActions sx={{ p: 3, pt: 0 }}>
        <Button
          fullWidth
          variant={isPopular ? 'contained' : 'outlined'}
          size="large"
          sx={{ 
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 'bold',
            ...(isPopular && {
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)'
            })
          }}
        >
          Choisir ce forfait
        </Button>
      </CardActions>
    </Card>
  );
}

function PaymentDialog({ open, onClose, selectedPlan }) {
  const navigate = useNavigate();
  const [paymentMethod, setPaymentMethod] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePayment = async () => {
    setIsProcessing(true);
    try {
      // Simuler le processus de paiement
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Rediriger vers la page de paiement avec l'ID du plan
      navigate(`/payment/${selectedPlan.id}`);
    } catch (error) {
      console.error('Erreur lors du paiement:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!selectedPlan) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
        <Typography variant="h4" component="h2">
          Confirmer votre choix
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
            {selectedPlan.name}
          </Typography>
          <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 1 }}>
            {new Intl.NumberFormat('mg-MG').format(selectedPlan.price)} Ar
          </Typography>
          <Typography variant="body1">
            Durée: {selectedPlan.duration} {selectedPlan.duration_unit === 'DAYS' ? 'jour(s)' : selectedPlan.duration_unit === 'WEEKS' ? 'semaine(s)' : 'mois'}
          </Typography>
        </Paper>
        
        <Typography variant="body1" sx={{ mb: 3, textAlign: 'center' }}>
          Vous êtes sur le point de souscrire à ce forfait. Cliquez sur "Procéder au paiement" pour continuer.
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          <PaymentIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">
            Méthodes de paiement disponibles
          </Typography>
        </Box>
        
        <List>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon sx={{ color: 'success.main' }} />
            </ListItemIcon>
            <ListItemText primary="Mobile Money (Orange Money, Airtel Money)" />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon sx={{ color: 'success.main' }} />
            </ListItemIcon>
            <ListItemText primary="Paiement en espèces (en agence)" />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon sx={{ color: 'success.main' }} />
            </ListItemIcon>
            <ListItemText primary="Virement bancaire" />
          </ListItem>
        </List>
      </DialogContent>
      
      <DialogActions sx={{ p: 3, gap: 2 }}>
        <Button 
          onClick={onClose}
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          disabled={isProcessing}
        >
          Retour
        </Button>
        <Button 
          onClick={handlePayment}
          variant="contained"
          size="large"
          disabled={isProcessing}
          startIcon={isProcessing ? <CircularProgress size={20} /> : <PaymentIcon />}
          sx={{ flex: 1 }}
        >
          {isProcessing ? 'Traitement...' : 'Procéder au paiement'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function Plans() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        // Récupérer les forfaits depuis l'API subscriptions
        const response = await axios.get(`${API_URL}/subscriptions/plans/`);
        setPlans(response.data);
      } catch (err) {
        console.error('Erreur lors du chargement des forfaits:', err);
        setError('Erreur lors du chargement des forfaits. Veuillez réessayer.');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  const handleSelectPlan = (plan) => {
    setSelectedPlan(plan);
    setPaymentDialogOpen(true);
  };

  const handleClosePaymentDialog = () => {
    setPaymentDialogOpen(false);
    setSelectedPlan(null);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Chargement des forfaits...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
        <Box sx={{ textAlign: 'center' }}>
          <Button 
            variant="contained" 
            onClick={() => window.location.reload()}
          >
            Réessayer
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* En-tête moderne */}
      <Paper 
        sx={{ 
          p: 6, 
          mb: 6, 
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 4
        }}
      >
        <WifiIcon sx={{ fontSize: 60, mb: 2 }} />
        <Typography 
          variant="h2" 
          component="h1" 
          gutterBottom
          sx={{ fontWeight: 'bold', textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}
        >
          Nos Forfaits Internet
        </Typography>
        <Typography 
          variant="h5" 
          sx={{ opacity: 0.9, fontWeight: 300 }}
        >
          Choisissez le forfait qui correspond à vos besoins
        </Typography>
      </Paper>

      {/* Grille des forfaits */}
      {plans.length > 0 ? (
        <Grid container spacing={4} sx={{ mb: 6 }}>
          {plans.map((plan) => (
            <Grid item key={plan.id} xs={12} md={6} lg={4}>
              <PlanCard plan={plan} onSelectPlan={handleSelectPlan} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Aucun forfait disponible pour le moment
          </Typography>
        </Paper>
      )}

      {/* Section contact */}
      <Paper sx={{ p: 4, textAlign: 'center', background: '#f8f9fa' }}>
        <SupportIcon sx={{ fontSize: 40, color: 'primary.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
          Besoin d'aide pour choisir ?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Notre équipe est là pour vous conseiller et vous aider à trouver le forfait parfait
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button 
            variant="outlined" 
            size="large"
            href="tel:+261347249715"
            sx={{ minWidth: 200 }}
          >
            Appeler: 034 72 497 15
          </Button>
          <Button 
            variant="outlined" 
            size="large"
            href="https://facebook.com/BestConnect-FARAFANGANA"
            target="_blank"
            sx={{ minWidth: 200 }}
          >
            Facebook
          </Button>
        </Box>
      </Paper>

      {/* Dialog de paiement */}
      <PaymentDialog 
        open={paymentDialogOpen}
        onClose={handleClosePaymentDialog}
        selectedPlan={selectedPlan}
      />
    </Container>
  );
}

export default Plans;