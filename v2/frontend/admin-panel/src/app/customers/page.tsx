import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { RootState } from '@/redux/store';
import { customerService } from '@/services/customerService';
import { setCustomers, setLoading, setError } from '@/redux/slices/customersSlice';
import { MainLayout } from '@/components/layout/MainLayout';

const CustomersPage = () => {
  const dispatch = useDispatch();
  const { customers, loading, error } = useSelector((state: RootState) => state.customers);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        dispatch(setLoading(true));
        const customers = await customerService.getCustomers();
        dispatch(setCustomers(customers));
      } catch (error) {
        dispatch(setError(error instanceof Error ? error.message : 'Error fetching customers'));
      } finally {
        dispatch(setLoading(false));
      }
    };

    fetchCustomers();
  }, [dispatch]);

  if (loading) return <Typography>Загрузка...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <MainLayout>
      <Box>
        <Typography variant="h4" gutterBottom>
          Клиенты
        </Typography>
        <Grid container spacing={3}>
          {customers.map((customer) => (
            <Grid item xs={12} sm={6} md={4} key={customer.id}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">{customer.name}</Typography>
                <Typography>Телефон: {customer.phone}</Typography>
                {customer.email && (
                  <Typography>Email: {customer.email}</Typography>
                )}
                {customer.address && (
                  <Typography>Адрес: {customer.address}</Typography>
                )}
                <Typography variant="subtitle2" sx={{ mt: 1 }}>
                  История заказов
                </Typography>
                {customer.orderHistory.map((order) => (
                  <Box key={order.orderId} sx={{ mt: 1 }}>
                    <Typography variant="body2">
                      Дата: {order.date}
                    </Typography>
                    <Typography variant="body2">
                      Сумма: {order.amount} тг
                    </Typography>
                  </Box>
                ))}
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
    </MainLayout>
  );
};

export default CustomersPage;
