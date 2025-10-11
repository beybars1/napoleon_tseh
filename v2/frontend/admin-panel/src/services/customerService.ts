import api from './api';
import { Customer } from '@/types';

export const customerService = {
  getCustomers: async () => {
    const response = await api.get('/customers');
    return response.data;
  },
  
  getCustomer: async (id: string) => {
    const response = await api.get(`/customers/${id}`);
    return response.data;
  },
  
  createCustomer: async (customerData: Omit<Customer, 'id'>) => {
    const response = await api.post('/customers', customerData);
    return response.data;
  },
  
  updateCustomer: async (id: string, customerData: Partial<Customer>) => {
    const response = await api.put(`/customers/${id}`, customerData);
    return response.data;
  },
  
  deleteCustomer: async (id: string) => {
    const response = await api.delete(`/customers/${id}`);
    return response.data;
  },
};
