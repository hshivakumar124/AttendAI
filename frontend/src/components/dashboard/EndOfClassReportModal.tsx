import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { EngagementGauge } from '../common/EngagementGauge';
import { Download, X, CheckCircle2, XCircle, AlertTriangle, Clock, Award } from 'lucide-react';

export interface RosterItem {
  student_id: string;
  name: string;
  roll_no: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE';
  presence_percentage: number;
  engagement_score: number;
  device_minutes: number;
  drowsy_minutes: number;
}

export interface EndOfClassReportData {
  courseName: string;
  className: string;
  facultyName: string;
  dateStr: string;
  durationMinutes: number;
  totalRegistered: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  avgEngagementScore: number;
  deviceEventsCount: number;
  drowsyEventsCount: number;
  roster: RosterItem[];
}

interface EndOfClassReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportData: EndOfClassReportData;
}

export const EndOfClassReportModal: React.FC<EndOfClassReportModalProps> = ({
  isOpen,
  onClose,
  reportData,
}) => {
  if (!isOpen) return null;

  const downloadCSV = () => {
    const headers = 'Roll No,Student Name,Status,Presence %,Visual Engagement %,Device Activity (min),Drowsiness (min)\n';
    const rows = reportData.roster
      .map(
        (r) =>
          `"${r.roll_no}","${r.name}","${r.status}",${r.presence_percentage}%,${r.engagement_score}%,${r.device_minutes},${r.drowsy_minutes}`
      )
      .join('\n');

    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${reportData.courseName}_Attendance_Report_${reportData.dateStr}.csv`;
    a.click();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="glass-card p-6 max-w-4xl w-full border-cyan-500/40 shadow-2xl relative space-y-6 max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="info" size="sm">
                FINAL CLASS REPORT
              </Badge>
              <span className="text-xs text-slate-400 font-mono">{reportData.dateStr}</span>
            </div>
            <h2 className="text-2xl font-extrabold text-white mt-1">{reportData.courseName}</h2>
            <p className="text-xs text-slate-400">
              Classroom: <strong className="text-slate-200">{reportData.className}</strong> | Faculty:{' '}
              <strong className="text-slate-200">{reportData.facultyName}</strong> | Duration:{' '}
              <strong className="text-slate-200">{reportData.durationMinutes} Minutes</strong>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="primary" icon={<Download className="w-4 h-4" />} onClick={downloadCSV}>
              Export CSV Report
            </Button>
            <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/5">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Top Summary Metrics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 flex flex-col justify-between">
            <span className="text-xs text-slate-400 font-medium">Registered Students</span>
            <p className="text-3xl font-extrabold text-white mt-2">{reportData.totalRegistered}</p>
          </div>

          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col justify-between">
            <span className="text-xs text-emerald-400 font-medium">Present Students</span>
            <p className="text-3xl font-extrabold text-emerald-400 mt-2">{reportData.presentCount}</p>
          </div>

          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex flex-col justify-between">
            <span className="text-xs text-rose-400 font-medium">Absent Students</span>
            <p className="text-3xl font-extrabold text-rose-400 mt-2">{reportData.absentCount}</p>
          </div>

          <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex flex-col justify-between">
            <span className="text-xs text-cyan-400 font-medium">Avg Visual Engagement</span>
            <p className="text-3xl font-extrabold text-cyan-300 mt-2">{reportData.avgEngagementScore}%</p>
          </div>
        </div>

        {/* Detailed Attendance Roster Table */}
        <div className="space-y-3">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-cyan-400" />
            Individual Student Attendance & Behavior Breakdown
          </h3>

          <div className="rounded-xl border border-white/10 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-white/10 uppercase tracking-wider">
                <tr>
                  <th className="p-3">Roll No</th>
                  <th className="p-3">Student Name</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Presence %</th>
                  <th className="p-3 text-right">Visual Engagement</th>
                  <th className="p-3 text-right">Device Usage</th>
                  <th className="p-3 text-right">Drowsiness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-slate-900/40">
                {reportData.roster.map((s) => (
                  <tr key={s.student_id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-mono text-cyan-300">{s.roll_no}</td>
                    <td className="p-3 font-semibold text-white">{s.name}</td>
                    <td className="p-3">
                      <Badge variant={s.status === 'PRESENT' ? 'success' : s.status === 'LATE' ? 'warning' : 'danger'}>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="p-3 text-right font-bold text-slate-200">{s.presence_percentage}%</td>
                    <td className="p-3 text-right font-bold text-cyan-400">{s.status !== 'ABSENT' ? `${s.engagement_score}%` : 'N/A'}</td>
                    <td className="p-3 text-right text-slate-300">{s.status !== 'ABSENT' ? `${s.device_minutes} min` : 'N/A'}</td>
                    <td className="p-3 text-right text-slate-300">{s.status !== 'ABSENT' ? `${s.drowsy_minutes} min` : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
