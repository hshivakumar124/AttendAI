import React, { useState } from 'react';
import { useAuth } from '../store/AuthContext';
import { Header, PortalView } from '../components/common/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EngagementGauge } from '../components/common/EngagementGauge';
import { LiveVideoCanvas } from '../components/dashboard/LiveVideoCanvas';
import { LiveAlertFeed } from '../components/dashboard/LiveAlertFeed';
import { useWebSocketFeed, LiveAlert } from '../hooks/useWebSocketFeed';
import { Play, Pause, LogOut, Users, Clock, AlertTriangle, Sparkles, CheckCircle2, XCircle } from 'lucide-react';

const MOCK_STUDENTS = [
  { id: '1', name: 'Alex Rivera', role: 'student', status: 'present', engagement: 88, arrival: '09:02 AM' },
  { id: '2', name: 'Jordan Lee', role: 'student', status: 'late', engagement: 62, arrival: '09:18 AM' },
  { id: '3', name: 'Taylor Swift', role: 'student', status: 'present', engagement: 94, arrival: '09:01 AM' },
  { id: '4', name: 'Chris Evans', role: 'student', status: 'absent', engagement: 0, arrival: '-' },
  { id: '5', name: 'Morgan Freeman', role: 'student', status: 'present', engagement: 85, arrival: '09:04 AM' },
];

interface FacultyDashboardProps {
  currentView?: PortalView;
  onViewChange?: (view: PortalView) => void;
}

export const FacultyDashboard: React.FC<FacultyDashboardProps> = ({ currentView, onViewChange }) => {
  const { user, logout } = useAuth();
  const [isSessionActive, setIsSessionActive] = useState(true);

  // Connect to WebSocket feed
  const { isConnected, tracks, alerts: wsAlerts } = useWebSocketFeed('session_cs401_001');

  // Fallback initial alerts for preview
  const initialAlerts: LiveAlert[] = [
    {
      id: 'alert-1',
      type: 'Drowsiness Alert',
      message: 'Jordan Lee (track_2) — Eye closure > 2.0 sec',
      timestamp: '09:22:15 AM',
      severity: 'critical',
      track_id: 'track_2',
    },
    {
      id: 'alert-2',
      type: 'Device Distraction',
      message: 'Mobile phone detected near Alex Rivera (track_1)',
      timestamp: '09:18:40 AM',
      severity: 'warning',
      track_id: 'track_1',
    },
  ];

  const alertsToDisplay = wsAlerts.length > 0 ? wsAlerts : initialAlerts;

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      <Header
        userName={user?.full_name || 'Dr. Sarah Jenkins'}
        userRole={user?.role || 'Faculty'}
        isConnected={isConnected || isSessionActive}
        currentView={currentView}
        onViewChange={onViewChange}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Session Banner */}
        <div className="glass-card p-6 border-cyan-500/20 bg-gradient-to-r from-cyan-950/30 via-indigo-950/20 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              <h2 className="text-xl font-bold text-white">CS-401: Deep Learning & Computer Vision</h2>
            </div>
            <p className="text-sm text-slate-400 mt-1">Hall A-102 • 45 Enrolled Students • Live AI Video Analytics</p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant={isSessionActive ? 'danger' : 'primary'}
              icon={isSessionActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              onClick={() => setIsSessionActive(!isSessionActive)}
            >
              {isSessionActive ? 'Pause Stream AI' : 'Start Session AI'}
            </Button>
            <Button variant="secondary" icon={<LogOut className="w-4 h-4" />} onClick={logout}>
              Sign Out
            </Button>
          </div>
        </div>

        {/* Live Camera Feed & Alert Ticker Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <LiveVideoCanvas tracks={tracks} isLive={isSessionActive} />
          </div>

          <div>
            <Card title="Live Distraction Alerts" subtitle="Real-time events streamed via WebSockets">
              <LiveAlertFeed alerts={alertsToDisplay} />
            </Card>
          </div>
        </div>

        {/* Real-time Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card title="Present Students">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-white font-display">38 / 45</span>
                <p className="text-xs text-emerald-400 font-medium mt-1">84.4% Attendance Rate</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Users className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="Avg Class Engagement">
            <div className="flex items-center justify-around mt-1">
              <EngagementGauge score={82} size={80} />
              <div className="text-left space-y-1">
                <Badge variant="success">High Focus</Badge>
                <p className="text-xs text-slate-400">+4% vs last session</p>
              </div>
            </div>
          </Card>

          <Card title="Drowsiness Alerts">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-amber-400 font-display">2</span>
                <p className="text-xs text-amber-400/80 font-medium mt-1">Temporal EAR &lt; 0.25</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Clock className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="Device Distractions">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-rose-400 font-display">3</span>
                <p className="text-xs text-rose-400/80 font-medium mt-1">YOLOv8 Phone Detections</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
            </div>
          </Card>
        </div>

        {/* Student Attendance List */}
        <Card title="Session Attendance Roster" subtitle="Real-time physical attendance tracking">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs font-semibold text-slate-400 uppercase">
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Arrival Time</th>
                  <th className="py-3 px-4">Visual Engagement</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {MOCK_STUDENTS.map((student) => (
                  <tr key={student.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-200">{student.name}</td>
                    <td className="py-3.5 px-4">
                      {student.status === 'present' ? (
                        <Badge variant="success">Present</Badge>
                      ) : student.status === 'late' ? (
                        <Badge variant="warning">Late Arrival</Badge>
                      ) : (
                        <Badge variant="danger">Absent</Badge>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-xs font-mono">{student.arrival}</td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${student.engagement >= 75 ? 'bg-emerald-400' : student.engagement >= 45 ? 'bg-amber-400' : 'bg-rose-400'}`}
                            style={{ width: `${student.engagement}%` }}
                          />
                        </div>
                        <span className="text-xs font-bold font-mono text-slate-300">{student.engagement}%</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Button variant="glass" size="sm">
                        Manual Override
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </main>
    </div>
  );
};
