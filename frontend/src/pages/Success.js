import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  CircularProgress,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Wifi as WifiIcon,
  Speed as SpeedIcon,
  AccessTime as TimeIcon,
  ExitToApp as LogoutIcon,
  CalendarToday as CalendarIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function Success() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [remainingTime, setRemainingTime] = useState(null);
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    if (hasChecked) return; // Éviter les vérifications multiples
    
    const checkSession = async () => {
      try {
        setHasChecked(true);
        const sessionId = localStorage.getItem('sessionId');
        const token = localStorage.getItem('accessToken');
        
        console.log('Debug - Checking session...', { sessionId, token });
        
        if (!sessionId || !token) {
          console.log('Debug - No session found, redirecting...');
          navigate('/portal', { replace: true });
          return;
        }

        const user = JSON.parse(localStorage.getItem('user') || '{}');
        setUserInfo(user);
        
        // Vérifier le statut de la session
        const response = await axios.get(`${API_URL}/captive-portal/check-status/`, {
          params: { session_id: sessionId },
          headers: { Authorization: `Bearer ${token}` }
        });
        
        console.log('Debug - API response:', response.data);
        
        if (response.data.is_active) {
          console.log('Session data:', response.data);
          setSessionInfo(response.data);
          setRemainingTime(response.data.remaining_time);
          setSubscriptionInfo(response.data.subscription);
        } else {
          console.log('Debug - Session not active, redirecting to portal');
          navigate('/portal');
        }
      } catch (error) {
        console.error('Erreur lors de la vérification:', error);
        console.log('Debug - Error occurred, redirecting to portal');
        navigate('/portal');
      } finally {
        setLoading(false);
      }
    };

    checkSession();
  }, [navigate, hasChecked]);

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const sessionId = localStorage.getItem('sessionId');
      
      if (token && sessionId) {
        await axios.post(`${API_URL}/captive-portal/logout/`, 
          { session_id: sessionId },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      // Nettoyer le stockage local
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('sessionId');
      localStorage.removeItem('user');
      navigate('/portal');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} color="primary" />
        <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>
          Vérification de votre connexion...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      {/* Alerte d'expiration si nécessaire */}
      {subscriptionInfo?.is_expired && (
        <Alert 
          severity="error" 
          icon={<WarningIcon />}
          sx={{ mb: 3, fontWeight: 'bold' }}
        >
          <Typography variant="h6" component="div">
            Ticket Expiré
          </Typography>
          <Typography variant="body2">
            Votre abonnement a expiré le {new Date(subscriptionInfo.end_date).toLocaleDateString('fr-FR')}. 
            Les tickets expirés ne sont plus autorisés à se connecter. Veuillez acheter un nouveau ticket.
          </Typography>
        </Alert>
      )}

      <Paper 
        elevation={8} 
        sx={{ 
          p: 6, 
          textAlign: 'center',
          background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
          color: 'white',
          borderRadius: 4,
          mb: 4
        }}
      >
        {/* Icône de succès */}
        <CheckCircleIcon 
          sx={{ 
            fontSize: 80, 
            mb: 2,
            filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))'
          }} 
        />
        
        {/* Titre de bienvenue */}
        <Typography 
          variant="h2" 
          component="h1" 
          sx={{ 
            fontSize: { xs: '2rem', md: '3rem' },
            fontWeight: 'bold',
            mb: 2,
            textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
          }}
        >
          Bienvenue !
        </Typography>
        
        <Typography 
          variant="h5" 
          sx={{ 
            mb: 2,
            fontWeight: 300,
            opacity: 0.9
          }}
        >
          Tonga soa {userInfo?.username || 'Mpampiasa'}
        </Typography>
        
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 300,
            opacity: 0.8
          }}
        >
          Votre connexion à internet a été établie avec succès
        </Typography>
      </Paper>

      {/* Informations de session */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center', p: 3 }}>
              <WifiIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Statut
              </Typography>
              <Chip 
                label="Connecté" 
                color="success" 
                variant="filled"
                sx={{ fontWeight: 'bold' }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center', p: 3 }}>
              <TimeIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Temps restant
              </Typography>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {remainingTime ? `${remainingTime} min` : 'Illimité'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center', p: 3 }}>
              <SpeedIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Vitesse
              </Typography>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {sessionInfo?.speed || 'Max'} Mbps
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Informations utilisateur */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Informations de session
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Utilisateur
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {userInfo?.username || 'Non disponible'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Adresse IP
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {sessionInfo?.ip_address || '192.168.1.100'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Identification de l'appareil
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {sessionInfo?.mac_address || 'Non disponible'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Heure de connexion
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {sessionInfo?.start_time ? 
                new Date(sessionInfo.start_time).toLocaleString('fr-FR', {
                  year: 'numeric',
                  month: '2-digit', 
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                }) : 'Maintenant'
              }
            </Typography>
          </Grid>
          {/* Nouvelles informations d'abonnement */}
          {subscriptionInfo && (
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Informations d'abonnement
              </Typography>
              <Typography variant="body1">
                <strong>Plan:</strong> {subscriptionInfo.plan_name}
              </Typography>
              <Typography variant="body1" color={subscriptionInfo.is_expired ? 'error' : 'inherit'}>
                <strong>Date d'expiration:</strong> {new Date(subscriptionInfo.end_date).toLocaleString('fr-FR')}
                {subscriptionInfo.is_expired && ' (Expiré)'}
              </Typography>
              {subscriptionInfo.is_expired && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    ⚠️ Votre ticket a expiré. L'accès ne sera pas autorisé.
                  </Typography>
                </Alert>
              )}
            </Paper>
          )}
        </Grid>
      </Paper>

      {/* Bouton de déconnexion */}
      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          color="error"
          size="large"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{ 
            px: 4, 
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 'bold'
          }}
        >
          Se déconnecter
        </Button>
      </Box>
    </Container>
  );
}

export default Success;