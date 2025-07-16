import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

// Components
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import OrdersPage from './pages/OrdersPage';
import ClientsPage from './pages/ClientsPage';
import ProductsPage from './pages/ProductsPage';
import ConversationsPage from './pages/ConversationsPage';
import KitchenDashboard from './pages/KitchenDashboard';
import ProtectedRoute from './components/ProtectedRoute';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="clients" element={<ClientsPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="conversations" element={<ConversationsPage />} />
              <Route path="kitchen" element={<KitchenDashboard />} />
            </Route>
          </Routes>
        </Router>
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;
