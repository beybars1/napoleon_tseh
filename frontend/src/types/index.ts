// API Response Types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'staff' | 'cook';
  is_active: boolean;
  created_at: string;
}

// Client Types
export interface Client {
  id: number;
  full_name: string;
  name: string; // Add this for compatibility
  phone?: string;
  email?: string;
  whatsapp?: string;
  telegram?: string;
  instagram?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  notes?: string;
  total_orders: number;
  total_spent: number;
  last_order?: string;
  preferred_contact_method: string;
  created_at: string;
}

// Product Types
export interface Product {
  id: number;
  name: string;
  category: 'cake' | 'pastry' | 'dessert' | 'beverage' | 'other';
  description?: string;
  base_price: number;
  cost: number;
  image_url?: string;
  is_available: boolean;
  is_customizable: boolean;
  available_sizes?: string[];
  available_flavors?: string[];
  available_decorations?: string[];
  preparation_time: number;
  ingredients?: string[];
  allergens?: string[];
  dietary_info?: string;
  customization_options?: {
    sizes?: string[];
    flavors?: string[];
    decorations?: string[];
  };
  created_at: string;
}

// Order Types
export interface OrderItem {
  id: number;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
  size?: string;
  flavor?: string;
  decorations?: string;
  customizations?: any;
  special_instructions?: string;
}

export interface Order {
  id: number;
  uuid: string;
  order_number: string;
  status: 'pending' | 'confirmed' | 'in_progress' | 'ready' | 'delivered' | 'cancelled';
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded';
  delivery_method: 'pickup' | 'delivery';
  client: Client;
  items: OrderItem[];
  pricing: {
    subtotal: number;
    tax_amount: number;
    delivery_fee: number;
    discount_amount: number;
    total_amount: number;
  };
  delivery?: {
    address?: string;
    city?: string;
    postal_code?: string;
    instructions?: string;
  };
  timing: {
    requested_delivery_time?: string;
    estimated_completion_time?: string;
    actual_completion_time?: string;
  };
  special_instructions?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

// Conversation Types
export interface Message {
  id: number;
  content: string;
  message_type: 'text' | 'image' | 'file';
  sender_type: 'client' | 'system' | 'ai';
  is_ai_processed: boolean;
  ai_response?: string;
  media_url?: string;
  external_id?: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  channel: 'whatsapp' | 'telegram' | 'sms' | 'email' | 'instagram';
  channel_identifier: string;
  client: Client;
  messages: Message[];
  is_active: boolean;
  last_message_at: string;
  created_at: string;
  updated_at?: string;
}

// Dashboard Types
export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  status_breakdown: Record<string, number>;
  recent_orders: Order[];
  active_conversations: number;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Form Types
export interface CreateClientRequest {
  full_name: string;
  phone?: string;
  email?: string;
  whatsapp?: string;
  telegram_username?: string;
  instagram_handle?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  notes?: string;
  preferred_contact_method: string;
}

export interface CreateOrderRequest {
  client_id: number;
  items: {
    product_id: number;
    quantity: number;
    size?: string;
    flavor?: string;
    decorations?: string;
    customizations?: any;
    special_instructions?: string;
  }[];
  delivery_method: 'pickup' | 'delivery';
  delivery_address?: string;
  special_instructions?: string;
}

export interface UpdateOrderStatusRequest {
  status: Order['status'];
} 