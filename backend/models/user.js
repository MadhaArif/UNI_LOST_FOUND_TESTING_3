const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

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
      enum: ['CLAIM', 'MATCH', 'SYSTEM', 'CHAT']
    }
  }]
});

// Hash password before saving
UserSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

// Compare password method
UserSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Get user's full name
UserSchema.virtual('name').get(function() {
  return `${this.firstName} ${this.lastName}`;
});

// Get unread notification count
UserSchema.methods.getUnreadNotificationCount = function() {
  return this.notifications.filter(notification => !notification.read).length;
};

// Add notification
UserSchema.methods.addNotification = function(message, type, link = '') {
  this.notifications.unshift({
    message,
    type,
    link,
    read: false,
    date: Date.now()
  });
  return this.save();
};

module.exports = mongoose.model('User', UserSchema);
