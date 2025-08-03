'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api';

interface NaverCredentialsProps {
  className?: string;
}

export default function NaverCredentials({ className = '' }: NaverCredentialsProps) {
  const [naverId, setNaverId] = useState('');
  const [naverPw, setNaverPw] = useState('');
  const [hasPassword, setHasPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // 컴포넌트 마운트 시 저장된 정보 조회
  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      const response = await apiClient.getNaverCredentials();
      if (response.success && response.data) {
        setNaverId(response.data.naverId);
        setHasPassword(response.data.hasPassword);
      }
    } catch {
      console.error('네이버 로그인 정보 조회 실패');
    }
  };

  const handleSave = async () => {
    if (!naverId.trim() || !naverPw.trim()) {
      setMessage('네이버 아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const response = await apiClient.saveNaverCredentials(naverId.trim(), naverPw.trim());
      
      if (response.success) {
        setMessage('네이버 로그인 정보가 저장되었습니다.');
        setHasPassword(true);
        setIsEditing(false);
      } else {
        setMessage(response.message || '저장에 실패했습니다.');
      }
    } catch {
      setMessage('저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setMessage('');
  };

  const handleCancel = () => {
    setIsEditing(false);
    setNaverPw('');
    setMessage('');
    loadCredentials(); // 원래 값으로 복원
  };

    return (
    <div className={`bg-white rounded-lg p-4 shadow-sm border border-gray-200 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-900 mb-3">네이버 로그인</h3>
      
      <div className="space-y-3">
        {/* 입력창들 - 가로 정렬 */}
        <div className="flex gap-3">
          {/* 네이버 아이디 */}
          <div className="flex-1">
            <label htmlFor="naverId" className="block text-xs font-medium text-gray-700 mb-1">
              아이디
            </label>
            <input
              type="text"
              id="naverId"
              value={naverId}
              onChange={(e) => setNaverId(e.target.value)}
              disabled={!isEditing}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              placeholder="네이버 아이디"
            />
          </div>

          {/* 네이버 비밀번호 */}
          <div className="flex-1">
            <label htmlFor="naverPw" className="block text-xs font-medium text-gray-700 mb-1">
              비밀번호
            </label>
                         <input
               type="text"
               id="naverPw"
               value={naverPw}
               onChange={(e) => setNaverPw(e.target.value)}
               disabled={!isEditing}
               className="w-full px-2 py-1 text-sm border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
               placeholder="비밀번호"
             />
          </div>

          {/* 저장 버튼 */}
          <div className="flex items-end">
            {!isEditing ? (
              <button
                onClick={handleEdit}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {hasPassword ? '수정' : '저장'}
              </button>
            ) : (
              <div className="flex gap-1">
                <button
                  onClick={handleSave}
                  disabled={isLoading}
                  className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? '저장 중...' : '저장'}
                </button>
                <button
                  onClick={handleCancel}
                  disabled={isLoading}
                  className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  취소
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 저장 상태 표시 */}
        {hasPassword && !isEditing && (
          <p className="text-xs text-gray-500">저장됨</p>
        )}

        {/* 메시지 */}
        {message && (
          <div className={`p-2 rounded text-xs ${
            message.includes('성공') 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
} 