import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  useTheme,
  alpha,
  Paper,
  Chip,
} from '@mui/material';
import {
  Dashboard,
  ShoppingCart,
  People,
  Inventory,
  Chat,
  Restaurant,
  Logout,
  AccountCircle,
  Menu as MenuIcon,
  Notifications,
  Settings,
} from '@mui/icons-material';
import { authApi } from '../services/api';

const drawerWidth = 280;

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard', color: '#6366f1' },
  { text: 'Orders', icon: <ShoppingCart />, path: '/orders', color: '#f59e0b' },
  { text: 'Clients', icon: <People />, path: '/clients', color: '#10b981' },
  { text: 'Products', icon: <Inventory />, path: '/products', color: '#8b5cf6' },
  { text: 'Conversations', icon: <Chat />, path: '/conversations', color: '#06b6d4' },
  { text: 'Kitchen', icon: <Restaurant />, path: '/kitchen', color: '#f97316' },
];

const Layout: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    authApi.logout();
    navigate('/login');
    handleMenuClose();
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ 
      height: '100%', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background decoration */}
      <Box sx={{
        position: 'absolute',
        top: -50,
        right: -50,
        width: 200,
        height: 200,
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.1)',
        zIndex: 0,
      }} />
      
      {/* Header */}
      <Box sx={{ 
        p: 3, 
        textAlign: 'center',
        position: 'relative',
        zIndex: 1,
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <Typography variant="h5" sx={{ 
          color: 'white', 
          fontWeight: 700,
          textShadow: '0 2px 4px rgba(0,0,0,0.1)',
          mb: 0.5
        }}>
          Napoleon-Tseh
        </Typography>
        <Typography variant="body2" sx={{ 
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.85rem'
        }}>
          Bakery Management System
        </Typography>
      </Box>

      {/* Navigation */}
      <List sx={{ px: 2, py: 2 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  px: 2,
                  backgroundColor: isActive ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                  backdropFilter: isActive ? 'blur(10px)' : 'none',
                  border: isActive ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid transparent',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    transform: 'translateX(4px)',
                  },
                }}
              >
                <ListItemIcon sx={{ 
                  color: isActive ? 'white' : 'rgba(255, 255, 255, 0.8)',
                  minWidth: 40,
                  '& .MuiSvgIcon-root': {
                    fontSize: '1.3rem',
                    filter: isActive ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' : 'none'
                  }
                }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    sx: {
                      color: isActive ? 'white' : 'rgba(255, 255, 255, 0.9)',
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '0.95rem',
                    }
                  }}
                />
                {isActive && (
                  <Box sx={{
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    backgroundColor: 'white',
                    boxShadow: '0 0 8px rgba(255, 255, 255, 0.6)',
                  }} />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Bottom decoration */}
      <Box sx={{
        position: 'absolute',
        bottom: -30,
        left: -30,
        width: 120,
        height: 120,
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.05)',
        zIndex: 0,
      }} />
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
          color: theme.palette.text.primary,
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ 
              fontWeight: 600,
              color: theme.palette.text.primary,
              textTransform: 'capitalize'
            }}>
              {location.pathname.slice(1) || 'Dashboard'}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              size="large"
              color="inherit"
              sx={{ 
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                '&:hover': { backgroundColor: alpha(theme.palette.primary.main, 0.2) }
              }}
            >
              <Notifications />
            </IconButton>
            
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
              <Avatar sx={{ 
                width: 36, 
                height: 36,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                fontSize: '1rem',
                fontWeight: 600
              }}>
                A
              </Avatar>
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        id="primary-search-account-menu"
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            mt: 1.5,
            minWidth: 200,
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
          }
        }}
      >
        <MenuItem onClick={handleMenuClose} sx={{ py: 1.5 }}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          Profile
        </MenuItem>
        <MenuItem onClick={handleMenuClose} sx={{ py: 1.5 }}>
          <ListItemIcon>
            <Settings fontSize="small" />
          </ListItemIcon>
          Settings
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout} sx={{ py: 1.5, color: 'error.main' }}>
          <ListItemIcon>
            <Logout fontSize="small" sx={{ color: 'error.main' }} />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="mailbox folders"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, border: 'none' },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, border: 'none' },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: '#f8fafc',
          minHeight: '100vh',
          backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.02) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.02) 0%, transparent 50%)',
        }}
      >
        <Toolbar />
        <Paper sx={{ 
          p: 0, 
          borderRadius: 3,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          border: '1px solid rgba(0, 0, 0, 0.02)',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(10px)',
          overflow: 'hidden'
        }}>
          <Box sx={{ p: 4 }}>
            <Outlet />
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default Layout; 