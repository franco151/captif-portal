import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Container,
} from '@mui/material';
import WifiIcon from '@mui/icons-material/Wifi';
import SecurityIcon from '@mui/icons-material/Security';
import SpeedIcon from '@mui/icons-material/Speed';

const features = [
  {
    icon: <WifiIcon sx={{ fontSize: 40 }} />,
    title: 'Connexion Rapide',
    description: 'Accédez à Internet en quelques clics',
  },
  {
    icon: <SecurityIcon sx={{ fontSize: 40 }} />,
    title: 'Sécurisé',
    description: 'Protection de vos données garantie',
  },
  {
    icon: <SpeedIcon sx={{ fontSize: 40 }} />,
    title: 'Haute Vitesse',
    description: 'Navigation fluide et rapide',
  },
];

function Home() {
  const navigate = useNavigate();

  return (
    <Box sx={{ py: 8 }}>
      {/* Hero Section */}
      <Box
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          py: 8,
          mb: 6,
          borderRadius: 2,
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h2" component="h1" gutterBottom>
            Bienvenue sur BestConnect
          </Typography>
          <Typography variant="h5" paragraph>
            Votre portail d'accès Internet sécurisé
          </Typography>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            onClick={() => navigate('/plans')}
            sx={{ mt: 2 }}
          >
            Voir les forfaits
          </Button>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Paper
                elevation={3}
                sx={{
                  p: 3,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                }}
              >
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h5" component="h2" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography color="text.secondary">
                  {feature.description}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        {/* Call to Action */}
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>
            Prêt à vous connecter ?
          </Typography>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => navigate('/login')}
            sx={{ mr: 2 }}
          >
            Se connecter
          </Button>
          <Button
            variant="outlined"
            color="primary"
            size="large"
            onClick={() => navigate('/register')}
          >
            Créer un compte
          </Button>
        </Box>
      </Container>
    </Box>
  );
}

export default Home; 