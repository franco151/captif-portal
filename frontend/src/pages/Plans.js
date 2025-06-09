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
} from '@mui/material';
import SpeedIcon from '@mui/icons-material/Speed';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import planService from '../services/plan.service';

function PlanCard({ plan }) {
  const navigate = useNavigate();

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        ...(plan.popular && {
          border: '2px solid',
          borderColor: 'primary.main',
        }),
      }}
    >
      {plan.popular && (
        <Chip
          label="Le plus populaire"
          color="primary"
          sx={{
            position: 'absolute',
            top: -12,
            right: 16,
          }}
        />
      )}
      <CardContent sx={{ flexGrow: 1, pt: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {plan.name}
        </Typography>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h3" component="div" color="primary">
            {plan.price}€
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            par mois
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SpeedIcon sx={{ mr: 1 }} />
          <Typography variant="body1">{plan.speed} Mbps</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <AccessTimeIcon sx={{ mr: 1 }} />
          <Typography variant="body1">{plan.duration} jours</Typography>
        </Box>
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Inclus :
          </Typography>
          {plan.features.map((feature, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                mb: 1,
              }}
            >
              <CheckCircleIcon
                sx={{ color: 'success.main', mr: 1, fontSize: 20 }}
              />
              <Typography variant="body1">{feature}</Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
      <CardActions>
        <Button
          fullWidth
          variant={plan.popular ? 'contained' : 'outlined'}
          size="large"
          onClick={() => navigate(`/payment/${plan.id}`)}
        >
          Choisir ce plan
        </Button>
      </CardActions>
    </Card>
  );
}

function Plans() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await planService.getAllPlans();
        setPlans(data);
      } catch (err) {
        setError(err.message || 'Erreur lors du chargement des plans');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Box sx={{ textAlign: 'center', mb: 8 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Choisissez votre forfait
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Des solutions adaptées à tous vos besoins
        </Typography>
      </Box>

      <Grid container spacing={4}>
        {plans.map((plan) => (
          <Grid item key={plan.id} xs={12} md={4}>
            <PlanCard plan={plan} />
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ mt: 8, p: 4, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Besoin d'un forfait personnalisé ?
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Contactez-nous pour discuter de vos besoins spécifiques
        </Typography>
        <Button variant="outlined" size="large">
          Nous contacter
        </Button>
      </Paper>
    </Container>
  );
}

export default Plans; 