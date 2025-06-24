const mongoose = require('mongoose');

const PostSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['LOST', 'FOUND'],
    required: true
  },
  description: String,
  category: {
    type: String,
    enum: ['ID_CARD', 'ELECTRONICS', 'STATIONERY', 'CLOTHING', 'BAGS', 'WATER_BOTTLES', 'OTHER']
  },
  location: String,
  date: {
    type: Date,
    default: Date.now
  },
  images: [String],
  imageFeatures: [Number], // For AI image similarity
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  status: {
    type: String,
    enum: ['ACTIVE', 'CLAIMED', 'ARCHIVED'],
    default: 'ACTIVE'
  }
});

// Method to find similar items based on image features
PostSchema.statics.findSimilarItems = async function(imageFeatures, threshold = 0.8, limit = 5) {
  if (!imageFeatures || imageFeatures.length === 0) {
    return [];
  }
  
  // Find posts with image features
  const posts = await this.find({
    imageFeatures: { $exists: true, $ne: [] }
  }).populate('user', 'firstName lastName email');
  
  // Calculate cosine similarity
  const similarities = posts.map(post => {
    // Use the first image features for comparison
    const postFeatures = post.imageFeatures;
    if (!postFeatures || postFeatures.length === 0) {
      return { post, similarity: 0 };
    }
    
    // Calculate dot product
    let dotProduct = 0;
    let magnitude1 = 0;
    let magnitude2 = 0;
    
    for (let i = 0; i < Math.min(imageFeatures.length, postFeatures.length); i++) {
      dotProduct += imageFeatures[i] * postFeatures[i];
      magnitude1 += imageFeatures[i] * imageFeatures[i];
      magnitude2 += postFeatures[i] * postFeatures[i];
    }
    
    magnitude1 = Math.sqrt(magnitude1);
    magnitude2 = Math.sqrt(magnitude2);
    
    const similarity = dotProduct / (magnitude1 * magnitude2);
    
    return { post, similarity };
  });
  
  // Filter by threshold and sort by similarity
  return similarities
    .filter(item => item.similarity >= threshold)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit)
    .map(item => ({
      ...item.post.toObject(),
      similarity: item.similarity
    }));
};

module.exports = mongoose.model('Post', PostSchema);
