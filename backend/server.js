const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["GET", "POST"]
  }
});

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true, limit: '10kb' }));
app.use(limiter);

// Routes
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Authentication routes
app.use('/api/auth', require('./routes/authRoutes'));

// Enterprise API routes
app.use('/api/missions', require('./routes/missionRoutes'));
app.use('/api/analytics', require('./routes/analyticsRoutes'));
app.use('/api/connectors', require('./routes/connectorRoutes'));

// WebSocket connection
io.on('connection', (socket) => {
  console.log('New client connected:', socket.id);

  // Join a room for mission updates
  socket.on('join-mission', (missionId) => {
    socket.join(missionId);
    console.log(`Socket ${socket.id} joined mission ${missionId}`);

    // Send confirmation
    socket.emit('mission-joined', { missionId, status: 'joined' });
  });

  // Leave mission room
  socket.on('leave-mission', (missionId) => {
    socket.leave(missionId);
    console.log(`Socket ${socket.id} left mission ${missionId}`);
  });

  // Request metrics data
  socket.on('request-metrics', () => {
    // Simulate sending metrics data
    const metricsData = {
      activeAgents: Math.floor(Math.random() * 10) + 5,
      memorySearchSpeed: (Math.random() * 2 + 0.5).toFixed(1),
      consensusLevel: Math.floor(Math.random() * 10) + 90,
      processingSpeed: Math.floor(Math.random() * 100) + 200
    };

    socket.emit('metrics-update', metricsData);
  });

  // Request agent activity
  socket.on('request-agent-activity', () => {
    const agents = [
      { agent: 'Grid Specialist', status: 'active', task: 'Analyzing substation 04' },
      { agent: 'Supply Chain Lead', status: 'busy', task: 'Coordinating with vendors' },
      { agent: 'Higher-Ed Analyst', status: 'idle', task: 'Monitoring exam portals' },
      { agent: 'Security Auditor', status: 'active', task: 'Scanning for intrusions' },
      { agent: 'Logistics Officer', status: 'active', task: 'Routing emergency supplies' },
      { agent: 'Comms Director', status: 'idle', task: 'Preparing public statements' }
    ];

    socket.emit('agent-activity', agents);
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Start server
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = { app, server, io };