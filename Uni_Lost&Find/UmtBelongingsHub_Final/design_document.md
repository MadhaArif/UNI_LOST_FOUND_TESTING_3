# UMT Belongings Hub - Design Document

## 1. System Architecture

### 1.1 Overview
The UMT Belongings Hub will be implemented as a full-stack web application with:
- Frontend: HTML, CSS, JavaScript with Bootstrap for responsive design
- Backend: Node.js with Express.js
- Database: MongoDB with Mongoose ODM
- Real-time features: Socket.io for chat and notifications
- Image processing: TensorFlow.js for image similarity

### 1.2 Component Diagram
```
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  Client Browser   |<---->|  Express Server   |<---->|  MongoDB Database |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +-------------------+
         ^                         ^
         |                         |
         v                         v
+-------------------+      +-------------------+
|                   |      |                   |
|    Socket.io      |      |   Image AI        |
|    (Real-time)    |      |   (TensorFlow.js) |
|                   |      |                   |
+-------------------+      +-------------------+
```

## 2. Database Schema

### 2.1 User Model
```javascript
const UserSchema = new mongoose.Schema({
  firstName: {
    type: String,
    required: true
  },
  lastName: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    match: /.+@.+\.edu$/  // Ensure university email
  },
  password: {
    type: String,
    required: true
  },
  role: {
    type: String,
    enum: ['STUDENT', 'ADMIN'],
    default: 'STUDENT'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  notifications: [{
    message: String,
    read: {
      type: Boolean,
      default: false
    },
    date: {
      type: Date,
      default: Date.now
    },
    link: String,
    type: {
      type: String,
      enum: ['CLAIM', 'MATCH', 'SYSTEM']
    }
  }]
});
```

### 2.2 Post Model (Already Exists, Add Features)
```javascript
// Add these fields to existing Post model
imageFeatures: [Number], // For AI image similarity
```

### 2.3 Claim Model
```javascript
const ClaimSchema = new mongoose.Schema({
  post: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post',
    required: true
  },
  claimant: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  status: {
    type: String,
    enum: ['PENDING', 'APPROVED', 'REJECTED'],
    default: 'PENDING'
  },
  date: {
    type: Date,
    default: Date.now
  },
  description: String,
  proofImages: [String]
});
```

### 2.4 Chat Model
```javascript
const MessageSchema = new mongoose.Schema({
  sender: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  content: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  read: {
    type: Boolean,
    default: false
  }
});

const ChatSchema = new mongoose.Schema({
  claim: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Claim',
    required: true
  },
  participants: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  messages: [MessageSchema],
  lastActivity: {
    type: Date,
    default: Date.now
  }
});
```

## 3. API Endpoints

### 3.1 Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/forgot-password` - Request password reset

### 3.2 Posts
- `GET /api/posts/lost` - Get lost items with pagination and filters
- `GET /api/posts/found` - Get found items with pagination and filters
- `POST /api/posts` - Create new post (lost or found)
- `GET /api/posts/:id` - Get single post details
- `PATCH /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post

### 3.3 Claims
- `POST /api/claims` - Create new claim
- `GET /api/claims/user` - Get user's claims
- `GET /api/claims/:id` - Get claim details
- `PATCH /api/claims/:id` - Update claim status

### 3.4 Chat
- `GET /api/chats` - Get user's chats
- `GET /api/chats/:id` - Get chat messages
- `POST /api/chats/:id/messages` - Send new message

### 3.5 Admin
- `GET /api/admin/posts` - Get all posts
- `PATCH /api/admin/posts/:id/archive` - Archive post
- `GET /api/admin/claims` - Get all claims
- `PATCH /api/admin/claims/:id` - Update claim status
- `GET /api/admin/users` - Get all users
- `PATCH /api/admin/users/:id` - Update user role

### 3.6 Notifications
- `GET /api/notifications` - Get user notifications
- `PATCH /api/notifications/:id/read` - Mark notification as read
- `DELETE /api/notifications/:id` - Delete notification

## 4. Real-time Features

### 4.1 Socket.io Events
- `connection` - User connects
- `disconnect` - User disconnects
- `join:chat` - Join chat room
- `leave:chat` - Leave chat room
- `message:send` - Send message
- `message:received` - Receive message
- `notification:new` - New notification
- `notification:read` - Mark notification as read

### 4.2 Notification Types
- Claim requests
- Claim status updates
- New messages
- Similar item matches
- System announcements

## 5. Image Similarity AI

### 5.1 Implementation Approach
1. Use TensorFlow.js MobileNet model for feature extraction
2. Extract features from uploaded images
3. Store feature vectors in database
4. Compare vectors using cosine similarity
5. Recommend similar items based on threshold

### 5.2 Integration Points
- Image upload process
- Lost item search
- Periodic background matching

## 6. User Interface Enhancements

### 6.1 Real-time Chat Interface
- Chat sidebar in claim details
- Message input with attachment support
- Read receipts
- Typing indicators

### 6.2 Notification Center
- Dropdown notification panel
- Real-time counter updates
- Mark as read functionality
- Notification categories

### 6.3 Mobile Responsiveness
- Optimize all pages for mobile devices
- Touch-friendly interface elements
- Responsive image galleries
- Mobile-first navigation

## 7. Security Considerations

### 7.1 Authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Email verification
- Rate limiting for login attempts

### 7.2 Authorization
- Role-based access control
- Route protection middleware
- Secure API endpoints

### 7.3 Data Protection
- Input validation and sanitization
- XSS protection
- CSRF protection
- Secure file uploads

## 8. Implementation Plan

### 8.1 Phase 1: Core Backend
- Complete server setup
- Implement user model and authentication
- Set up database connection
- Implement basic API endpoints

### 8.2 Phase 2: Real-time Features
- Integrate Socket.io
- Implement chat functionality
- Build notification system

### 8.3 Phase 3: AI Integration
- Implement image feature extraction
- Build similarity comparison algorithm
- Integrate with post creation flow

### 8.4 Phase 4: UI Enhancements
- Implement chat interface
- Build notification center
- Optimize mobile responsiveness

### 8.5 Phase 5: Testing & Deployment
- Unit and integration testing
- Performance optimization
- Deployment preparation
