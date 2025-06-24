const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');
const Post = require('../models/post');
const User = require('../models/user');
const { authMiddleware } = require('../middleware/auth');
const sharp = require('sharp');
const tf = require('@tensorflow/tfjs-node');

// Helper function to extract image features using MobileNet
async function extractImageFeatures(imagePath, mobilenet) {
  try {
    // Read and resize image
    const imageBuffer = await sharp(imagePath)
      .resize(224, 224)
      .toBuffer();
    
    // Convert to tensor
    const imageTensor = tf.node.decodeImage(imageBuffer, 3);
    
    // Normalize and expand dimensions
    const normalized = imageTensor.div(255).expandDims();
    
    // Get features from MobileNet's second-to-last layer
    const features = mobilenet.predict(normalized);
    
    // Convert to array and return
    const featuresArray = await features.data();
    
    // Clean up tensors
    tf.dispose([imageTensor, normalized, features]);
    
    return Array.from(featuresArray);
  } catch (error) {
    console.error('Error extracting image features:', error);
    return null;
  }
}

// Get lost items with pagination and filters
router.get('/lost', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;
    
    const category = req.query.category;
    const search = req.query.search;
    
    // Build query
    const query = { type: 'LOST', status: 'ACTIVE' };
    
    if (category && category !== 'ALL') {
      query.category = category;
    }
    
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
        { location: { $regex: search, $options: 'i' } }
      ];
    }
    
    // Execute query
    const items = await Post.find(query)
      .sort({ date: -1 })
      .skip(skip)
      .limit(limit)
      .populate('user', 'firstName lastName');
    
    res.json(items);
  } catch (error) {
    next(error);
  }
});

// Get found items with pagination and filters
router.get('/found', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;
    
    const category = req.query.category;
    const search = req.query.search;
    
    // Build query
    const query = { type: 'FOUND', status: 'ACTIVE' };
    
    if (category && category !== 'ALL') {
      query.category = category;
    }
    
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
        { location: { $regex: search, $options: 'i' } }
      ];
    }
    
    // Execute query
    const items = await Post.find(query)
      .sort({ date: -1 })
      .skip(skip)
      .limit(limit)
      .populate('user', 'firstName lastName');
    
    res.json(items);
  } catch (error) {
    next(error);
  }
});

// Get single post details
router.get('/:id', async (req, res, next) => {
  try {
    const post = await Post.findById(req.params.id)
      .populate('user', 'firstName lastName email');
    
    if (!post) {
      return res.status(404).json({ message: 'Post not found' });
    }
    
    res.json(post);
  } catch (error) {
    next(error);
  }
});

// Create new post (lost or found)
router.post('/', authMiddleware, async (req, res, next) => {
  try {
    // Handle file upload
    req.upload.array('images', 3)(req, res, async (err) => {
      if (err) {
        return next(err);
      }
      
      try {
        const { title, type, category, location, date, description } = req.body;
        
        // Create post
        const post = new Post({
          title,
          type,
          category,
          location,
          date: date || Date.now(),
          description,
          user: req.userId,
          images: []
        });
        
        // Process uploaded images
        if (req.files && req.files.length > 0) {
          // Save image paths
          post.images = req.files.map(file => `/uploads/${file.filename}`);
          
          // Extract features from first image if MobileNet is loaded
          if (req.mobilenet) {
            const imagePath = path.join(__dirname, '../../public', post.images[0]);
            const features = await extractImageFeatures(imagePath, req.mobilenet);
            if (features) {
              post.imageFeatures = features;
            }
          }
        }
        
        await post.save();
        
        // If this is a lost item, find similar found items
        if (type === 'LOST' && post.imageFeatures && post.imageFeatures.length > 0) {
          const similarItems = await Post.findSimilarItems(post.imageFeatures, 0.7, 3);
          
          // If similar items found, notify user
          if (similarItems.length > 0) {
            await User.findByIdAndUpdate(req.userId, {
              $push: {
                notifications: {
                  message: `We found ${similarItems.length} item(s) that might match your lost item!`,
                  type: 'MATCH',
                  link: `/dashboard?tab=matches&post=${post._id}`
                }
              }
            });
            
            // Notify via socket if available
            if (req.io) {
              req.io.to(`user:${req.userId}`).emit('notification:new');
            }
          }
        }
        
        res.status(201).json(post);
      } catch (error) {
        next(error);
      }
    });
  } catch (error) {
    next(error);
  }
});

// Update post
router.patch('/:id', authMiddleware, async (req, res, next) => {
  try {
    const post = await Post.findById(req.params.id);
    
    if (!post) {
      return res.status(404).json({ message: 'Post not found' });
    }
    
    // Check ownership
    if (post.user.toString() !== req.userId && req.user.role !== 'ADMIN') {
      return res.status(403).json({ message: 'Not authorized to update this post' });
    }
    
    // Update fields
    const { title, category, location, description, status } = req.body;
    
    if (title) post.title = title;
    if (category) post.category = category;
    if (location) post.location = location;
    if (description) post.description = description;
    if (status && req.user.role === 'ADMIN') post.status = status;
    
    await post.save();
    
    res.json(post);
  } catch (error) {
    next(error);
  }
});

// Delete post
router.delete('/:id', authMiddleware, async (req, res, next) => {
  try {
    const post = await Post.findById(req.params.id);
    
    if (!post) {
      return res.status(404).json({ message: 'Post not found' });
    }
    
    // Check ownership
    if (post.user.toString() !== req.userId && req.user.role !== 'ADMIN') {
      return res.status(403).json({ message: 'Not authorized to delete this post' });
    }
    
    // Delete images
    if (post.images && post.images.length > 0) {
      post.images.forEach(imagePath => {
        const fullPath = path.join(__dirname, '../../public', imagePath);
        if (fs.existsSync(fullPath)) {
          fs.unlinkSync(fullPath);
        }
      });
    }
    
    await post.remove();
    
    res.json({ message: 'Post deleted successfully' });
  } catch (error) {
    next(error);
  }
});

// Find similar items based on image
router.post('/find-similar', authMiddleware, async (req, res, next) => {
  try {
    // Handle file upload
    req.upload.single('image')(req, res, async (err) => {
      if (err) {
        return next(err);
      }
      
      try {
        if (!req.file) {
          return res.status(400).json({ message: 'No image uploaded' });
        }
        
        if (!req.mobilenet) {
          return res.status(500).json({ message: 'Image similarity service not available' });
        }
        
        // Extract features from uploaded image
        const imagePath = path.join(__dirname, '../../public/uploads', req.file.filename);
        const features = await extractImageFeatures(imagePath, req.mobilenet);
        
        if (!features) {
          return res.status(500).json({ message: 'Failed to extract image features' });
        }
        
        // Find similar items
        const type = req.query.type || 'FOUND'; // Default to finding similar found items
        const similarItems = await Post.findSimilarItems(features, 0.7, 5);
        
        // Delete the temporary uploaded file
        fs.unlinkSync(imagePath);
        
        res.json(similarItems);
      } catch (error) {
        next(error);
      }
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
