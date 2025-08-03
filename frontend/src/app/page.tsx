'use client';

import React, { useState, useEffect } from 'react';
import { KeywordInput } from '../components/settings/KeywordInput';
import { AutomationControls } from '../components/settings/AutomationControls';
import { StatusDisplay } from '../components/settings/StatusDisplay';
import { LogViewer } from '../components/monitoring/LogViewer';
import { GeneratedPostViewer } from '../components/monitoring/GeneratedPostViewer';
import GeneratingPostMonitor from '../components/monitoring/GeneratingPostMonitor';
import { Tabs } from '../components/ui/tabs';
import { apiClient, GeneratingPost } from '../lib/api';
import { storage } from '../lib/utils';
import type { AppState, GeneratedPost } from '../types';

export default function Home() {
  const [state, setState] = useState<AppState>({
    keyword: '',
    postCount: 1, // 고정값
    isRunning: false,
    status: '대기 중',
    progress: 0,
    logs: [],
    generatedPosts: [],
    activeTab: 'logs',
  });

  const [generatingPost, setGeneratingPost] = useState<GeneratingPost | null>(null);

  // 상태 업데이트 함수
  const updateState = (updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  // 키워드 변경 핸들러
  const handleKeywordChange = (keyword: string) => {
    updateState({ keyword });
    storage.set('keyword', keyword);
  };

  // 자동화 시작 핸들러
  const handleStartAutomation = async () => {
    try {
      updateState({ 
        isRunning: true, 
        status: '자동화 시작 중...',
        progress: 0 
      });

      const response = await apiClient.startAutomation({
        keyword: state.keyword,
        postCount: 1, // 고정값
      });

      if (response.success) {
        updateState({ status: '자동화가 시작되었습니다.' });
        // 실시간 상태 업데이트 시작
        startStatusPolling();
      } else {
        const errorLog = `[${new Date().toISOString()}] 자동화 시작 실패: ${response.message}`;
        updateState({ 
          isRunning: false, 
          status: `오류: ${response.message}`,
          logs: [...state.logs, errorLog]
        });
      }
    } catch (error) {
      const errorLog = `[${new Date().toISOString()}] 자동화 시작 중 네트워크 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`;
      updateState({ 
        isRunning: false, 
        status: `오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
        logs: [...state.logs, errorLog]
      });
    }
  };

  // 자동화 정지 핸들러
  const handleStopAutomation = async () => {
    try {
      const response = await apiClient.stopAutomation();
      updateState({ 
        isRunning: false, 
        status: '자동화가 정지되었습니다.',
        progress: 0 
      });
    } catch (error) {
      updateState({ 
        status: `정지 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}` 
      });
    }
  };

  // 로그 지우기 핸들러
  const handleClearLogs = async () => {
    try {
      await apiClient.clearLogs();
      updateState({ logs: [] });
    } catch (error) {
      console.error('로그 지우기 실패:', error);
    }
  };

  // 탭 변경 핸들러
  const handleTabChange = (tabId: string) => {
    updateState({ activeTab: tabId as 'logs' | 'generating' | 'posts' });
  };

  // 상태 폴링
  const startStatusPolling = () => {
    const pollStatus = async () => {
      try {
        const status = await apiClient.getStatus();
        const logs = await apiClient.getLogs();
        const posts = await apiClient.getGeneratedPosts();
        const generating = await apiClient.getGeneratingPost();

        console.log('폴링 결과:', { status, generating }); // 디버깅용

        updateState({
          isRunning: status.isRunning,
          status: status.status,
          progress: status.progress,
          logs: logs.map(log => `[${log.timestamp}] ${log.message}`),
          generatedPosts: posts,
        });

        setGeneratingPost(generating);

        // 자동화가 실행 중이거나 생성 중인 글이 있으면 계속 폴링
        if (status.isRunning || (generating && generating.isGenerating)) {
          setTimeout(pollStatus, 1000); // 1초마다 폴링
        }
      } catch (error) {
        console.error('상태 폴링 오류:', error);
        // 에러를 로그에 추가
        const errorLog = `[${new Date().toISOString()}] API 연결 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`;
        updateState({
          logs: [...state.logs, errorLog],
          isRunning: false,
          status: 'API 연결 오류'
        });
      }
    };

    pollStatus();
  };

  // 초기 로드 시 저장된 설정 복원
  useEffect(() => {
    const savedKeyword = storage.get('keyword');

    if (savedKeyword) updateState({ keyword: savedKeyword });

    // 초기 상태 로드
    const loadInitialState = async () => {
      try {
        const status = await apiClient.getStatus();
        const logs = await apiClient.getLogs();
        const posts = await apiClient.getGeneratedPosts();
        const generating = await apiClient.getGeneratingPost();

        updateState({
          isRunning: status.isRunning,
          status: status.status,
          progress: status.progress,
          logs: logs.map(log => `[${log.timestamp}] ${log.message}`),
          generatedPosts: posts,
        });

        setGeneratingPost(generating);

        if (status.isRunning) {
          startStatusPolling();
        }
      } catch (error) {
        console.error('초기 상태 로드 오류:', error);
      }
    };

    loadInitialState();
  }, []);

  const tabs = [
    {
      id: 'logs',
      label: '실시간 출력상황',
      content: (
        <LogViewer
          logs={state.logs}
          onClearLogs={handleClearLogs}
        />
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 text-gray-900">
      {/* 헤더 */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 p-6 shadow-sm">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              네이버 블로그 AI 자동화
            </h1>
            <p className="text-gray-600 text-lg">
              AI기반 스마트 콘텐츠 생성 및 자동 포스팅 시스템
            </p>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽 패널 - 설정 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200/50 shadow-lg">
            <div className="space-y-8">
              <KeywordInput
                value={state.keyword}
                onChange={handleKeywordChange}
                disabled={state.isRunning}
                error={!state.keyword.trim() && state.isRunning ? '키워드를 입력해주세요' : undefined}
              />
              
              <AutomationControls
                isRunning={state.isRunning}
                onStart={handleStartAutomation}
                onStop={handleStopAutomation}
                disabled={!state.keyword.trim()}
                loading={state.isRunning}
              />
              
              <StatusDisplay
                status={state.status}
                progress={state.progress}
              />
            </div>
          </div>

          {/* 오른쪽 패널 - 모니터링 */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200/50 shadow-lg">
            <Tabs
              tabs={tabs}
              activeTab={state.activeTab}
              onTabChange={handleTabChange}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
