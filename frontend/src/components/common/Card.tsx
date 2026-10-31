import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverable = false,
  title,
  subtitle,
  headerAction,
}) => {
  return (
    <div className={`glass-card p-5 ${hoverable ? 'glass-card-hover' : ''} ${className}`}>
      {(title || headerAction) && (
        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
          <div>
            {title && <h3 className="text-lg font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
