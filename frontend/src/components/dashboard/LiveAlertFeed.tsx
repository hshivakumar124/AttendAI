import React from 'react';
import { LiveAlert } from '../../hooks/useWebSocketFeed';
import { Badge, BadgeVariant } from '../common/Badge';
import { AlertCircle, Clock, Smartphone } from 'lucide-react';

interface LiveAlertFeedProps {
  alerts: LiveAlert[];
}

export const LiveAlertFeed: React.FC<LiveAlertFeedProps> = ({ alerts }) => {
  const getIcon = (type: string) => {
    if (type.toLowerCase().includes('phone') || type.toLowerCase().includes('device')) {
      return <Smartphone className="w-4 h-4 text-rose-400" />;
    }
    return <Clock className="w-4 h-4 text-amber-400" />;
  };

  const getVariant = (severity: string): BadgeVariant => {
    if (severity === 'critical') return 'danger';
    if (severity === 'warning') return 'warning';
    return 'info';
  };

  return (
    <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
      {alerts.length === 0 ? (
        <div className="p-6 text-center text-slate-500 text-xs">
          <AlertCircle className="w-6 h-6 mx-auto mb-2 opacity-40" />
          No distraction or drowsiness alerts triggered for this session yet.
        </div>
      ) : (
        alerts.map((alert) => (
          <div
            key={alert.id}
            className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-3 hover:border-white/10 transition-all"
          >
            <div className="mt-0.5">{getIcon(alert.type)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-slate-200">{alert.type}</span>
                <span className="text-[10px] text-slate-400">{alert.timestamp}</span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 truncate">{alert.message}</p>
            </div>
            <Badge variant={getVariant(alert.severity)} size="sm">
              {alert.severity}
            </Badge>
          </div>
        ))
      )}
    </div>
  );
};
