// Error handling middleware
const errorHandler = (err, req, res, next) => {
  console.error(err.stack);
  
  // Multer file size error
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ 
      message: 'File too large. Maximum size is 5MB.' 
    });
  }
  
  // Multer file type error
  if (err.message === 'Only image files are allowed') {
    return res.status(400).json({ 
      message: 'Only image files are allowed.' 
    });
  }
  
  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    return res.status(401).json({ 
      message: 'Invalid token. Please log in again.' 
    });
  }
  
  if (err.name === 'TokenExpiredError') {
    return res.status(401).json({ 
      message: 'Token expired. Please log in again.' 
    });
  }
  
  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const messages = Object.values(err.errors).map(val => val.message);
    return res.status(400).json({ 
      message: messages.join(', ') 
    });
  }
  
  // Mongoose duplicate key error
  if (err.code === 11000) {
    return res.status(400).json({ 
      message: 'Duplicate field value entered.' 
    });
  }
  
  // Default server error
  res.status(500).json({
    message: 'Server error. Please try again later.'
  });
};

module.exports = errorHandler;
