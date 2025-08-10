import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { ordersApi } from '../services/api';
import { Order } from '../types';

const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const data = await ordersApi.getOrders();
      setOrders(data);
    } catch (error) {
      console.error('Error loading orders:', error);
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

  const columns: GridColDef[] = [
    { field: 'order_number', headerName: 'Order #', width: 130 },
    { field: 'client_name', headerName: 'Client', width: 200 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value?.toUpperCase() || 'UNKNOWN'}
          color={getStatusColor(params.value) as any}
          size="small"
        />
      ),
    },
    {
      field: 'total_amount',
      headerName: 'Total',
      width: 120,
      renderCell: (params) => formatCurrency(params.value),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 150,
      renderCell: (params) => new Date(params.value).toLocaleDateString(),
    },
    {
      field: 'delivery_method',
      headerName: 'Delivery',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value?.toUpperCase() || 'N/A'}
          variant="outlined"
          size="small"
        />
      ),
    },
  ];

  const rows = orders.map((order) => ({
    id: order.id,
    order_number: order.order_number,
    client_name: order.client.full_name,
    status: order.status,
    total_amount: order.pricing.total_amount,
    created_at: order.created_at,
    delivery_method: order.delivery_method,
  }));

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Orders</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => {
            // TODO: Implement create order dialog
            console.log('Create new order');
          }}
        >
          New Order
        </Button>
      </Box>

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 10 },
            },
          }}
          pageSizeOptions={[10, 25, 50]}
          checkboxSelection
          disableRowSelectionOnClick
        />
      </Box>
    </Box>
  );
};

export default OrdersPage; 