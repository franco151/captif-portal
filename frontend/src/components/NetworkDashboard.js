import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Card, CardContent,
  Table, TableBody, TableCell, TableHead, TableRow,
  Chip, LinearProgress
} from '@mui/material';
import { Line, Doughnut } from 'react-chartjs-2';

const NetworkDashboard = ({ userId }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Mise à jour toutes les 30s
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/user-analytics/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Erreur lors du chargement des analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Tableau de bord réseau
      </Typography>
      
      <Grid container spacing={3}>
        {/* Statistiques générales */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Données téléchargées</Typography>
              <Typography variant="h4" color="primary">
                {analytics?.statistics?.total_downloaded_mb?.toFixed(2)} MB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Données envoyées</Typography>
              <Typography variant="h4" color="secondary">
                {analytics?.statistics?.total_uploaded_mb?.toFixed(2)} MB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Bande passante moyenne</Typography>
              <Typography variant="h4" color="success.main">
                {analytics?.statistics?.average_bandwidth?.toFixed(2)} Mbps
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Appareils connectés */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Appareils utilisés
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Appareil</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Statut</TableCell>
                    <TableCell>Dernière connexion</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analytics?.devices?.map((device, index) => (
                    <TableRow key={index}>
                      <TableCell>{device.name || 'Inconnu'}</TableCell>
                      <TableCell>{device.type}</TableCell>
                      <TableCell>
                        <Chip 
                          label={device.is_trusted ? 'Fiable' : 'Non vérifié'}
                          color={device.is_trusted ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(device.last_seen).toLocaleString('fr-FR')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Activités récentes */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Activités récentes
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Heure</TableCell>
                    <TableCell>Données</TableCell>
                    <TableCell>Bande passante</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analytics?.recent_activities?.slice(0, 10).map((activity, index) => (
                    <TableRow key={index}>
                      <TableCell>{activity.type}</TableCell>
                      <TableCell>
                        {new Date(activity.timestamp).toLocaleTimeString('fr-FR')}
                      </TableCell>
                      <TableCell>{activity.data_transfer?.toFixed(2)} MB</TableCell>
                      <TableCell>{activity.bandwidth?.toFixed(2)} Mbps</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NetworkDashboard;