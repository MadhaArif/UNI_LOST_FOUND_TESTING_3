const express = require('express');
const router = express.Router();
const Chat = require('../models/chat');
const Claim = require('../models/claim');
const User = require('../models/user');

// Get user's chats
router.get('/', async (req, res, next) => {
  try {
    // Find chats where user is a participant
    const chats = await Chat.find({ participants: req.userId })
      .populate({
        path: 'claim',
        populate: [
          { path: 'post', select: 'title type images' },
          { path: 'claimant', select: 'firstName lastName' }
        ]
      })
      .sort({ lastActivity: -1 });
    
    // Format response
    const formattedChats = chats.map(chat => {
      const otherParticipantId = chat.participants.find(
        p => p.toString() !== req.userId
      );
      
      // Count unread messages
      const unreadCount = chat.messages.filter(
        msg => msg.sender.toString() !== req.userId && !msg.read
      ).length;
      
      return {
        _id: chat._id,
        claim: chat.claim,
        lastActivity: chat.lastActivity,
        unreadCount,
        otherParticipantId
      };
    });
    
    res.json(formattedChats);
  } catch (error) {
    next(error);
  }
});

// Get chat messages
router.get('/:id', async (req, res, next) => {
  try {
    const chat = await Chat.findById(req.params.id)
      .populate({
        path: 'claim',
        populate: [
          { path: 'post', select: 'title type images' },
          { path: 'claimant', select: 'firstName lastName' }
        ]
      })
      .populate('participants', 'firstName lastName');
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Check if user is a participant
    if (!chat.participants.some(p => p._id.toString() === req.userId)) {
      return res.status(403).json({ message: 'Not authorized to access this chat' });
    }
    
    // Mark messages as read
    chat.messages.forEach(message => {
      if (message.sender.toString() !== req.userId && !message.read) {
        message.read = true;
      }
    });
    
    await chat.save();
    
    // Get sender info for each message
    const populatedMessages = await Promise.all(chat.messages.map(async (message) => {
      const sender = await User.findById(message.sender).select('firstName lastName');
      return {
        _id: message._id,
        content: message.content,
        timestamp: message.timestamp,
        read: message.read,
        sender: {
          _id: sender._id,
          name: `${sender.firstName} ${sender.lastName}`
        }
      };
    }));
    
    res.json({
      _id: chat._id,
      claim: chat.claim,
      participants: chat.participants,
      messages: populatedMessages,
      lastActivity: chat.lastActivity
    });
  } catch (error) {
    next(error);
  }
});

// Send new message
router.post('/:id/messages', async (req, res, next) => {
  try {
    const { content } = req.body;
    
    if (!content || content.trim() === '') {
      return res.status(400).json({ message: 'Message content is required' });
    }
    
    const chat = await Chat.findById(req.params.id);
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Check if user is a participant
    if (!chat.participants.some(p => p.toString() === req.userId)) {
      return res.status(403).json({ message: 'Not authorized to send messages in this chat' });
    }
    
    // Add message
    const message = {
      sender: req.userId,
      content,
      timestamp: Date.now(),
      read: false
    };
    
    chat.messages.push(message);
    chat.lastActivity = Date.now();
    
    await chat.save();
    
    // Get sender info
    const sender = await User.findById(req.userId).select('firstName lastName');
    
    const messageData = {
      _id: chat.messages[chat.messages.length - 1]._id,
      sender: {
        _id: sender._id,
        name: `${sender.firstName} ${sender.lastName}`
      },
      content,
      timestamp: Date.now(),
      read: false
    };
    
    // Send real-time notification to other participants
    if (req.io) {
      // Emit to chat room
      req.io.to(`chat:${chat._id}`).emit('message:received', messageData);
      
      // Send notifications to other participants
      chat.participants.forEach(async (participantId) => {
        if (participantId.toString() !== req.userId) {
          const participant = await User.findById(participantId);
          if (participant) {
            await participant.addNotification(
              `New message from ${sender.firstName} ${sender.lastName}`,
              'CHAT',
              `/dashboard?tab=chats&chat=${chat._id}`
            );
            req.io.to(`user:${participantId}`).emit('notification:new');
          }
        }
      });
    }
    
    res.status(201).json(messageData);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
