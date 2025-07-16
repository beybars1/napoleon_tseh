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
  FormControlLabel,
  Switch,
} from '@mui/material';
import { Add, Category, AttachMoney } from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { productsApi } from '../services/api';
import { Product } from '../types';

const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<Product>>({
    name: '',
    description: '',
    category: 'cake',
    base_price: 0,
    is_available: true,
    preparation_time: 30,
    dietary_info: '',
    ingredients: [],
    customization_options: {
      sizes: [],
      flavors: [],
      decorations: [],
    },
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await productsApi.getProducts();
      setProducts(data);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || formData.base_price === undefined || formData.base_price <= 0) {
      setFormError('Name and base price are required');
      return;
    }

    try {
      setSubmitting(true);
      setFormError('');
      await productsApi.createProduct(formData);
      setDialogOpen(false);
      setFormData({
        name: '',
        description: '',
        category: 'cake',
        base_price: 0,
        is_available: true,
        preparation_time: 30,
        dietary_info: '',
        ingredients: [],
        customization_options: {
          sizes: [],
          flavors: [],
          decorations: [],
        },
      });
      await loadProducts();
    } catch (error: any) {
      setFormError(error.message || 'Failed to create product');
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'cake':
        return 'primary';
      case 'pastry':
        return 'secondary';
      case 'dessert':
        return 'success';
      case 'beverage':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold">
          #{params.value}
        </Typography>
      ),
    },
    {
      field: 'name',
      headerName: 'Product Name',
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
      field: 'description',
      headerName: 'Description',
      width: 250,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ 
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {params.value || 'No description'}
        </Typography>
      ),
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value.toUpperCase()}
          color={getCategoryColor(params.value) as any}
          size="small"
          icon={<Category />}
        />
      ),
    },
    {
      field: 'is_available',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Available' : 'Unavailable'}
          color={params.value ? 'success' : 'error'}
          size="small"
        />
      ),
    },
    {
      field: 'base_price',
      headerName: 'Price',
      width: 120,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <AttachMoney sx={{ mr: 0.5, fontSize: 16 }} />
          <Typography variant="body2" fontWeight="bold">
            {formatCurrency(params.value)}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'cost',
      headerName: 'Cost',
      width: 120,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <Typography variant="body2" color="text.secondary">
            {formatCurrency(params.value || 0)}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'ingredients',
      headerName: 'Ingredients',
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ 
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {Array.isArray(params.value) ? params.value.join(', ') : params.value || 'N/A'}
        </Typography>
      ),
    },
    {
      field: 'preparation_time',
      headerName: 'Prep Time',
      width: 100,
      renderCell: (params) => (
        <Typography variant="body2">
          {params.value} min
        </Typography>
      ),
    },
    {
      field: 'dietary_info',
      headerName: 'Dietary Info',
      width: 150,
      renderCell: (params) => (
        <Typography variant="body2">
          {params.value || 'N/A'}
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}>
            Products
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your bakery's product catalog and inventory
          </Typography>
        </Box>
        <Button 
          variant="contained" 
          startIcon={<Add />} 
          onClick={() => setDialogOpen(true)}
          sx={{
            borderRadius: 2,
            px: 3,
            py: 1.5,
            fontWeight: 600,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 8px 30px rgba(102, 126, 234, 0.6)',
            }
          }}
        >
          New Product
        </Button>
      </Box>

      <Box sx={{ 
        height: 600, 
        width: '100%',
        '& .MuiDataGrid-root': {
          border: 'none',
          borderRadius: 3,
          backgroundColor: 'white',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#f8fafc',
            borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
            '& .MuiDataGrid-columnHeader': {
              fontWeight: 600,
              fontSize: '0.875rem',
              color: 'text.primary',
            }
          },
          '& .MuiDataGrid-row': {
            '&:hover': {
              backgroundColor: 'rgba(102, 126, 234, 0.04)',
            },
            '&.Mui-selected': {
              backgroundColor: 'rgba(102, 126, 234, 0.08)',
              '&:hover': {
                backgroundColor: 'rgba(102, 126, 234, 0.12)',
              }
            }
          },
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid rgba(0, 0, 0, 0.03)',
            fontSize: '0.875rem',
          }
        }
      }}>
        <DataGrid
          rows={products}
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

      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
          }
        }}
      >
        <DialogTitle sx={{ 
          pb: 2,
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          fontWeight: 600
        }}>
          New Product
        </DialogTitle>
        <DialogContent sx={{ p: 4 }}>
          {formError && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 3,
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  fontSize: 20
                }
              }}
            >
              {formError}
            </Alert>
          )}
          
          <Box sx={{ display: 'grid', gap: 3, mt: 1 }}>
            <TextField
              label="Product Name"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                }
              }}
            />
            
            <TextField
              label="Description"
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                }
              }}
            />
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Category"
                select
                SelectProps={{ native: true }}
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              >
                <option value="cake">Cake</option>
                <option value="pastry">Pastry</option>
                <option value="dessert">Dessert</option>
                <option value="beverage">Beverage</option>
              </TextField>
              
              <TextField
                label="Base Price"
                type="number"
                required
                value={formData.base_price}
                onChange={(e) => setFormData({ ...formData, base_price: parseFloat(e.target.value) || 0 })}
                InputProps={{
                  startAdornment: '$',
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              />
            </Box>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField
                label="Preparation Time (minutes)"
                type="number"
                value={formData.preparation_time}
                onChange={(e) => setFormData({ ...formData, preparation_time: parseInt(e.target.value) || 0 })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              />
              
              <Box sx={{ display: 'flex', alignItems: 'center', pt: 1 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_available}
                      onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                      color="primary"
                    />
                  }
                  label="Available"
                  sx={{ fontWeight: 500 }}
                />
              </Box>
            </Box>
            
            <TextField
              label="Dietary Information"
              placeholder="e.g., Gluten-free, Vegan, Contains nuts"
              value={formData.dietary_info}
              onChange={(e) => setFormData({ ...formData, dietary_info: e.target.value })}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                }
              }}
            />
            
            <TextField
              label="Ingredients"
              multiline
              rows={2}
              placeholder="List main ingredients..."
              value={formData.ingredients?.join(', ') || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                ingredients: e.target.value.split(',').map(s => s.trim()).filter(s => s)
              })}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                }
              }}
            />
            
            <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 600, color: 'text.primary' }}>
              Customization Options (comma-separated):
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2 }}>
              <TextField
                label="Available Sizes"
                placeholder="Small, Medium, Large"
                value={formData.customization_options?.sizes?.join(', ') || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  customization_options: {
                    ...formData.customization_options,
                    sizes: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                  }
                })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              />
              
              <TextField
                label="Available Flavors"
                placeholder="Vanilla, Chocolate, Strawberry"
                value={formData.customization_options?.flavors?.join(', ') || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  customization_options: {
                    ...formData.customization_options,
                    flavors: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                  }
                })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              />
              
              <TextField
                label="Available Decorations"
                placeholder="Roses, Sprinkles, Fondant"
                value={formData.customization_options?.decorations?.join(', ') || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  customization_options: {
                    ...formData.customization_options,
                    decorations: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                  }
                })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(0, 0, 0, 0.05)' }}>
          <Button 
            onClick={() => setDialogOpen(false)}
            sx={{ 
              borderRadius: 2,
              px: 3,
              fontWeight: 500
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={submitting}
            sx={{
              borderRadius: 2,
              px: 3,
              py: 1,
              fontWeight: 600,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
              '&:hover': {
                boxShadow: '0 8px 30px rgba(102, 126, 234, 0.6)',
              }
            }}
          >
            {submitting ? 'Creating...' : 'Create Product'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProductsPage; 