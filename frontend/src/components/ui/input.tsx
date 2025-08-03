import React from 'react';

interface InputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  type?: 'text' | 'number' | 'email' | 'password';
  disabled?: boolean;
  className?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  value,
  onChange,
  placeholder = '',
  label,
  type = 'text',
  disabled = false,
  className = '',
  error,
}) => {
  return (
    <div className="w-full space-y-2">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-4 py-3 bg-white border border-gray-300 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 ${
            error ? 'border-red-500 focus:ring-red-500' : ''
          } ${className}`}
        />
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    </div>
  );
}; 