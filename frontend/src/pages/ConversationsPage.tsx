import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItemText,
  ListItemAvatar,
  ListItemButton,
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
  Paper,
  Badge,
  IconButton,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  Chat,
  Telegram,
  Send,
  SmartToy,
  Refresh,
  Search,
  MoreVert,
  CheckCircle,
  Close,
} from '@mui/icons-material';
import { conversationsApi } from '../services/api';
import { Conversation } from '../types';

interface TelegramChat {
  conversation_id: number;
  client: {
    id: number;
    name: string;
    telegram_id: string;
    phone: string;
  };
  stats: {
    message_count: number;
    unread_count: number;
    ai_enabled: boolean;
  };
  last_message: {
    content: string;
    direction: 'incoming' | 'outgoing';
    message_type: string;
    created_at: string;
    ai_intent?: string;
  } | null;
  created_at: string;
  last_message_at: string | null;
}

interface ChatMessage {
  id: number;
  direction: 'incoming' | 'outgoing';
  content: string;
  message_type: string;
  created_at: string;
  external_id: string;
  ai_data?: {
    processed: boolean;
    intent?: string;
    entities?: any;
    confidence?: number;
    response?: string;
  } | null;
}

const ConversationsPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [telegramChats, setTelegramChats] = useState<TelegramChat[]>([]);
  const [selectedChat, setSelectedChat] = useState<TelegramChat | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatsLoading, setChatsLoading] = useState(false); // Separate loading state for chats
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'all' | 'telegram'>('telegram');
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [messageError, setMessageError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [apiError, setApiError] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(false); // Disabled by default

  useEffect(() => {
    loadConversations();
    loadTelegramChats();
  }, []);

  // Auto-refresh chats every 30 seconds (reduced frequency)
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadTelegramChats();
    }, 30000); // 30 seconds instead of 10

    return () => clearInterval(interval);
  }, [autoRefresh]); // Removed selectedChat dependency to prevent loops

  // Refresh messages when selecting a chat (one-time only)
  useEffect(() => {
    if (selectedChat) {
      loadChatMessages(selectedChat.conversation_id);
    }
  }, [selectedChat?.conversation_id]); // Only trigger when conversation_id changes

  const loadConversations = async () => {
    try {
      const data = await conversationsApi.getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadTelegramChats = async () => {
    if (chatsLoading) return; // Prevent concurrent calls using separate loading state
    
    try {
      setChatsLoading(true);
      setApiError('');
      
      // Always get fresh data, no cache
      const response = await fetch(
        '/api/v1/conversations/conversations/telegram/chats?_t=' + Date.now(),
        {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setTelegramChats(data.chats || []);
    } catch (error) {
      console.error('❌ Error loading Telegram chats:', error);
      setApiError(`Failed to load chats: ${error}`);
    } finally {
      setChatsLoading(false);
      setLoading(false); // Set main loading to false after first load attempt
    }
  };

  const loadChatMessages = async (conversationId: number) => {
    if (messagesLoading) return; // Prevent concurrent calls
    
    try {
      setMessagesLoading(true);
      
      // Always get fresh data, no cache
      const response = await fetch(
        `/api/v1/conversations/conversations/${conversationId}/messages?limit=100&_t=${Date.now()}`,
        {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Sort messages by created_at to ensure proper order
      const sortedMessages = (data.messages || []).sort((a: ChatMessage, b: ChatMessage) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
      
      setChatMessages(sortedMessages);
    } catch (error) {
      console.error('❌ Error loading chat messages:', error);
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleChatSelect = (chat: TelegramChat) => {
    setSelectedChat(chat);
    loadChatMessages(chat.conversation_id);
  };

  const handleSendMessage = async () => {
    if (!selectedChat || !newMessage.trim()) {
      setMessageError('Message cannot be empty');
      return;
    }

    try {
      setSendingMessage(true);
      setMessageError('');
      await conversationsApi.sendMessage(selectedChat.conversation_id, {
        content: newMessage,
        message_type: 'text',
      });
      setNewMessage('');
      setMessageDialogOpen(false);
      // Refresh chat messages
      await loadChatMessages(selectedChat.conversation_id);
      await loadTelegramChats();
    } catch (error: any) {
      setMessageError(error.message || 'Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const formatLastMessageTime = (timestamp: string | null) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 3600);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getAvatarColor = (name: string) => {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF'];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  const filteredChats = telegramChats.filter(chat =>
    chat.client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (chat.last_message?.content || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading conversations...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            💬 Conversations
          </Typography>
          <Stack direction="row" spacing={1}>
            <Tooltip title={autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}>
              <IconButton 
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? "primary" : "default"}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              size="small"
              disabled={chatsLoading}
              onClick={() => {
                loadTelegramChats();
                if (selectedChat) {
                  loadChatMessages(selectedChat.conversation_id);
                }
              }}
              startIcon={chatsLoading ? <CircularProgress size={16} /> : <Refresh />}
            >
              {chatsLoading ? 'Loading...' : 'Refresh Now'}
            </Button>
            <Button
              variant={viewMode === 'telegram' ? 'contained' : 'outlined'}
              startIcon={<Telegram />}
              onClick={() => setViewMode('telegram')}
              size="small"
            >
              Telegram
            </Button>
            <Button
              variant={viewMode === 'all' ? 'contained' : 'outlined'}
              startIcon={<Chat />}
              onClick={() => setViewMode('all')}
              size="small"
            >
              All Channels
            </Button>
          </Stack>
        </Stack>
      </Box>

      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Chat List Sidebar */}
        <Paper 
          sx={{ 
            width: 380, 
            borderRight: 1, 
            borderColor: 'divider',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}
        >
          {/* Search Bar */}
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search conversations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Box>

          {/* Chat List */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {apiError && (
              <Alert severity="error" sx={{ m: 2 }}>
                {apiError}
              </Alert>
            )}
            
            {chatsLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
                <CircularProgress size={24} />
                <Typography sx={{ ml: 2 }}>Loading chats...</Typography>
              </Box>
            )}
            
            {!chatsLoading && viewMode === 'telegram' ? (
              <List sx={{ p: 0 }}>
                {filteredChats.map((chat) => (
                  <ListItemButton
                    key={chat.conversation_id}
                    onClick={() => handleChatSelect(chat)}
                    selected={selectedChat?.conversation_id === chat.conversation_id}
                    sx={{
                      borderBottom: 1,
                      borderColor: 'divider',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                      '&.Mui-selected': {
                        backgroundColor: 'primary.50',
                        borderRight: 3,
                        borderRightColor: 'primary.main',
                      },
                    }}
                  >
                    <ListItemAvatar>
                      <Badge
                        badgeContent={chat.stats.unread_count}
                        color="error"
                        overlap="circular"
                        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                      >
                        <Avatar
                          sx={{
                            bgcolor: getAvatarColor(chat.client.name),
                            width: 48,
                            height: 48,
                            fontSize: '1.2rem',
                            fontWeight: 600,
                          }}
                        >
                          {chat.client.name.charAt(0).toUpperCase()}
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>

                    <ListItemText
                      primary={
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {chat.client.name}
                          </Typography>
                          <Chip
                            icon={<Telegram />}
                            label="Telegram"
                            size="small"
                            color="info"
                            variant="outlined"
                          />
                          {chat.stats.ai_enabled && (
                            <Chip
                              icon={<SmartToy />}
                              label="AI"
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          )}
                        </Stack>
                      }
                      secondary={
                        <Box>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              maxWidth: 250,
                              mb: 0.5,
                            }}
                          >
                            {chat.last_message?.direction === 'outgoing' && (
                              <SmartToy sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                            )}
                            {chat.last_message?.content || 'No messages yet'}
                          </Typography>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <Typography variant="caption" color="text.secondary">
                              {formatLastMessageTime(chat.last_message_at)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              • {chat.stats.message_count} messages
                            </Typography>
                            {chat.last_message?.ai_intent && (
                              <Chip
                                label={chat.last_message.ai_intent}
                                size="small"
                                variant="outlined"
                                sx={{ height: 16, fontSize: '0.65rem' }}
                              />
                            )}
                          </Stack>
                        </Box>
                      }
                    />
                  </ListItemButton>
                ))}
                {filteredChats.length === 0 && (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Telegram sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      No Telegram chats found
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Start a conversation with your Telegram bot to see chats here
                    </Typography>
                  </Box>
                )}
              </List>
            ) : (
              // Original all channels view
              <Typography sx={{ p: 2 }}>All channels view (original implementation)</Typography>
            )}
          </Box>
        </Paper>

        {/* Chat Messages Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {selectedChat ? (
            <>
              {/* Chat Header */}
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar
                      sx={{
                        bgcolor: getAvatarColor(selectedChat.client.name),
                        width: 40,
                        height: 40,
                      }}
                    >
                      {selectedChat.client.name.charAt(0).toUpperCase()}
                    </Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {selectedChat.client.name}
                      </Typography>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Chip
                          icon={<Telegram />}
                          label={`@${selectedChat.client.telegram_id}`}
                          size="small"
                          variant="outlined"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {selectedChat.stats.message_count} messages
                        </Typography>
                        {autoRefresh && (
                          <Chip
                            label="Auto-refresh ON"
                            size="small"
                            color="success"
                            variant="outlined"
                            sx={{ fontSize: '0.6rem', height: 20 }}
                          />
                        )}
                        {messagesLoading && (
                          <Chip
                            icon={<CircularProgress size={12} />}
                            label="Loading..."
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.6rem', height: 20 }}
                          />
                        )}
                      </Stack>
                    </Box>
                  </Stack>
                  <Stack direction="row" spacing={1}>
                    <IconButton
                      onClick={() => loadChatMessages(selectedChat.conversation_id)}
                      disabled={messagesLoading}
                      title="Refresh messages"
                    >
                      <Refresh />
                    </IconButton>
                    <IconButton
                      onClick={() => setMessageDialogOpen(true)}
                      color="primary"
                      sx={{ bgcolor: 'primary.50' }}
                    >
                      <Send />
                    </IconButton>
                    <IconButton>
                      <MoreVert />
                    </IconButton>
                  </Stack>
                </Stack>
              </Box>

              {/* Messages */}
              <Box sx={{ flex: 1, overflow: 'auto', p: 2, bgcolor: '#f5f5f5' }}>
                {messagesLoading ? (
                  <Box display="flex" justifyContent="center" p={4}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <Stack spacing={1}>
                    {chatMessages.map((message, index) => (
                      <Box
                        key={message.id}
                        sx={{
                          display: 'flex',
                          justifyContent: message.direction === 'outgoing' ? 'flex-end' : 'flex-start',
                          mb: 1,
                        }}
                      >
                        <Paper
                          sx={{
                            p: 1.5,
                            maxWidth: '70%',
                            bgcolor: message.direction === 'outgoing' 
                              ? 'primary.main' 
                              : 'background.paper',
                            color: message.direction === 'outgoing' 
                              ? 'primary.contrastText' 
                              : 'text.primary',
                            borderRadius: 2,
                            boxShadow: 1,
                          }}
                        >
                          <Typography variant="body1" sx={{ mb: 0.5 }}>
                            {message.content}
                          </Typography>
                          
                          <Stack 
                            direction="row" 
                            alignItems="center" 
                            justifyContent="space-between"
                            spacing={1}
                          >
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                opacity: 0.7,
                                fontSize: '0.7rem'
                              }}
                            >
                              {formatMessageTime(message.created_at)}
                            </Typography>
                            
                            {message.direction === 'outgoing' && (
                              <CheckCircle sx={{ fontSize: 12, opacity: 0.7 }} />
                            )}
                            
                            {message.ai_data?.processed && (
                              <Tooltip title={`AI Intent: ${message.ai_data.intent || 'Unknown'}`}>
                                <SmartToy sx={{ fontSize: 12, opacity: 0.7 }} />
                              </Tooltip>
                            )}
                          </Stack>
                          
                          {message.ai_data?.intent && (
                            <Chip
                              label={message.ai_data.intent}
                              size="small"
                              sx={{ 
                                mt: 0.5, 
                                height: 18, 
                                fontSize: '0.6rem',
                                opacity: 0.8
                              }}
                            />
                          )}
                        </Paper>
                      </Box>
                    ))}
                    
                    {chatMessages.length === 0 && (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Chat sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          No messages yet
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Start the conversation by sending a message
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                )}
              </Box>
            </>
          ) : (
            /* No Chat Selected */
            <Box sx={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexDirection: 'column',
              bgcolor: 'background.default'
            }}>
              <Telegram sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" color="text.secondary" gutterBottom>
                Select a conversation
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Choose a chat from the sidebar to view messages
              </Typography>
            </Box>
          )}
        </Box>
      </Box>

      {/* Send Message Dialog */}
      <Dialog open={messageDialogOpen} onClose={() => setMessageDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Typography variant="h6">Send Message</Typography>
            <IconButton onClick={() => setMessageDialogOpen(false)}>
              <Close />
            </IconButton>
          </Stack>
        </DialogTitle>
        <DialogContent>
          {messageError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {messageError}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Message"
            type="text"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message here..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMessageDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSendMessage} 
            variant="contained"
            disabled={sendingMessage || !newMessage.trim()}
            startIcon={sendingMessage ? <CircularProgress size={16} /> : <Send />}
          >
            {sendingMessage ? 'Sending...' : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConversationsPage; 