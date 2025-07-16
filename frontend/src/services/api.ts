import axios from 'axios';
import {
  User,
  Client,
  Product,
  Order,
  Conversation,
  DashboardStats,
  LoginRequest,
  AuthResponse,
  CreateClientRequest,
  CreateOrderRequest,
  UpdateOrderStatusRequest,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    // Extract error message from response
    let errorMessage = 'An error occurred';
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    // Create a clean error object
    const cleanError = new Error(errorMessage);
    cleanError.name = 'APIError';
    
    return Promise.reject(cleanError);
  }
);

// Authentication API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
};

// Clients API
export const clientsApi = {
  getClients: async (skip = 0, limit = 100): Promise<Client[]> => {
    const response = await api.get<Client[]>(`/clients/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getClient: async (id: number): Promise<Client> => {
    const response = await api.get<Client>(`/clients/${id}`);
    return response.data;
  },

  createClient: async (client: CreateClientRequest): Promise<Client> => {
    const response = await api.post<Client>('/clients/', client);
    return response.data;
  },

  updateClient: async (id: number, client: Partial<CreateClientRequest>): Promise<Client> => {
    const response = await api.put<Client>(`/clients/${id}`, client);
    return response.data;
  },

  deleteClient: async (id: number): Promise<void> => {
    await api.delete(`/clients/${id}`);
  },
};

// Products API
export const productsApi = {
  getProducts: async (skip = 0, limit = 100): Promise<Product[]> => {
    const response = await api.get<Product[]>(`/products/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getProduct: async (id: number): Promise<Product> => {
    const response = await api.get<Product>(`/products/${id}`);
    return response.data;
  },

  createProduct: async (product: Partial<Product>): Promise<Product> => {
    const response = await api.post<Product>('/products/', product);
    return response.data;
  },

  updateProduct: async (id: number, product: Partial<Product>): Promise<Product> => {
    const response = await api.put<Product>(`/products/${id}`, product);
    return response.data;
  },

  deleteProduct: async (id: number): Promise<void> => {
    await api.delete(`/products/${id}`);
  },
};

// Orders API
export const ordersApi = {
  getOrders: async (skip = 0, limit = 100, status?: string): Promise<Order[]> => {
    let url = `/orders/?skip=${skip}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    const response = await api.get<Order[]>(url);
    return response.data;
  },

  getOrder: async (id: number): Promise<Order> => {
    const response = await api.get<Order>(`/orders/${id}`);
    return response.data;
  },

  createOrder: async (order: CreateOrderRequest): Promise<{ message: string; order: any }> => {
    const response = await api.post<{ message: string; order: any }>('/orders/', order);
    return response.data;
  },

  updateOrderStatus: async (id: number, status: UpdateOrderStatusRequest): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>(`/orders/${id}/status`, status);
    return response.data;
  },

  updatePaymentStatus: async (id: number, paymentStatus: { payment_status: string }): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>(`/orders/${id}/payment-status`, paymentStatus);
    return response.data;
  },

  getOrderStats: async (): Promise<{ total_orders: number; total_revenue: number; status_breakdown: Record<string, number> }> => {
    const response = await api.get<{ total_orders: number; total_revenue: number; status_breakdown: Record<string, number> }>('/orders/stats/summary');
    return response.data;
  },
};

// Conversations API
export const conversationsApi = {
  getConversations: async (skip = 0, limit = 100): Promise<Conversation[]> => {
    const response = await api.get<Conversation[]>(`/conversations/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getConversation: async (id: number): Promise<Conversation> => {
    const response = await api.get<Conversation>(`/conversations/${id}`);
    return response.data;
  },

  sendMessage: async (conversationId: number, message: { content: string; message_type?: string }): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(`/conversations/${conversationId}/messages`, message);
    return response.data;
  },
};

export default api; 