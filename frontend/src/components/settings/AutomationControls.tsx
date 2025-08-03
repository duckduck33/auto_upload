import React from 'react';
import { Button } from '../ui/button';

interface AutomationControlsProps {
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export const AutomationControls: React.FC<AutomationControlsProps> = ({
  isRunning,
  onStart,
  onStop,
  disabled = false,
  loading = false,
}) => {
  return (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">자동화 제어</h3>
        <p className="text-sm text-gray-600">
          {isRunning ? '자동화가 실행 중입니다' : '키워드를 입력하고 자동화를 시작하세요'}
        </p>
      </div>
      
      <div className="space-y-3">
        <Button
          onClick={onStart}
          variant="primary"
          size="lg"
          disabled={disabled || isRunning}
          loading={loading}
          className="w-full"
        >
          {isRunning ? '실행 중...' : '자동화 시작'}
        </Button>
        
        <Button
          onClick={onStop}
          variant="danger"
          size="lg"
          disabled={disabled || !isRunning}
          className="w-full"
        >
          자동화 정지
        </Button>
      </div>
    </div>
  );
}; 