import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PhoneIcon from '@mui/icons-material/Phone';
import WifiIcon from '@mui/icons-material/Wifi';

function Success() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [credentials, setCredentials] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // Simuler le chargement des identifiants
    const timer = setTimeout(() => {
      setLoading(false);
      // Dans un cas réel, ces données viendraient du backend
      setCredentials({
        username: 'user_' + Math.random().toString(36).substr(2, 8),
        password: Math.random().toString(36).substr(2, 12),
      });
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Préparation de vos identifiants...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
        <Box sx={{ mb: 4 }}>
          <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main' }} />
        </Box>

        <Typography variant="h4" component="h1" gutterBottom>
          Paiement réussi !
        </Typography>

        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
          Votre abonnement a été activé avec succès
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {credentials && (
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'center' }}>
              <WifiIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Vos identifiants de connexion</Typography>
            </Box>

            <Paper variant="outlined" sx={{ p: 2, mb: 2, maxWidth: 400, mx: 'auto' }}>
              <Typography variant="body1" gutterBottom>
                <strong>Nom d'utilisateur :</strong> {credentials.username}
              </Typography>
              <Typography variant="body1">
                <strong>Mot de passe :</strong> {credentials.password}
              </Typography>
            </Paper>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Ces identifiants vous ont été envoyés par SMS
            </Typography>
          </Box>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 4 }}>
          <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="body1">
            Vérifiez votre téléphone pour recevoir vos identifiants
          </Typography>
        </Box>

        <Box sx={{ mt: 4 }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/')}
          >
            Retour à l'accueil
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

export default Success; 