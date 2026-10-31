import React, { useState } from 'react';
import { useAuth } from '../store/AuthContext';
import { Header, PortalView } from '../components/common/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { BiometricConsentModal } from '../components/student/BiometricConsentModal';
import { FaceEnrollmentWidget } from '../components/student/FaceEnrollmentWidget';
import { ShieldCheck, Lock, Trash2, CheckCircle2, Calendar, Award, UserCheck } from 'lucide-react';
import { apiClient } from '../api/client';

interface StudentPortalProps {
  currentView?: PortalView;
  onViewChange?: (view: PortalView) => void;
}

export const StudentPortal: React.FC<StudentPortalProps> = ({ currentView, onViewChange }) => {
  const { user, logout } = useAuth();
  const [isConsentModalOpen, setIsConsentModalOpen] = useState(false);
  const [hasConsent, setHasConsent] = useState(user?.consent_biometric || false);
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleDeleteBiometrics = async () => {
    if (!window.confirm('Are you sure you want to permanently erase all your facial biometric data? This action cannot be undone.')) {
      return;
    }
    setIsDeleting(true);
    setMessage(null);

    try {
      if (user?.id) {
        await apiClient.delete(`/users/${user.id}/biometric-data`);
      }
      setHasConsent(false);
      setIsEnrolled(false);
      setMessage({ type: 'success', text: 'All facial biometric data successfully deleted under Right-to-Erasure terms.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to purge biometric data' });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
      <Header
        userName={user?.full_name || 'Alex Rivera'}
        userRole={user?.role || 'Student'}
        isConnected={true}
        currentView={currentView}
        onViewChange={onViewChange}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Banner */}
        <div className="glass-card p-6 border-cyan-500/20 bg-gradient-to-r from-indigo-950/30 via-cyan-950/20 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-cyan-400" />
              <h2 className="text-xl font-bold text-white">Student Biometric & Attendance Portal</h2>
            </div>
            <p className="text-sm text-slate-400 mt-1">Computer Science Department • B.Tech 4th Year • Roll No: CS-2022-041</p>
          </div>
          <Button variant="secondary" onClick={logout}>
            Sign Out
          </Button>
        </div>

        {/* Message Banner */}
        {message && (
          <div
            className={`p-4 rounded-xl border text-xs font-semibold flex items-center justify-between ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">✕</button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Overall Attendance">
            <div className="flex items-center justify-between mt-2">
              <div>
                <span className="text-3xl font-extrabold text-emerald-400 font-display">94.2%</span>
                <p className="text-xs text-slate-400 mt-1">33 of 35 Sessions Attended</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Award className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card title="Biometric Consent Status">
            <div className="flex items-center justify-between mt-2">
              <div>
                {hasConsent ? (
                  <Badge variant="success" pulse>Consent Granted</Badge>
                ) : (
                  <Badge variant="danger">Consent Pending</Badge>
                )}
                <p className="text-xs text-slate-400 mt-2">Required before face enrollment</p>
              </div>
              {!hasConsent && (
                <Button variant="primary" size="sm" onClick={() => setIsConsentModalOpen(true)}>
                  Grant Consent
                </Button>
              )}
            </div>
          </Card>

          <Card title="Face Recognition Status">
            <div className="flex items-center justify-between mt-2">
              <div>
                {isEnrolled ? (
                  <Badge variant="purple">AES-256 Vector Stored</Badge>
                ) : (
                  <Badge variant="neutral">Not Enrolled</Badge>
                )}
                <p className="text-xs text-slate-400 mt-2">512-d ArcFace Embedding</p>
              </div>
              {isEnrolled && (
                <Button variant="danger" size="sm" isLoading={isDeleting} onClick={handleDeleteBiometrics}>
                  Purge Data
                </Button>
              )}
            </div>
          </Card>
        </div>

        {/* Face Enrollment Section */}
        {hasConsent && !isEnrolled && (
          <FaceEnrollmentWidget
            onSuccess={() => {
              setIsEnrolled(true);
              setMessage({ type: 'success', text: 'Facial embedding successfully encrypted with AES-256 and enrolled!' });
            }}
          />
        )}

        {/* Attendance History Roster */}
        <Card title="Recent Attendance Log" subtitle="Verified classroom presence logs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs font-semibold text-slate-400 uppercase">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Course</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Arrival Time</th>
                  <th className="py-3 px-4">Detection Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs">2026-07-23</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200">CS-401: Deep Learning</td>
                  <td className="py-3.5 px-4"><Badge variant="success">Present</Badge></td>
                  <td className="py-3.5 px-4 text-xs font-mono">09:02 AM</td>
                  <td className="py-3.5 px-4 font-mono text-cyan-400">96.8%</td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs">2026-07-22</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200">CS-401: Deep Learning</td>
                  <td className="py-3.5 px-4"><Badge variant="success">Present</Badge></td>
                  <td className="py-3.5 px-4 text-xs font-mono">09:01 AM</td>
                  <td className="py-3.5 px-4 font-mono text-cyan-400">95.4%</td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs">2026-07-21</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200">CS-401: Deep Learning</td>
                  <td className="py-3.5 px-4"><Badge variant="warning">Late Arrival</Badge></td>
                  <td className="py-3.5 px-4 text-xs font-mono">09:18 AM</td>
                  <td className="py-3.5 px-4 font-mono text-cyan-400">92.1%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </main>

      {/* Biometric Consent Modal */}
      <BiometricConsentModal
        isOpen={isConsentModalOpen}
        onClose={() => setIsConsentModalOpen(false)}
        onConsentGranted={() => {
          setHasConsent(true);
          setMessage({ type: 'success', text: 'Biometric consent recorded! You may now proceed with face enrollment.' });
        }}
      />
    </div>
  );
};
