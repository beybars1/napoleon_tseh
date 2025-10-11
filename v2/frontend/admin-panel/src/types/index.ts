export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Order {
  id: string;
  customerName: string;
  products: Array<{
    id: string;
    name: string;
    quantity: number;
    price: number;
  }>;
  totalAmount: number;
  status: 'pending' | 'processing' | 'completed' | 'cancelled';
  orderDate: string;
  deliveryTime: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  image?: string;
  available: boolean;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  orderHistory: Array<{
    orderId: string;
    date: string;
    amount: number;
  }>;
}
