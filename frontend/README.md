# Napoleon-Tseh CRM Frontend

A modern React TypeScript application for managing cake orders, customers, and multi-channel communications.

## Features

- **Dashboard**: Real-time statistics and order overview
- **Order Management**: Complete order lifecycle management
- **Customer Management**: Multi-channel customer profiles
- **Product Catalog**: Cake and pastry inventory management
- **Kitchen Dashboard**: Optimized interface for kitchen staff
- **Multi-Channel Communication**: WhatsApp, Telegram, SMS, Email, Instagram
- **AI-Powered Responses**: Automated customer service
- **Real-time Updates**: Live order status updates

## Tech Stack

- **React 19** with TypeScript
- **Material-UI (MUI)** for components and styling
- **React Router** for navigation
- **Axios** for API communication
- **Recharts** for data visualization
- **Day.js** for date handling

## Getting Started

### Prerequisites

- Node.js 16 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=Napoleon-Tseh CRM
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App

## Default Login Credentials

- **Username**: admin
- **Password**: admin123

## API Integration

The frontend communicates with the FastAPI backend through RESTful APIs:

- Authentication: JWT token-based
- Real-time updates: WebSocket connections
- File uploads: Multipart form data
- Error handling: Centralized error management

## Components Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main layout with navigation
│   └── ProtectedRoute.tsx
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── OrdersPage.tsx  # Order management
│   ├── ClientsPage.tsx # Customer management
│   ├── ProductsPage.tsx # Product catalog
│   ├── ConversationsPage.tsx # Multi-channel chat
│   ├── KitchenDashboard.tsx # Kitchen interface
│   └── LoginPage.tsx   # Authentication
├── services/           # API services
│   └── api.ts         # API client and endpoints
├── types/             # TypeScript type definitions
│   └── index.ts
└── App.tsx            # Main application component
```

## Key Features

### Dashboard
- Real-time order statistics
- Revenue tracking
- Order status distribution charts
- Recent orders overview

### Kitchen Dashboard
- Optimized for kitchen workflow
- Real-time order updates
- One-click status updates
- Special instructions highlighting

### Order Management
- Complete order lifecycle
- Status tracking
- Customer information
- Payment status

### Multi-Channel Communication
- WhatsApp Business API
- Telegram Bot
- SMS via Twilio
- Email integration
- Instagram messaging

## Deployment

1. Build the production bundle:
```bash
npm run build
```

2. Deploy the `build` folder to your hosting service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary software for Napoleon-Tseh cake business.
