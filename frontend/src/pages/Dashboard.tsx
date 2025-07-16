import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Avatar,
  Paper,
  LinearProgress,
  IconButton,
  Divider,
  useTheme,
  alpha,
} from '@mui/material';
import {
  ShoppingCart,
  AttachMoney,
  People,
  TrendingUp,
  ArrowUpward,
  ArrowDownward,
  MoreVert,
  LocalShipping,
  Schedule,
  CheckCircle,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line } from 'recharts';
import { ordersApi } from '../services/api';
import { DashboardStats, Order } from '../types';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [statsData, ordersData] = await Promise.all([
        ordersApi.getOrderStats(),
        ordersApi.getOrders(0, 10),
      ]);

      // Validate and transform stats data
      if (!statsData || typeof statsData !== 'object') {
        throw new Error('Invalid stats data received from server');
      }

      // Validate orders data
      if (!Array.isArray(ordersData)) {
        throw new Error('Invalid orders data received from server');
      }

      // Transform stats data to match DashboardStats interface
      const transformedStats: DashboardStats = {
        total_orders: statsData.total_orders || 0,
        total_revenue: statsData.total_revenue || 0,
        status_breakdown: statsData.status_breakdown || {},
        recent_orders: ordersData.slice(0, 5) || [],
        active_conversations: 0, // We'll add this later
      };

      setStats(transformedStats);
      setRecentOrders(ordersData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load dashboard data. Please check if the backend server is running.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'confirmed':
        return 'info';
      case 'in_progress':
        return 'primary';
      case 'ready':
        return 'success';
      case 'delivered':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} thickness={4} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography variant="h6" color="error">
          {error}
        </Typography>
      </Box>
    );
  }

  if (!stats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography variant="h6" color="text.secondary">
          No data available
        </Typography>
      </Box>
    );
  }

  const pieData = Object.entries(stats.status_breakdown || {}).map(([key, value]) => ({
    name: key.replace('_', ' ').toUpperCase(),
    value: typeof value === 'number' ? value : 0,
  }));

  const barData = Object.entries(stats.status_breakdown || {}).map(([key, value]) => ({
    status: key.replace('_', ' ').toUpperCase(),
    count: typeof value === 'number' ? value : 0,
  }));

  const StatCard = ({ title, value, icon, color, trend, subtitle }: any) => (
    <Card sx={{
      background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
      border: `1px solid ${color}20`,
      borderRadius: 3,
      overflow: 'hidden',
      position: 'relative',
      transition: 'all 0.3s ease',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: `0 12px 40px ${color}25`,
      }
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: color, mb: 0.5 }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ 
            bgcolor: color, 
            width: 56, 
            height: 56,
            boxShadow: `0 8px 24px ${color}40`
          }}>
            {icon}
          </Avatar>
        </Box>
        {trend && (
          <Box display="flex" alignItems="center" mt={2}>
            <Box display="flex" alignItems="center" sx={{ 
              color: trend > 0 ? 'success.main' : 'error.main',
              bgcolor: trend > 0 ? 'success.light' : 'error.light',
              px: 1,
              py: 0.5,
              borderRadius: 1,
              fontSize: '0.75rem',
              fontWeight: 600
            }}>
              {trend > 0 ? <ArrowUpward sx={{ fontSize: 16, mr: 0.5 }} /> : <ArrowDownward sx={{ fontSize: 16, mr: 0.5 }} />}
              {Math.abs(trend)}%
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              vs last month
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back! Here's what's happening with your bakery today.
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Chip 
            label="Live Data" 
            color="success" 
            variant="outlined"
            sx={{ 
              fontWeight: 600,
              '&::before': {
                content: '""',
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: 'success.main',
                marginRight: 1,
                animation: 'pulse 2s infinite'
              }
            }}
          />
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Total Orders"
            value={stats.total_orders}
            icon={<ShoppingCart />}
            color="#6366f1"
            trend={12.5}
            subtitle="This month"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Total Revenue"
            value={formatCurrency(stats.total_revenue)}
            icon={<AttachMoney />}
            color="#10b981"
            trend={8.2}
            subtitle="This month"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Active Orders"
            value={(stats.status_breakdown.pending || 0) + (stats.status_breakdown.in_progress || 0)}
            icon={<Schedule />}
            color="#f59e0b"
            trend={-2.4}
            subtitle="In progress"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Avg Order Value"
            value={formatCurrency(stats.total_orders > 0 ? stats.total_revenue / stats.total_orders : 0)}
            icon={<TrendingUp />}
            color="#8b5cf6"
            trend={15.8}
            subtitle="Per order"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{
            borderRadius: 3,
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
            overflow: 'hidden'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Order Status Distribution
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{
            borderRadius: 3,
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
            overflow: 'hidden'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Orders by Status
                </Typography>
                <IconButton size="small">
                  <MoreVert />
                </IconButton>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="status" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Orders */}
      <Card sx={{
        borderRadius: 3,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
        border: '1px solid rgba(0, 0, 0, 0.05)',
        overflow: 'hidden'
      }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ p: 3, borderBottom: '1px solid rgba(0, 0, 0, 0.05)' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Recent Orders
              </Typography>
              <Chip label={`${recentOrders.length} orders`} size="small" color="primary" variant="outlined" />
            </Box>
          </Box>
          <List sx={{ p: 0 }}>
            {recentOrders.slice(0, 5).map((order, index) => (
              <ListItem key={order.id} sx={{ 
                py: 2, 
                px: 3,
                borderBottom: index < 4 ? '1px solid rgba(0, 0, 0, 0.05)' : 'none',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.02)'
                }
              }}>
                <Avatar sx={{ 
                  mr: 2, 
                  bgcolor: getStatusColor(order.status) === 'success' ? 'success.main' : 
                           getStatusColor(order.status) === 'warning' ? 'warning.main' :
                           getStatusColor(order.status) === 'error' ? 'error.main' : 'primary.main',
                  width: 40,
                  height: 40
                }}>
                  {getStatusColor(order.status) === 'success' ? <CheckCircle /> : 
                   getStatusColor(order.status) === 'warning' ? <Schedule /> :
                   getStatusColor(order.status) === 'error' ? <ArrowDownward /> : <LocalShipping />}
                </Avatar>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={2}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {order.order_number || 'N/A'}
                      </Typography>
                      <Chip
                        label={order.status?.toUpperCase() || 'UNKNOWN'}
                        color={getStatusColor(order.status) as any}
                        size="small"
                        sx={{ fontWeight: 600 }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box mt={1}>
                      <Typography variant="body2" color="text.secondary">
                        {order.client?.full_name || 'Unknown Client'} • {formatCurrency(order.pricing?.total_amount || 0)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {order.created_at ? new Date(order.created_at).toLocaleDateString() : 'Unknown Date'}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 