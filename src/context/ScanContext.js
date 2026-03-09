import React, { createContext, useContext, useState } from 'react';

const ScanContext = createContext(null);

export function ScanProvider({ children }) {
  const [image, setImage] = useState(null);
  const [healthNote, setHealthNote] = useState('');
  const [result, setResult] = useState(null);
  const [stages, setStages] = useState([]);

  function updateStage(stageUpdate) {
    setStages(prev => {
      const idx = prev.findIndex(s => s.id === stageUpdate.id);
      if (idx !== -1) {
        const updated = [...prev];
        updated[idx] = { ...updated[idx], ...stageUpdate };
        return updated;
      }
      return [...prev, stageUpdate];
    });
  }

  return (
    <ScanContext.Provider
      value={{ image, setImage, healthNote, setHealthNote, result, setResult, stages, updateStage }}
    >
      {children}
    </ScanContext.Provider>
  );
}

export function useScan() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error('useScan must be used inside ScanProvider');
  return ctx;
}
