import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { RootState } from '@/redux/store';
import { orderService } from '@/services/orderService';
import { setOrders, setLoading, setError } from '@/redux/slices/ordersSlice';
import { MainLayout } from '@/components/layout/MainLayout';

const OrdersPage = () => {
  const dispatch = useDispatch();
  const { orders, loading, error } = useSelector((state: RootState) => state.orders);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        dispatch(setLoading(true));
        const orders = await orderService.getOrders();
        dispatch(setOrders(orders));
      } catch (error) {
        dispatch(setError(error instanceof Error ? error.message : 'Error fetching orders'));
      } finally {
        dispatch(setLoading(false));
      }
    };

    fetchOrders();
  }, [dispatch]);

  if (loading) return <Typography>Загрузка...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <MainLayout>
      <Box>
        <Typography variant="h4" gutterBottom>
          Заказы
        </Typography>
        <Grid container spacing={3}>
          {orders.map((order) => (
            <Grid item xs={12} md={6} lg={4} key={order.id}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">{order.customerName}</Typography>
                <Typography>Статус: {order.status}</Typography>
                <Typography>Дата: {order.orderDate}</Typography>
                <Typography>Время доставки: {order.deliveryTime}</Typography>
                <Typography>Сумма: {order.totalAmount} тг</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
    </MainLayout>
  );
};

export default OrdersPage;
