import React, { useState } from 'react';
import { useAuth } from '../store/AuthContext';
import { Header, PortalView } from '../components/common/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
  Building2,
  Video,
  Cpu,
  Server,
  Plus,
  Settings,
  Users,
  CheckCircle2,
  Activity,
  Layers,
  LogOut,
} from 'lucide-react';

const MOCK_CLASSROOMS = [
  { id: '1', name: 'Hall A-102', dept: 'Computer Science', camera: 'RTSP Cam 01 (192.168.1.101)', status: 'active', fps: 15 },
  { id: '2', name: 'Hall B-204', dept: 'Electronics & Comm', camera: 'RTSP Cam 02 (192.168.1.102)', status: 'active', fps: 15 },
  { id: '3', name: 'Lab C-301', dept: 'Mechanical Eng', camera: 'Webcam Stream 03', status: 'idle', fps: 0 },
  { id: '4', name: 'Auditorium Main', dept: 'General Admin', camera: 'RTSP Cam 04 (192.168.1.105)', status: 'active', fps: 30 },
];

interface AdminDashboardProps {
  currentView?: PortalView;
  onViewChange?: (view: PortalView) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ currentView, onViewChange }) => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'classrooms' | 'departments' | 'health'>('classrooms');

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      <Header
        userName={user?.full_name || 'System Admin'}
        userRole={user?.role || 'Super Admin'}
        isConnected={true}
        currentView={currentView}
        onViewChange={onViewChange}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Admin Header Banner */}
        <div className="glass-card p-6 border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-indigo-400" />
              <h2 className="text-xl font-bold text-white">Institutional Administration Console</h2>
            </div>
            <p className="text-sm text-slate-400 mt-1">Stanford Institute of Technology • Central Multi-Tenant Management</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="primary" icon={<Plus className="w-4 h-4" />}>
              Add Classroom Camera
            </Button>
            <Button variant="secondary" icon={<LogOut className="w-4 h-4" />} onClick={logout}>
              Sign Out
            </Button>
          </div>
        </div>

        {/* Quick System Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card title="Managed Classrooms">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-white font-display">18</span>
                <p className="text-xs text-indigo-400 font-medium mt-1">Across 4 Departments</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Building2 className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="Active RTSP Streams">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-emerald-400 font-display">14</span>
                <p className="text-xs text-emerald-400/80 font-medium mt-1">Live Processing @ 15 FPS</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Video className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="AI Inference Latency">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-cyan-400 font-display">18.4 ms</span>
                <p className="text-xs text-cyan-400/80 font-medium mt-1">GPU Accelerated (YOLOv8)</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <Cpu className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="Database & Redis Health">
            <div className="flex items-center justify-between mt-2">
              <div>
                <Badge variant="success" pulse>PostgreSQL 15 Connected</Badge>
                <p className="text-xs text-slate-400 mt-2">Redis Pub/Sub Active</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                <Server className="w-6 h-6" />
              </div>
            </div>
          </Card>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-white/10 pb-3">
          <button
            onClick={() => setActiveTab('classrooms')}
            className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'classrooms'
                ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Classrooms & Cameras
          </button>
          <button
            onClick={() => setActiveTab('departments')}
            className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'departments'
                ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Departments & Faculty
          </button>
          <button
            onClick={() => setActiveTab('health')}
            className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all ${
              activeTab === 'health'
                ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            System Infrastructure Health
          </button>
        </div>

        {/* Classrooms Tab */}
        {activeTab === 'classrooms' && (
          <Card title="Classroom Camera Infrastructure" subtitle="RTSP Camera Endpoint Configuration">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-xs font-semibold text-slate-400 uppercase">
                    <th className="py-3 px-4">Classroom Name</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Camera Endpoint</th>
                    <th className="py-3 px-4">Stream Status</th>
                    <th className="py-3 px-4">Frame Rate</th>
                    <th className="py-3 px-4 text-right">Settings</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {MOCK_CLASSROOMS.map((room) => (
                    <tr key={room.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-slate-200">{room.name}</td>
                      <td className="py-3.5 px-4 text-xs text-slate-400">{room.dept}</td>
                      <td className="py-3.5 px-4 font-mono text-xs text-cyan-400">{room.camera}</td>
                      <td className="py-3.5 px-4">
                        {room.status === 'active' ? (
                          <Badge variant="success" pulse>Stream Active</Badge>
                        ) : (
                          <Badge variant="neutral">Standby</Badge>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs">{room.fps} FPS</td>
                      <td className="py-3.5 px-4 text-right">
                        <Button variant="glass" size="sm" icon={<Settings className="w-3.5 h-3.5" />}>
                          Configure
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Departments Tab */}
        {activeTab === 'departments' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Computer Science & Engineering">
              <div className="space-y-3 mt-2 text-xs text-slate-300">
                <p><span className="text-slate-400">Head of Department:</span> Dr. Alan Turing</p>
                <p><span className="text-slate-400">Enrolled Students:</span> 240 Students</p>
                <p><span className="text-slate-400">Assigned Faculty:</span> 12 Professors</p>
                <div className="pt-2 flex items-center gap-2">
                  <Badge variant="purple">8 Classrooms</Badge>
                  <Badge variant="success">96% Enrollment Consent</Badge>
                </div>
              </div>
            </Card>

            <Card title="Electronics & Communication">
              <div className="space-y-3 mt-2 text-xs text-slate-300">
                <p><span className="text-slate-400">Head of Department:</span> Dr. Claude Shannon</p>
                <p><span className="text-slate-400">Enrolled Students:</span> 180 Students</p>
                <p><span className="text-slate-400">Assigned Faculty:</span> 9 Professors</p>
                <div className="pt-2 flex items-center gap-2">
                  <Badge variant="purple">6 Classrooms</Badge>
                  <Badge variant="success">92% Enrollment Consent</Badge>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Health Tab */}
        {activeTab === 'health' && (
          <Card title="System Diagnostics & Microservices" subtitle="Real-time backend service telemetry">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">FastAPI Core Backend</span>
                  <Badge variant="success">Port 8080 OK</Badge>
                </div>
                <p className="text-xs text-slate-400">Uptime: 99.98% • Uvicorn Async Workers Active</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">Redis Pub/Sub Broker</span>
                  <Badge variant="success">Port 6379 OK</Badge>
                </div>
                <p className="text-xs text-slate-400">Memory: 42 MB • Channels: 14 Active</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">AI Service Pipeline</span>
                  <Badge variant="purple">PyTorch / OpenCV</Badge>
                </div>
                <p className="text-xs text-slate-400">ArcFace 512-d Vector Extraction Ready</p>
              </div>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};
