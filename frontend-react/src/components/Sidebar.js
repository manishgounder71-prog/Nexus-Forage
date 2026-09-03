import React from 'react';
import { useStateContext } from '../context/StateContext';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const { isConnected } = useStateContext();

  const navItems = [
    { icon: 'fas fa-compass', label: 'Command Center', path: '/command-center' },
    { icon: 'fas fa-diagram-project', label: 'Live Mission', path: '/live-mission' },
    { icon: 'fas fa-users-gear', label: 'AI Organization', path: '/ai-organization' },
    { icon: 'fas fa-gavel', label: 'Parliament', path: '/agent-parliament' },
    { icon: 'fas fa-shield-halved', label: 'Red Team', path: '/red-team' },
    { icon: 'fas fa-chart-network', label: 'Simulation', path: '/simulation' },
    { icon: 'fas fa-brain', label: 'Memory', path: '/memory' },
    { icon: 'fas fa-plug-circle-bolt', label: 'Connectors', path: '/connectors' },
  ];

  return (
    <aside className="sidebar">
      {navItems.map((item, index) => (
        <NavLink
          key={index}
          to={item.path}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <i className={item.icon}></i>
          <span>{item.label}</span>
        </NavLink>
      ))}
      <div className="footer">
        <p>System Status: <span className={isConnected ? 'status-indicator' : 'status-indicator error'}></span> {isConnected ? 'Online' : 'Offline'}</p>
        <p>NEXUS FORGE v1.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;