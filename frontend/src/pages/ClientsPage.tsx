import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import { Add, Phone, Email, WhatsApp } from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { clientsApi } from '../services/api';
import { Client, CreateClientRequest } from '../types';

const ClientsPage: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<CreateClientRequest>({
    full_name: '',
    phone: '',
    email: '',
    whatsapp: '',
    telegram_username: '',
    instagram_handle: '',
    preferred_contact_method: 'phone',
    address: '',
    city: '',
    postal_code: '',
    notes: '',
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      setLoading(true);
      const data = await clientsApi.getClients();
      setClients(data);
    } catch (error) {
      console.error('Error loading clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.full_name || !formData.phone) {
      setFormError('Name and phone are required');
      return;
    }

    try {
      setSubmitting(true);
      setFormError('');
      await clientsApi.createClient(formData);
      setDialogOpen(false);
      setFormData({
        full_name: '',
        phone: '',
        email: '',
        whatsapp: '',
        telegram_username: '',
        instagram_handle: '',
        preferred_contact_method: 'phone',
        address: '',
        city: '',
        postal_code: '',
        notes: '',
      });
      await loadClients();
    } catch (error: any) {
      setFormError(error.message || 'Failed to create client');
    } finally {
      setSubmitting(false);
    }
  };

  const getContactMethodColor = (method: string) => {
    switch (method) {
      case 'phone':
        return 'primary';
      case 'email':
        return 'secondary';
      case 'whatsapp':
        return 'success';
      case 'telegram':
        return 'info';
      case 'instagram':
        return 'warning';
      default:
        return 'default';
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'full_name',
      headerName: 'Name',
      width: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="bold">
            {params.value}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'phone',
      headerName: 'Phone',
      width: 150,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <Phone sx={{ mr: 1, fontSize: 16 }} />
          {params.value}
        </Box>
      ),
    },
    {
      field: 'email',
      headerName: 'Email',
      width: 200,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <Email sx={{ mr: 1, fontSize: 16 }} />
          {params.value || 'N/A'}
        </Box>
      ),
    },
    {
      field: 'whatsapp',
      headerName: 'WhatsApp',
      width: 150,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <WhatsApp sx={{ mr: 1, fontSize: 16 }} />
          {params.value || 'N/A'}
        </Box>
      ),
    },
    {
      field: 'preferred_contact_method',
      headerName: 'Preferred Contact',
      width: 150,
      renderCell: (params) => (
        <Chip
          label={params.value?.toUpperCase() || 'N/A'}
          color={getContactMethodColor(params.value) as any}
          size="small"
        />
      ),
    },
    {
      field: 'city',
      headerName: 'City',
      width: 120,
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Clients</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          New Client
        </Button>
      </Box>

      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={clients}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 25 },
            },
          }}
          pageSizeOptions={[25, 50, 100]}
          disableRowSelectionOnClick
        />
      </Box>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Client</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          
          <Box sx={{ display: 'grid', gap: 2, mt: 1 }}>
            <TextField
              label="Full Name"
              required
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Phone"
                required
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
              <TextField
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Box>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="WhatsApp"
                value={formData.whatsapp}
                onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
              />
              <TextField
                label="Telegram Username"
                value={formData.telegram_username}
                onChange={(e) => setFormData({ ...formData, telegram_username: e.target.value })}
              />
            </Box>
            
            <TextField
              label="Instagram Handle"
              value={formData.instagram_handle}
              onChange={(e) => setFormData({ ...formData, instagram_handle: e.target.value })}
            />
            
            <TextField
              label="Preferred Contact Method"
              select
              SelectProps={{ native: true }}
              value={formData.preferred_contact_method}
              onChange={(e) => setFormData({ ...formData, preferred_contact_method: e.target.value as any })}
            >
              <option value="phone">Phone</option>
              <option value="email">Email</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="telegram">Telegram</option>
              <option value="instagram">Instagram</option>
            </TextField>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 2 }}>
              <TextField
                label="Address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
              <TextField
                label="City"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
              <TextField
                label="Postal Code"
                value={formData.postal_code}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
              />
            </Box>
            
            <TextField
              label="Notes"
              multiline
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Client'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ClientsPage; 