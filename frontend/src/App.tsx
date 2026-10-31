import React, { useState } from 'react';
import { AuthProvider, useAuth } from './store/AuthContext';
import { FacultyDashboard } from './pages/FacultyDashboard';
import { StudentPortal } from './pages/StudentPortal';
import { AdminDashboard } from './pages/AdminDashboard';
import { RealTimeClassroomDemo } from './pages/RealTimeClassroomDemo';
import { PortalView } from './components/common/Header';

const MainContent: React.FC = () => {
  const { isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<PortalView>('demo');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
      </div>
    );
  }

  if (currentView === 'demo') {
    return <RealTimeClassroomDemo currentView={currentView} onViewChange={setCurrentView} />;
  }
  if (currentView === 'student') {
    return <StudentPortal currentView={currentView} onViewChange={setCurrentView} />;
  }
  if (currentView === 'admin') {
    return <AdminDashboard currentView={currentView} onViewChange={setCurrentView} />;
  }
  return <FacultyDashboard currentView={currentView} onViewChange={setCurrentView} />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
};
