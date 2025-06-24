const mongoose = require('mongoose');

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

module.exports = mongoose.model('Claim', ClaimSchema);
