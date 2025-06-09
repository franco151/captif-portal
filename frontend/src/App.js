import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import CaptivePortal from './pages/CaptivePortal';
import './App.css';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Plans from './pages/Plans';
import Payment from './pages/Payment';
import Success from './pages/Success';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/portal" element={<CaptivePortal />} />
        <Route path="/" element={<Navigate to="/portal" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/plans" element={<Plans />} />
        <Route path="/payment/:planId" element={<Payment />} />
        <Route path="/success" element={<Success />} />
      </Routes>
    </Router>
  );
}

export default App;
