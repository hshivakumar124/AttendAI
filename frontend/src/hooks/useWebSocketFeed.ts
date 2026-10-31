import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../store/AuthContext';

export interface TrackData {
  track_id: string;
  bbox: [number, number, number, number];
  normalized_bbox: [number, number, number, number];
  confidence: number;
  student_id?: string;
  head_pose?: {
    orientation: string;
    is_attentive: boolean;
  };
  eye_state?: {
    ear: number;
    is_open: boolean;
    drowsy_alert: boolean;
    closed_frames: number;
  };
  engagement?: {
    score: number;
    label: string;
  };
  has_device_distraction?: boolean;
}

export interface LiveAlert {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'critical';
  track_id?: string;
}

export function useWebSocketFeed(sessionId: string) {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [tracks, setTracks] = useState<TrackData[]>([]);
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId || !token) return;

    const wsUrl = `ws://${window.location.host}/api/v1/ws/sessions/${sessionId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.tracks) {
          setTracks(message.tracks);

          // Check for new real-time alerts
          message.tracks.forEach((t: TrackData) => {
            if (t.eye_state?.drowsy_alert) {
              setAlerts((prev) => [
                {
                  id: `${t.track_id}-drowsy-${Date.now()}`,
                  type: 'Drowsiness Alert',
                  message: `${t.track_id} has closed eyes for over 2 seconds`,
                  timestamp: new Date().toLocaleTimeString(),
                  severity: 'critical',
                  track_id: t.track_id,
                },
                ...prev.slice(0, 19),
              ]);
            }
            if (t.has_device_distraction) {
              setAlerts((prev) => [
                {
                  id: `${t.track_id}-phone-${Date.now()}`,
                  type: 'Device Distraction',
                  message: `Mobile phone detected near ${t.track_id}`,
                  timestamp: new Date().toLocaleTimeString(),
                  severity: 'warning',
                  track_id: t.track_id,
                },
                ...prev.slice(0, 19),
              ]);
            }
          });
        }
      } catch (err) {
        console.error('Error parsing WebSocket message', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [sessionId, token]);

  return { isConnected, tracks, alerts };
}
