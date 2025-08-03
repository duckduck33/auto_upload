import React from 'react';
import { Button } from '../ui/button';

interface LogViewerProps {
  logs: any[];
  onClearLogs: () => void;
  className?: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({
  logs,
  onClearLogs,
  className = '',
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">실시간 출력상황</h3>
          <p className="text-sm text-gray-600">자동화 진행 상황을 실시간으로 확인하세요</p>
        </div>
        <Button
          onClick={onClearLogs}
          variant="ghost"
          size="sm"
        >
          로그 지우기
        </Button>
      </div>
      
      <div className="bg-gray-50 rounded-xl p-4 h-80 overflow-y-auto border border-gray-200">
        {logs.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">📝</div>
            <div className="text-gray-500 text-sm">로그가 없습니다</div>
            <div className="text-gray-400 text-xs mt-1">자동화를 시작하면 로그가 표시됩니다</div>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log, index) => (
              <div key={index} className="text-sm text-gray-700 font-mono bg-white rounded-lg p-3 border border-gray-200">
                {typeof log === 'string' ? log : log.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}; 