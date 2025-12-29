import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { HomePage } from './components/HomePage';
import { ModelStats } from './components/ModelStats';
import { Reports } from './components/Reports';
import { CallLogs } from './components/CallLogs';
import { FraudDetection } from './components/FraudDetection';

export default function App() {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <BrowserRouter>
      <div className={isDark ? 'dark' : ''}>
        <div className="flex min-h-screen bg-background text-foreground">
          <Sidebar
            isDark={isDark}
            toggleTheme={toggleTheme}
          />
          <main className="flex-1 transition-all duration-300">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/call-logs" element={<CallLogs />} />
              <Route path="/fraud-detection" element={<FraudDetection />} />
              {/* Redirect any unknown routes to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
