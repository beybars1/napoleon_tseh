import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  CircularProgress,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Divider,
} from '@mui/material';
import {
  Chat,
  WhatsApp,
  Telegram,
  Email,
  Phone,
  Instagram,
  Send,
  Person,
  SmartToy,
} from '@mui/icons-material';
import { conversationsApi } from '../services/api';
import { Conversation } from '../types';

const ConversationsPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [messageError, setMessageError] = useState('');

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoading(true);
      const data = await conversationsApi.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedConversation || !newMessage.trim()) {
      setMessageError('Message cannot be empty');
      return;
    }

    try {
      setSendingMessage(true);
      setMessageError('');
      await conversationsApi.sendMessage(selectedConversation.id, {
        content: newMessage,
        message_type: 'text',
      });
      setNewMessage('');
      setMessageDialogOpen(false);
      // Refresh conversations to get updated messages
      await loadConversations();
    } catch (error: any) {
      setMessageError(error.message || 'Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return <WhatsApp color="success" />;
      case 'telegram':
        return <Telegram color="info" />;
      case 'email':
        return <Email color="secondary" />;
      case 'sms':
        return <Phone color="primary" />;
      case 'instagram':
        return <Instagram sx={{ color: '#E4405F' }} />;
      default:
        return <Chat color="action" />;
    }
  };

  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return 'success';
      case 'telegram':
        return 'info';
      case 'email':
        return 'secondary';
      case 'sms':
        return 'primary';
      case 'instagram':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSenderIcon = (senderType: string) => {
    switch (senderType) {
      case 'client':
        return <Person />;
      case 'ai':
        return <SmartToy />;
      case 'system':
        return <Chat />;
      default:
        return <Person />;
    }
  };

  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Conversations
      </Typography>

      {conversations.length === 0 ? (
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Chat sx={{ mr: 2 }} />
              <Typography variant="h6">
                Multi-Channel Communication
              </Typography>
            </Box>
            <Typography variant="body1" color="text.secondary">
              No conversations yet. Customer messages from WhatsApp, Telegram, SMS, Email, and Instagram will appear here.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 3, height: '70vh' }}>
          {/* Conversations List */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Conversations ({conversations.length})
              </Typography>
              <List sx={{ maxHeight: '60vh', overflow: 'auto' }}>
                {conversations.map((conversation) => (
                  <ListItem
                    key={conversation.id}
                    component="div"
                    onClick={() => setSelectedConversation(conversation)}
                    sx={{
                      border: selectedConversation?.id === conversation.id ? '2px solid' : '1px solid',
                      borderColor: selectedConversation?.id === conversation.id ? 'primary.main' : 'divider',
                      borderRadius: 1,
                      mb: 1,
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar>
                        {getChannelIcon(conversation.channel)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle1">
                            {conversation.client.full_name}
                          </Typography>
                          <Chip
                            label={conversation.channel.toUpperCase()}
                            color={getChannelColor(conversation.channel) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {conversation.messages.length > 0
                              ? conversation.messages[conversation.messages.length - 1].content.substring(0, 50) + '...'
                              : 'No messages yet'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {conversation.messages.length} messages • {formatMessageTime(conversation.updated_at || conversation.created_at)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Messages View */}
          <Card>
            <CardContent>
              {selectedConversation ? (
                <>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Avatar>
                        {getChannelIcon(selectedConversation.channel)}
                      </Avatar>
                      <Box>
                        <Typography variant="h6">
                          {selectedConversation.client.full_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {selectedConversation.channel.toUpperCase()} • {selectedConversation.messages.length} messages
                        </Typography>
                      </Box>
                    </Box>
                    <Button
                      variant="contained"
                      startIcon={<Send />}
                      onClick={() => setMessageDialogOpen(true)}
                    >
                      Send Message
                    </Button>
                  </Box>

                  <Divider sx={{ mb: 2 }} />

                  <Box sx={{ height: '50vh', overflow: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2 }}>
                    {selectedConversation.messages.length === 0 ? (
                      <Typography variant="body2" color="text.secondary" textAlign="center">
                        No messages in this conversation yet.
                      </Typography>
                    ) : (
                      selectedConversation.messages.map((message) => (
                        <Box
                          key={message.id}
                          sx={{
                            display: 'flex',
                            mb: 2,
                            flexDirection: message.sender_type === 'client' ? 'row' : 'row-reverse',
                          }}
                        >
                          <Avatar sx={{ mr: message.sender_type === 'client' ? 1 : 0, ml: message.sender_type === 'client' ? 0 : 1 }}>
                            {getSenderIcon(message.sender_type)}
                          </Avatar>
                          <Box
                            sx={{
                              maxWidth: '70%',
                              p: 1.5,
                              borderRadius: 2,
                              backgroundColor: message.sender_type === 'client' ? 'grey.100' : 'primary.light',
                              color: message.sender_type === 'client' ? 'text.primary' : 'primary.contrastText',
                            }}
                          >
                            <Typography variant="body2">
                              {message.content}
                            </Typography>
                            <Typography variant="caption" sx={{ opacity: 0.7, display: 'block', mt: 0.5 }}>
                              {formatMessageTime(message.created_at)}
                              {message.is_ai_processed && ' • AI Processed'}
                            </Typography>
                            {message.ai_response && (
                              <Box sx={{ mt: 1, p: 1, backgroundColor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
                                <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                  AI Response:
                                </Typography>
                                <Typography variant="body2" sx={{ mt: 0.5 }}>
                                  {message.ai_response}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        </Box>
                      ))
                    )}
                  </Box>
                </>
              ) : (
                <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="60vh">
                  <Chat sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Select a conversation to view messages
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Send Message Dialog */}
      <Dialog open={messageDialogOpen} onClose={() => setMessageDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Message</DialogTitle>
        <DialogContent>
          {messageError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {messageError}
            </Alert>
          )}
          <TextField
            label="Message"
            multiline
            rows={4}
            fullWidth
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message here..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMessageDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSendMessage} variant="contained" disabled={sendingMessage}>
            {sendingMessage ? 'Sending...' : 'Send Message'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConversationsPage; 