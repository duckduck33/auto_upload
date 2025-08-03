import React from 'react';
import { GeneratingPost } from '@/lib/api';

interface GeneratingPostMonitorProps {
  generatingPost: GeneratingPost | null;
}

export default function GeneratingPostMonitor({ generatingPost }: GeneratingPostMonitorProps) {
  if (!generatingPost || !generatingPost.isGenerating) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">실시간 생성 모니터링</h3>
        <p className="text-sm text-gray-600">현재 생성 중인 글이 없습니다</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">실시간 생성 모니터링</h3>
      
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="space-y-4">
          {/* 키워드 정보 */}
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                키워드: {generatingPost.currentPost?.keyword}
              </p>
              <p className="text-xs text-gray-500">
                시작 시간: {generatingPost.currentPost?.startedAt}
              </p>
            </div>
          </div>

          {/* 현재 상태 */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-900">현재 상태</span>
            </div>
            <p className="text-sm text-gray-700">{generatingPost.currentContent}</p>
          </div>

          {/* 진행률 표시 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">생성 진행률</span>
              <span className="text-emerald-600 font-medium">진행 중...</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-emerald-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>

          {/* 상태 메시지 */}
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-sm font-medium text-emerald-800">AI가 글을 생성하고 있습니다</span>
            </div>
            <p className="text-xs text-emerald-700 mt-1">
              잠시만 기다려주세요. 고품질의 콘텐츠를 생성하고 있습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 