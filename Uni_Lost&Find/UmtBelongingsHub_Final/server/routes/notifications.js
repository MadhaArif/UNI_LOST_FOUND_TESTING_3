const express = require('express');
const router = express.Router();
const User = require('../models/user');

// Get user notifications
router.get('/', async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    res.json(user.notifications);
  } catch (error) {
    next(error);
  }
});

// Mark notification as read
router.patch('/:id/read', async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    const notification = user.notifications.id(req.params.id);
    if (!notification) {
      return res.status(404).json({ message: 'Notification not found' });
    }
    
    notification.read = true;
    await user.save();
    
    res.json(notification);
  } catch (error) {
    next(error);
  }
});

// Delete notification
router.delete('/:id', async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    user.notifications.pull(req.params.id);
    await user.save();
    
    res.json({ message: 'Notification deleted' });
  } catch (error) {
    next(error);
  }
});

// Mark all notifications as read
router.patch('/read-all', async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    user.notifications.forEach(notification => {
      notification.read = true;
    });
    
    await user.save();
    
    res.json({ message: 'All notifications marked as read' });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
