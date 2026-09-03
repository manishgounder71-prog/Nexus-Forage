import React, { useState, useEffect } from 'react';
import { useStateContext } from '../context/StateContext';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const CommandCenter = () => {
  const { socket, isConnected } = useStateContext();
  const [metrics, setMetrics] = useState({
    activeAgents: 0,
    memorySearchSpeed: 0,
    consensusLevel: 0,
    processingSpeed: 0,
  });
  const [agentActivity, setAgentActivity] = useState([]);

  useEffect(() => {
    if (!socket) return;

    // Listen for metrics updates from backend
    socket.on('metrics-update', (data) => {
      setMetrics(data);
    });

    // Listen for agent activity
    socket.on('agent-activity', (data) => {
      setAgentActivity(data);
    });

    // Request initial data
    socket.emit('request-initial-data');

    return () => {
      socket.off('metrics-update');
      socket.off('agent-activity');
    };
  }, [socket]);

  // Mock data if not connected
  useEffect(() => {
    if (!isConnected) {
      setMetrics({
        activeAgents: 6,
        memorySearchSpeed: 1.4,
        consensusLevel: 94.8,
        processingSpeed: 284,
      });
      setAgentActivity([
        { agent: 'Grid Specialist', status: 'active', task: 'Analyzing substation 04' },
        { agent: 'Supply Chain Lead', status: 'busy', task: 'Coordinating with vendors' },
        { agent: 'Higher-Ed Analyst', status: 'idle', task: 'Monitoring exam portals' },
        { agent: 'Security Auditor', status: 'active', task: 'Scanning for intrusions' },
        { agent: 'Logistics Officer', status: 'active', task: 'Routing emergency supplies' },
        { agent: 'Comms Director', status: 'idle', task: 'Preparing public statements' },
      ]);
    }
  }, [isConnected]);

  return (
    <div className="view-container">
      <div className="grid">
        {/* Metrics Cards */}
        <div className="card">
          <h3><i className="fas fa-users"></i> Active AI Agents</h3>
          <div className="metric-value">{metrics.activeAgents}</div>
          <div className="metric-label">AI Team Working in Parallel</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-search"></i> Memory Search Speed</h3>
          <div className="metric-value">{metrics.memorySearchSpeed}ms</div>
          <div className="metric-label">Smart Search Database</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-handshake"></i> Team Agreement Level</h3>
          <div className="metric-value">{metrics.consensusLevel}%</div>
          <div className="metric-progress">
            <div className="progress-bar" style={{ width: `${metrics.consensusLevel}%` }}></div>
          </div>
          <div className="metric-label">Consensus Across Agents</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-tachometer-alt"></i> AI Processing Speed</h3>
          <div className="metric-value">{metrics.processingSpeed} t/s</div>
          <div className="metric-label">All Agents Running Simultaneously</div>
        </div>
      </div>

      {/* Agent Activity and Chart */}
      <div className="grid">
        <div className="card">
          <h3><i className="fas fa-robot"></i> Agent Activity</h3>
          <div className="agent-list">
            {agentActivity.map((agent, index) => (
              <div key={index} className="agent-item">
                <span className="agent-name">{agent.agent}</span>
                <span className={`agent-status ${agent.status.toLowerCase()}`}></span>
                <span className="agent-task">{agent.task}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3><i className="fas fa-chart-area"></i> Mission Timeline</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { name: 'Detection', detection: 45, response: 30, recovery: 25 },
                { name: 'Analysis', detection: 30, response: 50, recovery: 20 },
                { name: 'Response', detection: 20, response: 60, recovery: 20 },
                { name: 'Recovery', detection: 10, response: 20, recovery: 70 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="detection" label="Detection" fillColor="#ec4899" />
                <Bar dataKey="response" label="Response" fillColor="#6366f1" />
                <Bar dataKey="recovery" label="Recovery" fillColor="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommandCenter;