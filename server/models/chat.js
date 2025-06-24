const mongoose = require('mongoose');
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

module.exports = mongoose.model('Chat', ChatSchema);
