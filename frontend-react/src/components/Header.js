import React from 'react';
import { useStateContext } from '../context/StateContext';

const Header = () => {
  const { isConnected } = useStateContext();

  return (
    <header className="header">
      <h1>NEXUS FORGE</h1>
      <div className="tech-stack">
        <span className="tech-badge omi">
          <i className="fas fa-microphone"></i> OMI
        </span>
        <span className="tech-badge lyzr">
          <i className="fas fa-robot"></i> LYZR
        </span>
        <span className="tech-badge qdrant">
          <i className="fas fa-database"></i> QDRANT
        </span>
        <span className={`status-indicator ${isConnected ? '' : 'error'}`} title={isConnected ? 'Connected to Backend' : 'Disconnected'}>
        </span>
      </div>
    </header>
  );
};

export default Header;