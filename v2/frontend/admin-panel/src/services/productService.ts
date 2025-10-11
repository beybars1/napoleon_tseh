import api from './api';
import { Product } from '@/types';

export const productService = {
  getProducts: async () => {
    const response = await api.get('/products');
    return response.data;
  },
  
  getProduct: async (id: string) => {
    const response = await api.get(`/products/${id}`);
    return response.data;
  },
  
  createProduct: async (productData: Omit<Product, 'id'>) => {
    const response = await api.post('/products', productData);
    return response.data;
  },
  
  updateProduct: async (id: string, productData: Partial<Product>) => {
    const response = await api.put(`/products/${id}`, productData);
    return response.data;
  },
  
  deleteProduct: async (id: string) => {
    const response = await api.delete(`/products/${id}`);
    return response.data;
  },
};
