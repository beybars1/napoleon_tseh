import React from 'react';
import { useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  ShoppingCart as OrdersIcon,
  Cake as ProductsIcon,
  People as CustomersIcon,
  AttachMoney as RevenueIcon,
} from '@mui/icons-material';
import { Line } from 'recharts';
import { RootState } from '@/redux/store';
import { MainLayout } from '@/components/layout/MainLayout';

const DashboardPage = () => {
  const orders = useSelector((state: RootState) => state.orders.orders);
  const products = useSelector((state: RootState) => state.products.products);
  const customers = useSelector((state: RootState) => state.customers.customers);

  const totalRevenue = orders.reduce((sum, order) => sum + order.totalAmount, 0);

  const stats = [
    {
      title: 'Всего заказов',
      value: orders.length,
      icon: <OrdersIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Продукты',
      value: products.length,
      icon: <ProductsIcon sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
    },
    {
      title: 'Клиенты',
      value: customers.length,
      icon: <CustomersIcon sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
    },
    {
      title: 'Общий доход',
      value: `${totalRevenue.toLocaleString()} тг`,
      icon: <RevenueIcon sx={{ fontSize: 40 }} />,
      color: '#9c27b0',
    },
  ];

  return (
    <MainLayout>
      <Box>
        <Typography variant="h4" gutterBottom>
          Панель управления
        </Typography>

        <Grid container spacing={3}>
          {stats.map((stat) => (
            <Grid item xs={12} sm={6} md={3} key={stat.title}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                  bgcolor: stat.color,
                  color: 'white',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  {stat.icon}
                  <Typography variant="h4">{stat.value}</Typography>
                </Box>
                <Typography variant="h6" sx={{ mt: 2 }}>
                  {stat.title}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Последние заказы
          </Typography>
          <Grid container spacing={3}>
            {orders.slice(0, 5).map((order) => (
              <Grid item xs={12} key={order.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{order.customerName}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Дата: {order.orderDate}
                    </Typography>
                    <Typography>Сумма: {order.totalAmount} тг</Typography>
                    <Typography>Статус: {order.status}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Box>
    </MainLayout>
  );
};

export default DashboardPage;
