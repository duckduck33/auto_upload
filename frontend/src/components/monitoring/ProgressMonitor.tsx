import React from 'react';

interface ProgressMonitorProps {
  currentStep: number;
  totalSteps: number;
  stepDescription: string;
  className?: string;
}

export const ProgressMonitor: React.FC<ProgressMonitorProps> = ({
  currentStep,
  totalSteps,
  stepDescription,
  className = '',
}) => {
  const progress = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">진행 상황</h3>
        <span className="text-sm text-gray-400">
          {currentStep} / {totalSteps}
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-sm text-gray-300">{stepDescription}</div>
      </div>
    </div>
  );
}; 