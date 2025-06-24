const express = require('express');
const router = express.Router();
const Claim = require('../models/claim');
const Post = require('../models/post');
const User = require('../models/user');
const Chat = require('../models/chat');
const path = require('path');
const fs = require('fs');

// Create new claim
router.post('/', async (req, res, next) => {
  try {
    const { postId, description } = req.body;
    
    // Find post
    const post = await Post.findById(postId);
    if (!post) {
      return res.status(404).json({ message: 'Post not found' });
    }
    
    // Check if post is already claimed
    if (post.status !== 'ACTIVE') {
      return res.status(400).json({ message: 'This item is no longer available' });
    }
    
    // Check if user already has a pending claim for this post
    const existingClaim = await Claim.findOne({
      post: postId,
      claimant: req.userId,
      status: 'PENDING'
    });
    
    if (existingClaim) {
      return res.status(400).json({ message: 'You already have a pending claim for this item' });
    }
    
    // Handle file upload for proof images
    req.upload.array('proofImages', 2)(req, res, async (err) => {
      if (err) {
        return next(err);
      }
      
      try {
        // Create claim
        const claim = new Claim({
          post: postId,
          claimant: req.userId,
          description,
          proofImages: req.files ? req.files.map(file => `/uploads/${file.filename}`) : []
        });
        
        await claim.save();
        
        // Create chat for communication
        const chat = new Chat({
          claim: claim._id,
          participants: [req.userId, post.user],
          messages: []
        });
        
        await chat.save();
        
        // Notify post owner
        const postOwner = await User.findById(post.user);
        if (postOwner) {
          await postOwner.addNotification(
            `Someone has claimed your ${post.type === 'FOUND' ? 'found' : 'lost'} item: ${post.title}`,
            'CLAIM',
            `/dashboard?tab=claims&claim=${claim._id}`
          );
          
          // Send real-time notification if socket is available
          if (req.io) {
            req.io.to(`user:${post.user}`).emit('notification:new');
          }
        }
        
        res.status(201).json({
          claim,
          chatId: chat._id
        });
      } catch (error) {
        next(error);
      }
    });
  } catch (error) {
    next(error);
  }
});

// Get user's claims
router.get('/user', async (req, res, next) => {
  try {
    const claims = await Claim.find({ claimant: req.userId })
      .populate({
        path: 'post',
        populate: { path: 'user', select: 'firstName lastName' }
      })
      .sort({ date: -1 });
    
    res.json(claims);
  } catch (error) {
    next(error);
  }
});

// Get claims for user's posts
router.get('/received', async (req, res, next) => {
  try {
    // Find user's posts
    const userPosts = await Post.find({ user: req.userId });
    const postIds = userPosts.map(post => post._id);
    
    // Find claims for those posts
    const claims = await Claim.find({ post: { $in: postIds } })
      .populate('post')
      .populate('claimant', 'firstName lastName email')
      .sort({ date: -1 });
    
    res.json(claims);
  } catch (error) {
    next(error);
  }
});

// Get claim details
router.get('/:id', async (req, res, next) => {
  try {
    const claim = await Claim.findById(req.params.id)
      .populate('post')
      .populate('claimant', 'firstName lastName email');
    
    if (!claim) {
      return res.status(404).json({ message: 'Claim not found' });
    }
    
    // Check if user is authorized to view this claim
    const post = await Post.findById(claim.post);
    if (claim.claimant.toString() !== req.userId && post.user.toString() !== req.userId && req.user.role !== 'ADMIN') {
      return res.status(403).json({ message: 'Not authorized to view this claim' });
    }
    
    res.json(claim);
  } catch (error) {
    next(error);
  }
});

// Update claim status (for post owner)
router.patch('/:id', async (req, res, next) => {
  try {
    const { status } = req.body;
    
    if (!['APPROVED', 'REJECTED'].includes(status)) {
      return res.status(400).json({ message: 'Invalid status' });
    }
    
    const claim = await Claim.findById(req.params.id);
    if (!claim) {
      return res.status(404).json({ message: 'Claim not found' });
    }
    
    // Find post to check ownership
    const post = await Post.findById(claim.post);
    if (!post) {
      return res.status(404).json({ message: 'Associated post not found' });
    }
    
    // Check if user is post owner or admin
    if (post.user.toString() !== req.userId && req.user.role !== 'ADMIN') {
      return res.status(403).json({ message: 'Not authorized to update this claim' });
    }
    
    // Update claim status
    claim.status = status;
    await claim.save();
    
    // If approved, update post status
    if (status === 'APPROVED') {
      post.status = 'CLAIMED';
      await post.save();
    }
    
    // Notify claimant
    const claimant = await User.findById(claim.claimant);
    if (claimant) {
      await claimant.addNotification(
        `Your claim for "${post.title}" has been ${status === 'APPROVED' ? 'approved' : 'rejected'}`,
        'CLAIM',
        `/dashboard?tab=claims&claim=${claim._id}`
      );
      
      // Send real-time notification if socket is available
      if (req.io) {
        req.io.to(`user:${claim.claimant}`).emit('notification:new');
      }
    }
    
    res.json(claim);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
