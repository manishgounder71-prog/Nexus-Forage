import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import io from 'socket.io-client';
import './App.css';

// Components
import CommandCenter from './components/CommandCenter';
import LiveMission from './components/LiveMission';
import AIOOrganization from './components/AIOOrganization';
import AgentParliament from './components/AgentParliament';
import RedTeam from './components/RedTeam';
import SimulationEngine from './components/SimulationEngine';
import MemoryIntelligence from './components/MemoryIntelligence';
import ConnectorCenter from './components/ConnectorCenter';
import Header from './components/Header';
import Sidebar from './components/Sidebar';

// Context for global state (like socket, user, etc.)
import { StateContext } from './context/StateContext';

function App() {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to backend WebSocket
    const socketInstance = io(process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000');
    setSocket(socketInstance);

    socketInstance.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to backend');
    });

    socketInstance.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from backend');
    });

    // Cleanup on unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return (
    <StateContext.Provider value={{ socket, isConnected }}>
      <Router>
        <div className="app">
          <Sidebar />
          <div className="main-content">
            <Header />
            <div className="content">
              <Routes>
                <Route path="/" element={<Navigate replace to="/command-center" />} />
                <Route path="/command-center" element={<CommandCenter />} />
                <Route path="/live-mission" element={<LiveMission />} />
                <Route path="/ai-organization" element={<AIOOrganization />} />
                <Route path="/agent-parliament" element={<AgentParliament />} />
                <Route path="/red-team" element={<RedTeam />} />
                <Route path="/simulation" element={<SimulationEngine />} />
                <Route path="/memory" element={<MemoryIntelligence />} />
                <Route path="/connectors" element={<ConnectorCenter />} />
                <Route path="*" element={<Navigate replace to="/command-center" />} />
              </Routes>
            </div>
          </div>
        </div>
      </Router>
    </StateContext.Provider>
  );
}

export default App;