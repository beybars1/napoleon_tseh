import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Avatar,
  Paper,
  InputAdornment,
  IconButton,
  Divider,
  useTheme,
  alpha,
} from '@mui/material';
import { 
  LockOutlined, 
  Person, 
  Lock, 
  Visibility, 
  VisibilityOff,
  Cake,
  Store,
  TrendingUp
} from '@mui/icons-material';
import { authApi } from '../services/api';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const theme = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.login({ username, password });
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      let errorMessage = 'Login failed. Please try again.';
      
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Handle Pydantic validation errors
          errorMessage = err.response.data.detail.map((e: any) => e.msg).join(', ');
        } else if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background decorations */}
      <Box sx={{
        position: 'absolute',
        top: -100,
        left: -100,
        width: 300,
        height: 300,
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.1)',
        animation: 'float 6s ease-in-out infinite',
      }} />
      <Box sx={{
        position: 'absolute',
        bottom: -150,
        right: -150,
        width: 400,
        height: 400,
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.05)',
        animation: 'float 8s ease-in-out infinite reverse',
      }} />

      <Container component="main" maxWidth="sm">
        <Paper sx={{
          borderRadius: 4,
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        }}>
          {/* Header Section */}
          <Box sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            textAlign: 'center',
            py: 6,
            position: 'relative',
            overflow: 'hidden'
          }}>
            <Box sx={{
              position: 'absolute',
              top: -20,
              right: -20,
              width: 100,
              height: 100,
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.1)',
            }} />
            
            <Avatar sx={{ 
              mx: 'auto',
              mb: 2,
              width: 80, 
              height: 80,
              background: 'rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)',
              border: '2px solid rgba(255, 255, 255, 0.3)',
            }}>
              <Cake sx={{ fontSize: 40 }} />
            </Avatar>
            
            <Typography variant="h4" sx={{ 
              fontWeight: 700, 
              mb: 1,
              textShadow: '0 2px 10px rgba(0,0,0,0.2)'
            }}>
              Napoleon-Tseh
            </Typography>
            <Typography variant="h6" sx={{ 
              opacity: 0.9,
              fontWeight: 400,
              fontSize: '1.1rem'
            }}>
              Bakery Management System
            </Typography>
            
            {/* Feature highlights */}
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              gap: 3, 
              mt: 3,
              flexWrap: 'wrap'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Store sx={{ fontSize: 20 }} />
                <Typography variant="body2">Order Management</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp sx={{ fontSize: 20 }} />
                <Typography variant="body2">Analytics</Typography>
              </Box>
            </Box>
          </Box>

          {/* Login Form */}
          <CardContent sx={{ p: 6 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Typography variant="h5" sx={{ 
                fontWeight: 600, 
                color: 'text.primary',
                mb: 1
              }}>
                Welcome Back
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to access your bakery dashboard
              </Typography>
            </Box>

            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 3,
                  borderRadius: 2,
                  '& .MuiAlert-icon': {
                    fontSize: 20
                  }
                }}
              >
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(0, 0, 0, 0.02)',
                      boxShadow: `0 0 0 3px ${alpha(theme.palette.primary.main, 0.1)}`,
                    }
                  }
                }}
              />
              
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={togglePasswordVisibility}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(0, 0, 0, 0.02)',
                      boxShadow: `0 0 0 3px ${alpha(theme.palette.primary.main, 0.1)}`,
                    }
                  }
                }}
              />
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  fontWeight: 600,
                  fontSize: '1rem',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 30px rgba(102, 126, 234, 0.6)',
                  },
                  '&:disabled': {
                    background: 'rgba(0, 0, 0, 0.12)',
                    transform: 'none',
                    boxShadow: 'none',
                  }
                }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </Box>

            <Divider sx={{ my: 4 }}>
              <Typography variant="body2" color="text.secondary">
                Demo Credentials
              </Typography>
            </Divider>

            <Paper sx={{ 
              p: 3, 
              bgcolor: 'rgba(102, 126, 234, 0.05)',
              border: '1px solid rgba(102, 126, 234, 0.1)',
              borderRadius: 2,
              textAlign: 'center'
            }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 600 }}>
                Default Admin Credentials
              </Typography>
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 2
              }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Username:</strong> admin
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Password:</strong> admin123
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </CardContent>
        </Paper>
      </Container>

      <style>
        {`
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
          }
        `}
      </style>
    </Box>
  );
};

export default LoginPage; 