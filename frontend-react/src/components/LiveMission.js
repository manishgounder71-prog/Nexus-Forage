import React, { useState, useEffect } from 'react';
import { useStateContext } from '../context/StateContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const LiveMission = () => {
  const { socket, isConnected } = useStateContext();
  const [missionData, setMissionData] = useState({
    status: 'READY',
    breachTime: '00:00:00',
    threatLevel: 'LOW',
    affectedSystems: 0,
    responseActions: [],
  });
  const [threatTimeline, setThreatTimeline] = useState([]);

  useEffect(() => {
    if (!socket) return;

    // Listen for mission updates
    socket.on('mission-update', (data) => {
      setMissionData(data);
    });

    // Listen for threat timeline updates
    socket.on('threat-timeline', (data) => {
      setThreatTimeline(data);
    });

    return () => {
      socket.off('mission-update');
      socket.off('threat-timeline');
    };
  }, [socket]);

  // Mock data if not connected
  useEffect(() => {
    if (!isConnected) {
      setMissionData({
        status: 'ACTIVE',
        breachTime: '02:15:30',
        threatLevel: 'CRITICAL',
        affectedSystems: 12,
        responseActions: [
          { time: '00:05:00', action: 'Isolated substation 04', status: 'completed' },
          { time: '00:12:00', action: 'Deployed countermeasures', status: 'in-progress' },
          { time: '00:18:00', action: 'Notified emergency response', status: 'pending' },
        ],
      });
      setThreatTimeline([
        { time: '00:00:00', level: 1, label: 'Initial Detection' },
        { time: '00:05:00', level: 3, label: 'Threat Escalation' },
        { time: '00:12:00', level: 7, label: 'System Compromise' },
        { time: '00:18:00', level: 9, label: 'Peak Threat' },
        { time: '00:25:00', level: 6, label: 'Response Effective' },
        { time: '00:30:00', level: 3, label: 'Recovery Phase' },
      ]);
    }
  }, [isConnected]);

  const getThreatColor = (level) => {
    if (level >= 8) return '#ef4444'; // Red
    if (level >= 5) return '#f59e0b'; // Amber
    if (level >= 3) return '#fbbf24'; // Yellow
    return '#10b981'; // Green
  };

  return (
    <div className="view-container">
      <div className="grid">
        {/* Mission Status Cards */}
        <div className="card">
          <h3><i className="fas fa-exclamation-triangle"></i> Mission Status</h3>
          <div className="metric-value" style={{
            textTransform: 'uppercase',
            letterSpacing: '1px',
            fontWeight: 'bold',
            color: missionData.status === 'ACTIVE' ? '#ef4444' :
                      missionData.status === 'RESOLVED' ? '#10b981' : '#6366f1'
          }}>
            {missionData.status}
          </div>
          <div className="metric-label">Current Operational State</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-stopwatch"></i> Breach Duration</h3>
          <div className="metric-value" style={{ fontFamily: 'monospace' }}>
            {missionData.breachTime}
          </div>
          <div className="metric-label">Time Since Initial Detection</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-shield-alt"></i> Threat Level</h3>
          <div className="metric-value" style={{
            textTransform: 'uppercase',
            fontWeight: 'bold',
            color: getThreatColor(
              missionData.threatLevel === 'LOW' ? 1 :
                     missionData.threatLevel === 'MEDIUM' ? 5 :
                     missionData.threatLevel === 'HIGH' ? 8 : 10
            )
          }}>
            {missionData.threatLevel}
          </div>
          <div className="metric-label">Current Risk Assessment</div>
        </div>

        <div className="card">
          <h3><i className="fas fa-server"></i> Affected Systems</h3>
          <div className="metric-value">{missionData.affectedSystems}</div>
          <div className="metric-label">Infrastructure Components Impacted</div>
        </div>
      </div>

      {/* Threat Timeline and Response Actions */}
      <div className="grid">
        <div className="card">
          <h3><i className="fas fa-chart-line"></i> Threat Evolution Timeline</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={threatTimeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 10]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="level" stroke="#ef4444" strokeWidth={2}
                      dot={{ r: 4 }} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3><i className="fas fa-list-check"></i> Response Actions</h3>
          <div className="action-list">
            {missionData.responseActions.map((action, index) => (
              <div key={index} className="action-item">
                <div className="action-header">
                  <span className="action-time">{action.time}</span>
                  <span className={`action-status ${action.status.toLowerCase()}`}>
                    {action.status.toUpperCase()}
                  </span>
                </div>
                <div className="action-description">{action.action}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMission;