import api from './api';
import { Order } from '@/types';

export const orderService = {
  getOrders: async () => {
    const response = await api.get('/orders');
    return response.data;
  },
  
  getOrder: async (id: string) => {
    const response = await api.get(`/orders/${id}`);
    return response.data;
  },
  
  createOrder: async (orderData: Omit<Order, 'id'>) => {
    const response = await api.post('/orders', orderData);
    return response.data;
  },
  
  updateOrder: async (id: string, orderData: Partial<Order>) => {
    const response = await api.put(`/orders/${id}`, orderData);
    return response.data;
  },
  
  deleteOrder: async (id: string) => {
    const response = await api.delete(`/orders/${id}`);
    return response.data;
  },
};
