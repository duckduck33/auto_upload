import React from 'react';
import { Input } from '../ui/input';

interface KeywordInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
}

export const KeywordInput: React.FC<KeywordInputProps> = ({
  value,
  onChange,
  disabled = false,
  error,
}) => {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">키워드 입력</h3>
        <p className="text-sm text-gray-600">
          블로그 글을 생성할 키워드를 입력해주세요
        </p>
      </div>
      
      <Input
        value={value}
        onChange={onChange}
        placeholder="예: 인공지능, 블로그 마케팅, 디지털 마케팅..."
        disabled={disabled}
        error={error}
        className="text-center text-lg"
      />
    </div>
  );
}; 