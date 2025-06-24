const express = require('express');
const router = express.Router();
const User = require('../models/user');
const Post = require('../models/post');
const Claim = require('../models/claim');
const { adminMiddleware } = require('../middleware/auth');

// Admin middleware applied to all routes
router.use(adminMiddleware);

// Get all posts
router.get('/posts', async (req, res, next) => {
  try {
    const type = req.query.type || 'ALL';
    const status = req.query.status || 'ACTIVE';
    const search = req.query.search || '';
    
    // Build query
    const query = {};
    
    if (type !== 'ALL') {
      query.type = type;
    }
    
    if (status !== 'ALL') {
      query.status = status;
    }
    
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
        { location: { $regex: search, $options: 'i' } }
      ];
    }
    
    const posts = await Post.find(query)
      .populate('user', 'firstName lastName email')
      .sort({ date: -1 });
    
    res.json(posts);
  } catch (error) {
    next(error);
  }
});

// Archive post
router.patch('/posts/:id/archive', async (req, res, next) => {
  try {
    const post = await Post.findById(req.params.id);
    
    if (!post) {
      return res.status(404).json({ message: 'Post not found' });
    }
    
    post.status = 'ARCHIVED';
    await post.save();
    
    // Notify post owner
    const postOwner = await User.findById(post.user);
    if (postOwner) {
      await postOwner.addNotification(
        `Your post "${post.title}" has been archived by an admin`,
        'SYSTEM',
        `/dashboard?tab=posts`
      );
      
      // Send real-time notification if socket is available
      if (req.io) {
        req.io.to(`user:${post.user}`).emit('notification:new');
      }
    }
    
    res.json(post);
  } catch (error) {
    next(error);
  }
});

// Get all claims
router.get('/claims', async (req, res, next) => {
  try {
    const status = req.query.status || 'PENDING';
    
    const query = {};
    if (status !== 'ALL') {
      query.status = status;
    }
    
    const claims = await Claim.find(query)
      .populate({
        path: 'post',
        populate: { path: 'user', select: 'firstName lastName email' }
      })
      .populate('claimant', 'firstName lastName email')
      .sort({ date: -1 });
    
    res.json(claims);
  } catch (error) {
    next(error);
  }
});

// Update claim status
router.patch('/claims/:id', async (req, res, next) => {
  try {
    const { status } = req.body;
    
    if (!['APPROVED', 'REJECTED'].includes(status)) {
      return res.status(400).json({ message: 'Invalid status' });
    }
    
    const claim = await Claim.findById(req.params.id);
    if (!claim) {
      return res.status(404).json({ message: 'Claim not found' });
    }
    
    // Update claim status
    claim.status = status;
    await claim.save();
    
    // If approved, update post status
    if (status === 'APPROVED') {
      const post = await Post.findById(claim.post);
      if (post) {
        post.status = 'CLAIMED';
        await post.save();
      }
    }
    
    // Notify claimant
    const claimant = await User.findById(claim.claimant);
    if (claimant) {
      const post = await Post.findById(claim.post);
      await claimant.addNotification(
        `Your claim for "${post ? post.title : 'an item'}" has been ${status === 'APPROVED' ? 'approved' : 'rejected'} by an admin`,
        'CLAIM',
        `/dashboard?tab=claims&claim=${claim._id}`
      );
      
      // Send real-time notification if socket is available
      if (req.io) {
        req.io.to(`user:${claim.claimant}`).emit('notification:new');
      }
    }
    
    // Notify post owner
    const post = await Post.findById(claim.post);
    if (post && post.user) {
      const postOwner = await User.findById(post.user);
      if (postOwner) {
        await postOwner.addNotification(
          `A claim for your item "${post.title}" has been ${status === 'APPROVED' ? 'approved' : 'rejected'} by an admin`,
          'CLAIM',
          `/dashboard?tab=claims`
        );
        
        // Send real-time notification if socket is available
        if (req.io) {
          req.io.to(`user:${post.user}`).emit('notification:new');
        }
      }
    }
    
    res.json(claim);
  } catch (error) {
    next(error);
  }
});

// Get all users
router.get('/users', async (req, res, next) => {
  try {
    const search = req.query.search || '';
    
    const query = {};
    if (search) {
      query.$or = [
        { firstName: { $regex: search, $options: 'i' } },
        { lastName: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } }
      ];
    }
    
    const users = await User.find(query)
      .select('-password -notifications')
      .sort({ createdAt: -1 });
    
    res.json(users);
  } catch (error) {
    next(error);
  }
});

// Update user role
router.patch('/users/:id', async (req, res, next) => {
  try {
    const { role } = req.body;
    
    if (!['STUDENT', 'ADMIN'].includes(role)) {
      return res.status(400).json({ message: 'Invalid role' });
    }
    
    const user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    // Prevent changing own role
    if (user._id.toString() === req.userId) {
      return res.status(400).json({ message: 'Cannot change your own role' });
    }
    
    user.role = role;
    await user.save();
    
    // Notify user
    await user.addNotification(
      `Your account role has been updated to ${role}`,
      'SYSTEM',
      '/dashboard'
    );
    
    // Send real-time notification if socket is available
    if (req.io) {
      req.io.to(`user:${user._id}`).emit('notification:new');
    }
    
    res.json({
      _id: user._id,
      firstName: user.firstName,
      lastName: user.lastName,
      email: user.email,
      role: user.role
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
