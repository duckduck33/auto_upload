import React from 'react';

interface GeneratedPost {
  id: string;
  title: string;
  content: string;
  createdAt: string;
}

interface GeneratedPostViewerProps {
  posts: GeneratedPost[];
  className?: string;
}

export const GeneratedPostViewer: React.FC<GeneratedPostViewerProps> = ({
  posts,
  className = '',
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <h3 className="text-lg font-semibold text-gray-900">생성된 글</h3>
        <p className="text-sm text-gray-600">AI가 생성한 블로그 글을 확인하세요</p>
      </div>
      
      <div className="space-y-4">
        {posts.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg mb-2">📄</div>
            <div className="text-gray-500 text-sm">생성된 글이 없습니다</div>
            <div className="text-gray-400 text-xs mt-1">자동화를 완료하면 생성된 글이 표시됩니다</div>
          </div>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="bg-white rounded-xl p-6 border border-gray-200 hover:border-gray-300 transition-colors shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <h4 className="text-gray-900 font-semibold text-lg">{post.title}</h4>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">
                  {new Date(post.createdAt).toLocaleString('ko-KR')}
                </span>
              </div>
              <div className="text-gray-700 text-sm leading-relaxed line-clamp-3">
                {post.content}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg">
                  AI 생성 완료
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}; 