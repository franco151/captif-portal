import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import QrScanner from 'react-qr-scanner';
import {
  Box,
  Button,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Link,
  Snackbar
} from '@mui/material';
import {
  ConfirmationNumber as TicketIcon,
  ShoppingCart as ShopIcon,
  QrCodeScanner as QrIcon,
  Login as LoginIcon,
  Facebook as FacebookIcon,
  Phone as PhoneIcon,
  Support as SupportIcon,
  Close as CloseIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import '../styles/CaptivePortal.css';

const API_URL = 'http://localhost:8000/api';

// SUPPRIMER COMPLÈTEMENT ce bloc d'imports dupliqués (lignes 40-56 environ) :
// import {
//   Box,
//   Button,
//   Container,
//   Typography,
//   Paper,
//   Grid,
//   Card,
//   CardContent,
//   TextField,
//   Alert,
//   CircularProgress,
//   Dialog,
//   DialogTitle,
//   DialogContent,
//   DialogActions,
//   Divider,
//   Link
// } from '@mui/material';

const CaptivePortal = () => {
    const navigate = useNavigate();
    const [sessionId, setSessionId] = useState(null);
    const [showAuthDialog, setShowAuthDialog] = useState(false);
    const [authMethod, setAuthMethod] = useState('login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showQRScanner, setShowQRScanner] = useState(false);
    const [qrScanError, setQrScanError] = useState('');
    // Nouveaux états pour l'alerte d'appareil
    const [showDeviceAlert, setShowDeviceAlert] = useState(false);
    const [deviceAlertMessage, setDeviceAlertMessage] = useState('');

    // Définir handleLogout avant son utilisation
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
            setSessionId(null);
            delete axios.defaults.headers.common['Authorization'];
        }
    };

    const checkSessionStatus = async (sessionId, token) => {
        try {
            const response = await axios.get(`${API_URL}/captive-portal/check-status/`, {
                params: { session_id: sessionId },
                headers: { Authorization: `Bearer ${token}` }
            });
            
            if (response.data.is_active) {
                navigate('/success');
            } else {
                handleLogout();
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du statut:', error);
            handleLogout();
        }
    };

    useEffect(() => {
        // Vérifier si une session existe déjà
        const storedSessionId = localStorage.getItem('sessionId');
        const storedToken = localStorage.getItem('accessToken');
        
        if (storedSessionId && storedToken) {
            setSessionId(storedSessionId);
            checkSessionStatus(storedSessionId, storedToken);
        }
    }, [checkSessionStatus]); // Ajouter checkSessionStatus aux dépendances

    const generateDeviceFingerprint = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
        
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            window.screen.width + 'x' + window.screen.height, // Correction ici
            new Date().getTimezoneOffset(),
            canvas.toDataURL()
        ].join('|');
        
        // Générer un hash simple
        let hash = 0;
        for (let i = 0; i < fingerprint.length; i++) {
            const char = fingerprint.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        return Math.abs(hash).toString(16);
    };
    
    // Modifier la fonction handleLogin
    const handleLogin = async () => {
        if (!username || !password) {
            setError('Veuillez remplir tous les champs');
            return;
        }
    
        setIsLoading(true);
        setError('');
    
        try {
            const deviceFingerprint = generateDeviceFingerprint();
            
            const response = await axios.post(`${API_URL}/captive-portal/login/`, {
                username,
                password,
                mac_address: deviceFingerprint
            });

            const { access_token, refresh_token, session_id, user } = response.data;
            
            // Stocker les tokens et l'ID de session
            localStorage.setItem('accessToken', access_token);
            localStorage.setItem('refreshToken', refresh_token);
            localStorage.setItem('sessionId', session_id);
            localStorage.setItem('user', JSON.stringify(user));
            
            setSessionId(session_id);
            setShowAuthDialog(false);
            
            // Configurer axios pour utiliser le token
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
            
            // Rediriger vers la page de bienvenue
            navigate('/success');
            
        } catch (error) {
            console.error('Erreur de connexion:', error);
            if (error.response) {
                // Vérifier si c'est l'erreur de device déjà utilisé
                if (error.response.data.error === 'DEVICE_ALREADY_USED') {
                    setDeviceAlertMessage(error.response.data.message);
                    setShowDeviceAlert(true);
                    setShowAuthDialog(false); // Fermer le dialog de connexion
                } else {
                    setError(error.response.data.error || 'Une erreur est survenue lors de la connexion');
                }
            } else if (error.request) {
                setError('Impossible de se connecter au serveur. Veuillez vérifier votre connexion internet.');
            } else {
                setError('Une erreur est survenue lors de la connexion');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleTicketAuth = async () => {
        setShowAuthDialog(true);
        setAuthMethod('login');
    };

    const handleBuyTicket = () => {
        navigate('/plans');
    };

    const handleQRAuth = () => {
        setAuthMethod('qr');
        setShowQRScanner(true);
        setError('');
        setQrScanError('');
    };

    const handleQRScan = (data) => {
        if (data) {
            try {
                // Le QR code devrait contenir les données au format JSON
                const credentials = JSON.parse(data);
                
                if (credentials.username && credentials.password) {
                    setUsername(credentials.username);
                    setPassword(credentials.password);
                    setShowQRScanner(false);
                    
                    // Utiliser handleLogin au lieu d'authenticateUser
                    handleLogin({ preventDefault: () => {} });
                } else {
                    setQrScanError('QR code invalide : format de données incorrect');
                }
            } catch (error) {
                // Si ce n'est pas du JSON, essayer de parser comme "username:password"
                const parts = data.split(':');
                if (parts.length === 2) {
                    const [user, pass] = parts;
                    setUsername(user);
                    setPassword(pass);
                    setShowQRScanner(false);
                    handleLogin({ preventDefault: () => {} });
                } else {
                    setQrScanError('QR code invalide : format non reconnu');
                }
            }
        }
    };

    const handleQRError = (error) => {
        console.error('Erreur de scan QR:', error);
        setQrScanError('Erreur lors du scan du QR code. Vérifiez votre caméra.');
    };

    const handleCloseDeviceAlert = () => {
        setShowDeviceAlert(false);
        setDeviceAlertMessage('');
    };

    // Si l'utilisateur a une session active, rediriger vers success
    if (sessionId) {
        navigate('/success');
        return null;
    }

    return (
        <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Container maxWidth="md" sx={{ py: 4, flex: 1 }}>
                <Paper 
                    elevation={8} 
                    sx={{ 
                        p: 6, 
                        textAlign: 'center',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        borderRadius: 4
                    }}
                >
                    {/* Titre principal */}
                    <Typography 
                        variant="h1" 
                        component="h1" 
                        sx={{ 
                            fontSize: { xs: '2.5rem', md: '3.5rem' },
                            fontWeight: 'bold',
                            mb: 2,
                            textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
                        }}
                    >
                        BestConnect
                    </Typography>

                    {/* Message de bienvenue en Malagasy */}
                    <Typography 
                        variant="h5" 
                        component="h2" 
                        sx={{ 
                            mb: 6,
                            fontWeight: 300,
                            opacity: 0.9,
                            lineHeight: 1.4
                        }}
                    >
                        Tonga soa eto amin'ny service de fournisseur connection internet illimité
                    </Typography>

                    {/* Boutons principaux */}
                    <Grid container spacing={4} justifyContent="center">
                        <Grid item xs={12} sm={6} md={5}>
                            <Card 
                                sx={{ 
                                    height: '100%',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-8px)',
                                        boxShadow: '0 12px 24px rgba(0,0,0,0.2)'
                                    }
                                }}
                                onClick={handleTicketAuth}
                            >
                                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                                    <TicketIcon 
                                        sx={{ 
                                            fontSize: 60, 
                                            color: 'primary.main', 
                                            mb: 2 
                                        }} 
                                    />
                                    <Typography 
                                        variant="h4" 
                                        component="h3" 
                                        sx={{ 
                                            fontWeight: 'bold',
                                            color: 'text.primary',
                                            mb: 2
                                        }}
                                    >
                                        Manana Ticket
                                    </Typography>
                                    <Typography 
                                        variant="body1" 
                                        color="text.secondary"
                                        sx={{ lineHeight: 1.6 }}
                                    >
                                        Connectez-vous avec vos identifiants ou scannez votre QR code
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>

                        <Grid item xs={12} sm={6} md={5}>
                            <Card 
                                sx={{ 
                                    height: '100%',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-8px)',
                                        boxShadow: '0 12px 24px rgba(0,0,0,0.2)'
                                    }
                                }}
                                onClick={handleBuyTicket}
                            >
                                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                                    <ShopIcon 
                                        sx={{ 
                                            fontSize: 60, 
                                            color: 'secondary.main', 
                                            mb: 2 
                                        }} 
                                    />
                                    <Typography 
                                        variant="h4" 
                                        component="h3" 
                                        sx={{ 
                                            fontWeight: 'bold',
                                            color: 'text.primary',
                                            mb: 2
                                        }}
                                    >
                                        Hividy Ticket
                                    </Typography>
                                    <Typography 
                                        variant="body1" 
                                        color="text.secondary"
                                        sx={{ lineHeight: 1.6 }}
                                    >
                                        Découvrez nos forfaits et choisissez celui qui vous convient
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                </Paper>

                {/* Dialog d'authentification */}
                <Dialog 
                    open={showAuthDialog} 
                    onClose={() => setShowAuthDialog(false)}
                    maxWidth="sm"
                    fullWidth
                >
                    <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
                        <Typography variant="h4" component="h2">
                            Authentification
                        </Typography>
                    </DialogTitle>
                    
                    <DialogContent sx={{ pt: 2 }}>
                        {/* Boutons de choix de méthode d'authentification */}
                        <Box sx={{ mb: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
                            <Button
                                variant={authMethod === 'login' ? 'contained' : 'outlined'}
                                startIcon={<LoginIcon />}
                                onClick={() => {
                                    setAuthMethod('login');
                                    setShowQRScanner(false);
                                }}
                            >
                                Identifiants
                            </Button>
                            <Button
                                variant={authMethod === 'qr' ? 'contained' : 'outlined'}
                                startIcon={<QrIcon />}
                                onClick={handleQRAuth}
                            >
                                QR Code
                            </Button>
                        </Box>

                        {authMethod === 'login' && (
                            <Box component="form" onSubmit={handleLogin}>
                                {error && (
                                    <Alert severity="error" sx={{ mb: 2 }}>
                                        {error}
                                    </Alert>
                                )}
                                
                                <TextField
                                    fullWidth
                                    label="Nom d'utilisateur"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    margin="normal"
                                    required
                                    autoFocus
                                />
                                
                                <TextField
                                    fullWidth
                                    label="Mot de passe"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    margin="normal"
                                    required
                                />
                            </Box>
                        )}

                        {authMethod === 'qr' && showQRScanner && (
                            <Box sx={{ textAlign: 'center' }}>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Scannez le QR code de votre reçu
                                </Typography>
                                
                                {qrScanError && (
                                    <Alert severity="error" sx={{ mb: 2 }}>
                                        {qrScanError}
                                    </Alert>
                                )}
                                
                                <Box sx={{ 
                                    width: '100%', 
                                    maxWidth: 400, 
                                    mx: 'auto',
                                    border: '2px solid #ddd',
                                    borderRadius: 2,
                                    overflow: 'hidden'
                                }}>
                                    <QrScanner
                                        delay={300}
                                        onError={handleQRError}
                                        onScan={handleQRScan}
                                        style={{ width: '100%' }}
                                        constraints={{
                                            video: {
                                                facingMode: 'environment' // Caméra arrière
                                            }
                                        }}
                                    />
                                </Box>
                                
                                <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
                                    Positionnez le QR code dans le cadre pour le scanner
                                </Typography>
                            </Box>
                        )}
                    </DialogContent>
                    
                    <DialogActions sx={{ p: 3, pt: 1 }}>
                        <Button 
                            onClick={() => {
                                setShowAuthDialog(false);
                                setShowQRScanner(false);
                            }}
                            disabled={isLoading}
                        >
                            Annuler
                        </Button>
                        
                        {authMethod === 'qr' && showQRScanner && (
                            <Button 
                                onClick={() => setShowQRScanner(false)}
                                startIcon={<CloseIcon />}
                            >
                                Fermer Scanner
                            </Button>
                        )}
                        
                        {authMethod === 'login' && (
                            <Button 
                                onClick={handleLogin}
                                variant="contained"
                                disabled={isLoading || !username || !password}
                                startIcon={isLoading ? <CircularProgress size={20} /> : null}
                            >
                                {isLoading ? 'Connexion...' : 'Se connecter'}
                            </Button>
                        )}
                    </DialogActions>
                </Dialog>
            </Container>

            {/* Footer avec informations de contact et service client */}
            <Paper 
                component="footer" 
                elevation={3} 
                sx={{ 
                    mt: 'auto',
                    py: 3,
                    px: 2,
                    backgroundColor: '#2c3e50',
                    color: 'white'
                }}
            >
                <Container maxWidth="lg">
                    <Grid container spacing={3} alignItems="center">
                        {/* Section Service Client */}
                        <Grid item xs={12} md={4}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <SupportIcon sx={{ mr: 1, color: '#3498db' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    Service Client
                                </Typography>
                            </Box>
                            <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                En cas de panne, problème ou question
                            </Typography>
                        </Grid>

                        {/* Section Contact Téléphone */}
                        <Grid item xs={12} md={4}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <PhoneIcon sx={{ mr: 1, color: '#27ae60' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    Contact
                                </Typography>
                            </Box>
                            <Link 
                                href="tel:+261347249715" 
                                sx={{ 
                                    color: 'white', 
                                    textDecoration: 'none',
                                    '&:hover': { textDecoration: 'underline' }
                                }}
                            >
                                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                                    034 72 497 15
                                </Typography>
                            </Link>
                            <Typography variant="body2" sx={{ opacity: 0.8 }}>
                                Disponible 24h/24 et 7j/7
                            </Typography>
                        </Grid>

                        {/* Section Facebook */}
                        <Grid item xs={12} md={4}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <FacebookIcon sx={{ mr: 1, color: '#3b5998' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    Facebook
                                </Typography>
                            </Box>
                            <Link 
                                href="https://facebook.com/BestConnect-FARAFANGANA" 
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{ 
                                    color: 'white', 
                                    textDecoration: 'none',
                                    '&:hover': { textDecoration: 'underline' }
                                }}
                            >
                                <Typography variant="body1">
                                    BestConnect FARAFANGANA
                                </Typography>
                            </Link>
                        </Grid>
                    </Grid>

                    <Divider sx={{ my: 2, backgroundColor: 'rgba(255,255,255,0.2)' }} />
                    
                    {/* Copyright */}
                    <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" sx={{ opacity: 0.7 }}>
                            © 2025 BestConnect FARAFANGANA. Tous droits réservés.
                        </Typography>
                    </Box>
                </Container>
            </Paper>
        </Box>
    );
};

// DELETE EVERYTHING BELOW THIS LINE - Remove lines 642-718
// All the code from line 642 onwards should be completely deleted
export default CaptivePortal;