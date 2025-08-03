import React from 'react';

interface ProgressProps {
  value: number; // 0-100
  max?: number;
  label?: string;
  showPercentage?: boolean;
  className?: string;
  color?: 'emerald' | 'blue' | 'yellow' | 'red';
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  className = '',
  color = 'emerald',
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colorClasses = {
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  };
  
  return (
    <div className={`w-full space-y-3 ${className}`}>
      {label && (
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {showPercentage && (
            <span className="text-sm text-gray-500 font-mono">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}; 