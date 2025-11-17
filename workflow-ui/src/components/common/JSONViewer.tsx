import { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface JSONViewerProps {
  data: unknown;
  title?: string;
  className?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export default function JSONViewer({
  data,
  title,
  className,
  collapsible = false,
  defaultCollapsed = false,
}: JSONViewerProps) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title || 'data'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={cn('bg-gray-50 rounded-lg border border-gray-200', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-100">
        <div className="flex items-center gap-2">
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg
                className={cn('w-4 h-4 transition-transform', collapsed && '-rotate-90')}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
          )}
          {title && <span className="text-sm font-medium text-gray-700">{title}</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-green-600" />
                <span className="text-green-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded transition-colors"
            title="Download as JSON"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      {/* Content */}
      {!collapsed && (
        <div className="p-4 overflow-auto max-h-96">
          <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap break-words">
            {jsonString}
          </pre>
        </div>
      )}
    </div>
  );
}
