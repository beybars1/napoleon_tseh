import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { RootState } from '@/redux/store';
import { productService } from '@/services/productService';
import { setProducts, setLoading, setError } from '@/redux/slices/productsSlice';
import { MainLayout } from '@/components/layout/MainLayout';

const ProductsPage = () => {
  const dispatch = useDispatch();
  const { products, loading, error } = useSelector((state: RootState) => state.products);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        dispatch(setLoading(true));
        const products = await productService.getProducts();
        dispatch(setProducts(products));
      } catch (error) {
        dispatch(setError(error instanceof Error ? error.message : 'Error fetching products'));
      } finally {
        dispatch(setLoading(false));
      }
    };

    fetchProducts();
  }, [dispatch]);

  if (loading) return <Typography>Загрузка...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <MainLayout>
      <Box>
        <Typography variant="h4" gutterBottom>
          Продукты
        </Typography>
        <Grid container spacing={3}>
          {products.map((product) => (
            <Grid item xs={12} sm={6} md={4} key={product.id}>
              <Paper sx={{ p: 2 }}>
                {product.image && (
                  <Box
                    component="img"
                    src={product.image}
                    alt={product.name}
                    sx={{ width: '100%', height: 200, objectFit: 'cover', mb: 2 }}
                  />
                )}
                <Typography variant="h6">{product.name}</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {product.description}
                </Typography>
                <Typography>Цена: {product.price} тг</Typography>
                <Typography>Категория: {product.category}</Typography>
                <Typography>
                  Статус: {product.available ? 'В наличии' : 'Нет в наличии'}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
    </MainLayout>
  );
};

export default ProductsPage;
