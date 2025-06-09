import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/CaptivePortal.css';

const API_URL = 'http://localhost:8000/api';

const CaptivePortal = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [sessionId, setSessionId] = useState(null);
    const [remainingTime, setRemainingTime] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // Vérifier si une session existe déjà
        const storedSessionId = localStorage.getItem('sessionId');
        const storedToken = localStorage.getItem('accessToken');
        
        if (storedSessionId && storedToken) {
            setSessionId(storedSessionId);
            checkSessionStatus(storedSessionId, storedToken);
        }
    }, []);

    const checkSessionStatus = async (sessionId, token) => {
        try {
            const response = await axios.get(`${API_URL}/captive-portal/check-status/`, {
                params: { session_id: sessionId },
                headers: { Authorization: `Bearer ${token}` }
            });
            
            if (response.data.is_active) {
                setRemainingTime(response.data.remaining_time);
            } else {
                handleLogout();
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du statut:', error);
            handleLogout();
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            console.log('Tentative de connexion...');  // Debug log
            const response = await axios.post(`${API_URL}/captive-portal/login/`, {
                username,
                password
            });

            console.log('Réponse reçue:', response.data);  // Debug log

            const { access_token, refresh_token, session_id, user } = response.data;
            
            // Stocker les tokens et l'ID de session
            localStorage.setItem('accessToken', access_token);
            localStorage.setItem('refreshToken', refresh_token);
            localStorage.setItem('sessionId', session_id);
            localStorage.setItem('user', JSON.stringify(user));
            
            setSessionId(session_id);
            setRemainingTime(null);
            
            // Configurer axios pour utiliser le token
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
            
        } catch (error) {
            console.error('Erreur de connexion:', error);  // Debug log
            if (error.response) {
                // La requête a été faite et le serveur a répondu avec un code d'état
                // qui est en dehors de la plage 2xx
                setError(error.response.data.error || 'Une erreur est survenue lors de la connexion');
            } else if (error.request) {
                // La requête a été faite mais aucune réponse n'a été reçue
                setError('Impossible de se connecter au serveur. Veuillez vérifier votre connexion internet.');
            } else {
                // Une erreur s'est produite lors de la configuration de la requête
                setError('Une erreur est survenue lors de la connexion');
            }
        } finally {
            setIsLoading(false);
        }
    };

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
            setRemainingTime(null);
            delete axios.defaults.headers.common['Authorization'];
        }
    };

    if (sessionId) {
        return (
            <div className="captive-portal-container">
                <div className="portal-card">
                    <h2>Session Active</h2>
                    {remainingTime && (
                        <p>Temps restant: {remainingTime} minutes</p>
                    )}
                    <button 
                        className="logout-button"
                        onClick={handleLogout}
                    >
                        Se déconnecter
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="captive-portal-container">
            <div className="portal-card">
                <h2>Connexion au Portail Captif</h2>
                {error && <div className="error-message">{error}</div>}
                <form onSubmit={handleLogin}>
                    <div className="form-group">
                        <label htmlFor="username">Nom d'utilisateur</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Mot de passe</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button 
                        type="submit" 
                        className="login-button"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Connexion...' : 'Se connecter'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default CaptivePortal; 