# UMT Belongings Hub - Deployment Guide

## Prerequisites
- Node.js (v14+)
- MongoDB (v4.4+)
- npm or yarn package manager
- TensorFlow.js dependencies

## Environment Setup

### Environment Variables
Create a `.env` file in the project root with the following variables:

```
PORT=3000
MONGODB_URI=mongodb://localhost:27017/umt_belongings_hub
JWT_SECRET=your_jwt_secret_key
NODE_ENV=production
```

### MongoDB Setup
1. Install MongoDB if not already installed
2. Create a database named `umt_belongings_hub`
3. Ensure MongoDB is running on the default port (27017)

## Installation Steps

### 1. Install Dependencies
```bash
npm install
```

### 2. Build Frontend Assets (if needed)
```bash
npm run build
```

### 3. Create Upload Directory
```bash
mkdir -p public/uploads
```

### 4. Start the Server
```bash
npm start
```

## Production Deployment

### Option 1: Traditional Server
1. Clone the repository to your server
2. Follow the installation steps above
3. Use a process manager like PM2:
   ```bash
   npm install -g pm2
   pm2 start server/index.js --name umt-belongings-hub
   ```
4. Set up a reverse proxy with Nginx or Apache

### Option 2: Docker Deployment
1. Build the Docker image:
   ```bash
   docker build -t umt-belongings-hub .
   ```
2. Run the container:
   ```bash
   docker run -p 3000:3000 -e MONGODB_URI=mongodb://mongo:27017/umt_belongings_hub -d umt-belongings-hub
   ```

### Option 3: Cloud Deployment
1. Deploy to Heroku:
   ```bash
   heroku create
   git push heroku main
   ```
2. Set environment variables in the Heroku dashboard

## Maintenance

### Database Backup
```bash
mongodump --db umt_belongings_hub --out /backup/path
```

### Restore Database
```bash
mongorestore --db umt_belongings_hub /backup/path/umt_belongings_hub
```

### Updating the Application
1. Pull the latest changes
2. Install any new dependencies
3. Restart the server

## Troubleshooting

### Common Issues
- **Connection refused**: Check if MongoDB is running
- **Authentication failed**: Verify JWT_SECRET is set correctly
- **Image upload fails**: Check if uploads directory exists and has proper permissions
- **TensorFlow model not loading**: Ensure internet connection is available for model download

### Logs
- Application logs are stored in `logs/app.log`
- Access logs are stored in `logs/access.log`

## Security Considerations
- Keep JWT_SECRET secure and unique
- Regularly update dependencies
- Implement rate limiting for API endpoints
- Use HTTPS in production
- Validate all user inputs
