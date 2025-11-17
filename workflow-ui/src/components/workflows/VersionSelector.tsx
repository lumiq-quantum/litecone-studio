import { useState } from 'react';
import { motion } from 'framer-motion';
import { GitBranch, Check, Calendar, User, ChevronDown } from 'lucide-react';
import type { WorkflowResponse } from '@/types';
import { cn } from '@/lib/utils';

interface VersionSelectorProps {
  versions: WorkflowResponse[];
  selectedVersion: number;
  onVersionSelect: (version: number) => void;
  currentVersion?: number;
  className?: string;
}

export default function VersionSelector({
  versions,
  selectedVersion,
  onVersionSelect,
  currentVersion,
  className = '',
}: VersionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Sort versions in descending order (newest first)
  const sortedVersions = [...versions].sort((a, b) => b.version - a.version);

  const selectedVersionData = sortedVersions.find((v) => v.version === selectedVersion);

  const handleVersionClick = (version: number) => {
    onVersionSelect(version);
    setIsOpen(false);
  };

  return (
    <div className={cn('relative', className)}>
      {/* Selector Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <GitBranch className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">
                Version {selectedVersion}
              </span>
              {selectedVersion === currentVersion && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  Current
                </span>
              )}
            </div>
            {selectedVersionData && (
              <span className="text-xs text-gray-500">
                {new Date(selectedVersionData.created_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
        <ChevronDown
          className={cn(
            'w-5 h-5 text-gray-400 transition-transform',
            isOpen && 'transform rotate-180'
          )}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute z-20 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto"
          >
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Version History
              </div>
              {sortedVersions.map((version) => {
                const isSelected = version.version === selectedVersion;
                const isCurrent = version.version === currentVersion;

                return (
                  <button
                    key={version.id}
                    type="button"
                    onClick={() => handleVersionClick(version.version)}
                    className={cn(
                      'w-full flex items-start gap-3 px-3 py-3 rounded-lg transition-colors text-left',
                      isSelected
                        ? 'bg-blue-50 hover:bg-blue-100'
                        : 'hover:bg-gray-50'
                    )}
                  >
                    {/* Version Indicator */}
                    <div className="flex-shrink-0 pt-0.5">
                      {isSelected ? (
                        <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                          <Check className="w-3 h-3 text-white" />
                        </div>
                      ) : (
                        <div
                          className={cn(
                            'w-5 h-5 rounded-full border-2',
                            isCurrent
                              ? 'border-green-500 bg-green-50'
                              : 'border-gray-300 bg-white'
                          )}
                        >
                          {isCurrent && (
                            <div className="w-full h-full flex items-center justify-center">
                              <div className="w-2 h-2 bg-green-500 rounded-full" />
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Version Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={cn(
                            'text-sm font-medium',
                            isSelected ? 'text-blue-900' : 'text-gray-900'
                          )}
                        >
                          Version {version.version}
                        </span>
                        {isCurrent && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            Current
                          </span>
                        )}
                      </div>

                      {/* Metadata */}
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 text-xs text-gray-500">
                          <Calendar className="w-3 h-3" />
                          <span>
                            {new Date(version.created_at).toLocaleString()}
                          </span>
                        </div>
                        {version.created_by && (
                          <div className="flex items-center gap-1.5 text-xs text-gray-500">
                            <User className="w-3 h-3" />
                            <span>{version.created_by}</span>
                          </div>
                        )}
                        {version.description && (
                          <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                            {version.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
