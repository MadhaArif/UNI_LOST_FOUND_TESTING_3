require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const http = require('http');
const socketIo = require('socket.io');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');
const tf = require('@tensorflow/tfjs-node');

// Import routes
const authRoutes = require('./routes/auth');
const postRoutes = require('./routes/posts');
const claimRoutes = require('./routes/claims');
const chatRoutes = require('./routes/chats');
const adminRoutes = require('./routes/admin');
const notificationRoutes = require('./routes/notifications');

// Import middleware
const { authMiddleware } = require('./middleware/auth');
const errorHandler = require('./middleware/errorHandler');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, '../public')));

// Set up file upload
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = path.join(__dirname, '../public/uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueFilename = `${uuidv4()}-${file.originalname}`;
    cb(null, uniqueFilename);
  }
});

const upload = multer({ 
  storage: storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'), false);
    }
  }
});

// Make upload available globally
app.use((req, res, next) => {
  req.upload = upload;
  next();
});

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/umt_belongings_hub', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB connected'))
.catch(err => console.error('MongoDB connection error:', err));

// Load TensorFlow MobileNet model for image feature extraction
let mobilenet;
async function loadModel() {
  try {
    mobilenet = await tf.loadLayersModel('https://storage.googleapis.com/tfjs-models/tfjs/mobilenet_v1_0.25_224/model.json');
    console.log('MobileNet model loaded successfully');
  } catch (error) {
    console.error('Error loading MobileNet model:', error);
  }
}
loadModel();

// Make TensorFlow model available globally
app.use((req, res, next) => {
  req.tf = tf;
  req.mobilenet = mobilenet;
  next();
});

// Socket.io setup
io.on('connection', (socket) => {
  console.log('New client connected');
  
  // Authenticate socket connection
  socket.on('authenticate', (token) => {
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.userId = decoded.userId;
      socket.join(`user:${decoded.userId}`);
      console.log(`User ${decoded.userId} authenticated`);
    } catch (error) {
      console.error('Socket authentication error:', error);
    }
  });
  
  // Join chat room
  socket.on('join:chat', (chatId) => {
    if (socket.userId) {
      socket.join(`chat:${chatId}`);
      console.log(`User ${socket.userId} joined chat ${chatId}`);
    }
  });
  
  // Leave chat room
  socket.on('leave:chat', (chatId) => {
    socket.leave(`chat:${chatId}`);
    console.log(`User left chat ${chatId}`);
  });
  
  // Send message
  socket.on('message:send', async ({ chatId, content }) => {
    if (!socket.userId) return;
    
    try {
      const Chat = require('./models/chat');
      const User = require('./models/user');
      
      const chat = await Chat.findById(chatId);
      if (!chat) return;
      
      // Check if user is participant
      if (!chat.participants.includes(socket.userId)) return;
      
      // Add message to chat
      chat.messages.push({
        sender: socket.userId,
        content,
        timestamp: Date.now(),
        read: false
      });
      
      chat.lastActivity = Date.now();
      await chat.save();
      
      // Get sender info
      const sender = await User.findById(socket.userId);
      
      // Emit to all participants
      const messageData = {
        _id: chat.messages[chat.messages.length - 1]._id,
        sender: {
          _id: sender._id,
          name: sender.firstName + ' ' + sender.lastName
        },
        content,
        timestamp: Date.now(),
        read: false
      };
      
      io.to(`chat:${chatId}`).emit('message:received', messageData);
      
      // Send notifications to other participants
      chat.participants.forEach(async (participantId) => {
        if (participantId.toString() !== socket.userId) {
          const participant = await User.findById(participantId);
          if (participant) {
            await participant.addNotification(
              `New message from ${sender.firstName} ${sender.lastName}`,
              'CHAT',
              `/dashboard?tab=chats&chat=${chatId}`
            );
            io.to(`user:${participantId}`).emit('notification:new');
          }
        }
      });
    } catch (error) {
      console.error('Error sending message:', error);
    }
  });
  
  // Mark messages as read
  socket.on('messages:read', async ({ chatId }) => {
    if (!socket.userId) return;
    
    try {
      const Chat = require('./models/chat');
      const chat = await Chat.findById(chatId);
      if (!chat) return;
      
      // Update unread messages
      chat.messages.forEach(message => {
        if (message.sender.toString() !== socket.userId && !message.read) {
          message.read = true;
        }
      });
      
      await chat.save();
      io.to(`chat:${chatId}`).emit('messages:updated', { chatId });
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  });
  
  // Typing indicator
  socket.on('typing:start', ({ chatId }) => {
    if (socket.userId) {
      socket.to(`chat:${chatId}`).emit('typing:update', {
        userId: socket.userId,
        isTyping: true
      });
    }
  });
  
  socket.on('typing:stop', ({ chatId }) => {
    if (socket.userId) {
      socket.to(`chat:${chatId}`).emit('typing:update', {
        userId: socket.userId,
        isTyping: false
      });
    }
  });
  
  // Disconnect
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// Make io available to routes
app.use((req, res, next) => {
  req.io = io;
  next();
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/posts', postRoutes);
app.use('/api/claims', authMiddleware, claimRoutes);
app.use('/api/chats', authMiddleware, chatRoutes);
app.use('/api/admin', authMiddleware, adminRoutes);
app.use('/api/notifications', authMiddleware, notificationRoutes);

// Serve HTML files
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../index.html'));
});

app.get('/lost', (req, res) => {
  res.sendFile(path.join(__dirname, '../lost.html'));
});

app.get('/found', (req, res) => {
  res.sendFile(path.join(__dirname, '../found.html'));
});

app.get('/dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, '../dashboard.html'));
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, '../admin.html'));
});

// Error handling middleware
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = { app, server, io };
