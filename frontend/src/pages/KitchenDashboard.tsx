import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { Restaurant, Timer, CheckCircle } from '@mui/icons-material';
import { ordersApi } from '../services/api';
import { Order } from '../types';

const KitchenDashboard: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
    // Set up polling for real-time updates
    const interval = setInterval(loadOrders, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const data = await ordersApi.getOrders();
      // Filter for kitchen-relevant orders
      const kitchenOrders = data.filter(order => 
        ['confirmed', 'in_progress'].includes(order.status)
      );
      setOrders(kitchenOrders);
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId: number, status: string) => {
    try {
      await ordersApi.updateOrderStatus(orderId, { status: status as any });
      await loadOrders(); // Refresh the list
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'info';
      case 'in_progress':
        return 'warning';
      case 'ready':
        return 'success';
      default:
        return 'default';
    }
  };

  const getTimeAgo = (dateString: string) => {
    const now = new Date();
    const orderTime = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - orderTime.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours}h ago`;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Restaurant sx={{ mr: 2, fontSize: 40 }} />
        <Typography variant="h4">Kitchen Dashboard</Typography>
      </Box>

      <Grid container spacing={3}>
        {orders.length === 0 ? (
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Box display="flex" flexDirection="column" alignItems="center" py={4}>
                  <CheckCircle sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                  <Typography variant="h6" color="success.main">
                    All caught up!
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No pending orders at the moment.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          orders.map((order) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={order.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  border: order.status === 'confirmed' ? '2px solid #2196f3' : 'none',
                  boxShadow: order.status === 'confirmed' ? '0 4px 8px rgba(33, 150, 243, 0.3)' : undefined
                }}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" component="div">
                      {order.order_number}
                    </Typography>
                    <Chip
                      label={order.status.toUpperCase()}
                      color={getStatusColor(order.status) as any}
                      size="small"
                    />
                  </Box>

                  <Box display="flex" alignItems="center" mb={2}>
                    <Timer sx={{ mr: 1, fontSize: 16 }} />
                    <Typography variant="body2" color="text.secondary">
                      {getTimeAgo(order.created_at)}
                    </Typography>
                  </Box>

                  <Typography variant="subtitle2" gutterBottom>
                    Customer: {order.client.full_name}
                  </Typography>

                  <Typography variant="subtitle2" gutterBottom>
                    Items:
                  </Typography>
                  <List dense>
                    {order.items.map((item, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemText
                          primary={`${item.quantity}x ${item.product.name}`}
                          secondary={
                            <Box>
                              {item.size && <Typography variant="caption">Size: {item.size}</Typography>}
                              {item.flavor && <Typography variant="caption" display="block">Flavor: {item.flavor}</Typography>}
                              {item.decorations && <Typography variant="caption" display="block">Decorations: {item.decorations}</Typography>}
                              {item.special_instructions && (
                                <Typography variant="caption" display="block" color="warning.main">
                                  Special: {item.special_instructions}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>

                  {order.special_instructions && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                      <Typography variant="caption" color="warning.dark">
                        Order Notes: {order.special_instructions}
                      </Typography>
                    </Box>
                  )}

                  <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    {order.status === 'confirmed' && (
                      <Button
                        variant="contained"
                        color="warning"
                        size="small"
                        fullWidth
                        onClick={() => updateOrderStatus(order.id, 'in_progress')}
                      >
                        Start Preparing
                      </Button>
                    )}
                    {order.status === 'in_progress' && (
                      <Button
                        variant="contained"
                        color="success"
                        size="small"
                        fullWidth
                        onClick={() => updateOrderStatus(order.id, 'ready')}
                      >
                        Mark Ready
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>
    </Box>
  );
};

export default KitchenDashboard; 