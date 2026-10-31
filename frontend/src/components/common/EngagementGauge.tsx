import React from 'react';

interface EngagementGaugeProps {
  score: number; // 0.0 to 100.0
  size?: number; // width/height in px
  label?: string;
}

export const EngagementGauge: React.FC<EngagementGaugeProps> = ({
  score,
  size = 120,
  label = "Engagement",
}) => {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  let color = "#10b981"; // Emerald
  if (score < 45) {
    color = "#f43f5e"; // Rose
  } else if (score < 75) {
    color = "#f59e0b"; // Amber
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
            style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.5s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-bold tracking-tight text-white font-display">
            {score.toFixed(0)}%
          </span>
        </div>
      </div>
      {label && <span className="mt-2 text-xs font-medium text-slate-400">{label}</span>}
    </div>
  );
};
