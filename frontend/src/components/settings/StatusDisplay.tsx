import React from 'react';
import { Progress } from '../ui/progress';

interface StatusDisplayProps {
  status: string;
  progress: number;
  className?: string;
}

export const StatusDisplay: React.FC<StatusDisplayProps> = ({
  status,
  progress,
  className = '',
}) => {
  const getStatusColor = (status: string) => {
    if (status.includes('오류') || status.includes('실패')) return 'red';
    if (status.includes('완료') || status.includes('성공')) return 'emerald';
    if (status.includes('대기')) return 'blue';
    return 'emerald';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">현재 상태</h3>
        <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
          <div className="text-gray-700 text-sm font-medium">{status}</div>
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="text-center">
          <h4 className="text-sm font-medium text-gray-700 mb-2">진행률</h4>
        </div>
        <Progress 
          value={progress} 
          color={getStatusColor(status) as 'emerald' | 'blue' | 'yellow' | 'red'}
        />
      </div>
    </div>
  );
}; 