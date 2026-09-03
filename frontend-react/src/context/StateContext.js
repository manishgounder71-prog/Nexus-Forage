import React, { createContext, useContext } from 'react';

const StateContext = createContext();

export const StateProvider = ({ children, value }) => {
  return <StateContext.Provider value={value}>{children}</StateContext.Provider>;
};

export const useStateContext = () => {
  const context = useContext(StateContext);
  if (!context) {
    throw new Error('useStateContext must be used within a StateProvider');
  }
  return context;
};

export default StateContext;