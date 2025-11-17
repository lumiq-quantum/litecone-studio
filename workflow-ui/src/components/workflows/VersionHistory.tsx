import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  GitBranch,
  Calendar,
  User,
  Eye,
  Play,
  GitCompare,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import VersionCompare from './VersionCompare';
import ExecuteWorkflowDialog from './ExecuteWorkflowDialog';
import { showToast } from '@/lib/toast';
import { cn } from '@/lib/utils';
import type { WorkflowResponse } from '@/types';

interface VersionHistoryProps {
  versions: WorkflowResponse[];
  currentVersion: number;
  onViewVersion?: (version: WorkflowResponse) => void;
  className?: string;
}

export default function VersionHistory({
  versions,
  currentVersion,
  onViewVersion,
  className = '',
}: VersionHistoryProps) {
  const navigate = useNavigate();
  const [compareVersions, setCompareVersions] = useState<{
    original: WorkflowResponse;
    modified: WorkflowResponse;
  } | null>(null);
  const [executeVersion, setExecuteVersion] = useState<WorkflowResponse | null>(null);

  // Sort versions in descending order (newest first)
  const sortedVersions = [...versions].sort((a, b) => b.version - a.version);

  const handleView = (version: WorkflowResponse) => {
    if (onViewVersion) {
      onViewVersion(version);
    } else {
      // Navigate to workflow detail with version parameter
      navigate(`/workflows/${version.id}`);
    }
  };

  const handleCompare = (version: WorkflowResponse) => {
    // Find the previous version to compare with
    const versionIndex = sortedVersions.findIndex((v) => v.version === version.version);
    if (versionIndex < sortedVersions.length - 1) {
      const previousVersion = sortedVersions[versionIndex + 1];
      setCompareVersions({
        original: previousVersion,
        modified: version,
      });
    } else {
      showToast.error('No previous version to compare with');
    }
  };

  const handleExecute = (version: WorkflowResponse) => {
    if (version.status !== 'active') {
      showToast.error('Only active workflows can be executed');
      return;
    }
    setExecuteVersion(version);
  };

  const formatDuration = (date: string) => {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMins > 0) {
      return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  if (sortedVersions.length === 0) {
    return (
      <div className={cn('bg-white rounded-xl border border-gray-200 p-8', className)}>
        <div className="text-center">
          <GitBranch className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-lg font-medium text-gray-900 mb-1">No Version History</p>
          <p className="text-sm text-gray-600">
            Version history will appear here as you make changes to the workflow
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={cn('bg-white rounded-xl border border-gray-200', className)}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Version History</h3>
              <p className="text-sm text-gray-600">
                {sortedVersions.length} version{sortedVersions.length !== 1 ? 's' : ''} available
              </p>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="p-6">
          <div className="space-y-4">
            {sortedVersions.map((version, index) => {
              const isCurrent = version.version === currentVersion;
              const isLatest = index === 0;
              const isActive = version.status === 'active';

              return (
                <motion.div
                  key={version.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative"
                >
                  {/* Timeline Line */}
                  {index < sortedVersions.length - 1 && (
                    <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-gray-200" />
                  )}

                  {/* Version Card */}
                  <div
                    className={cn(
                      'relative flex gap-4 p-4 rounded-lg border-2 transition-all',
                      isCurrent
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                    )}
                  >
                    {/* Version Indicator */}
                    <div className="flex-shrink-0">
                      <div
                        className={cn(
                          'w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm',
                          isCurrent
                            ? 'bg-green-500 text-white'
                            : isLatest
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 text-gray-700'
                        )}
                      >
                        {isCurrent ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : (
                          `v${version.version}`
                        )}
                      </div>
                    </div>

                    {/* Version Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-base font-semibold text-gray-900">
                              Version {version.version}
                            </h4>
                            {isCurrent && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Current
                              </span>
                            )}
                            {isLatest && !isCurrent && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                Latest
                              </span>
                            )}
                            {!isActive && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                                Inactive
                              </span>
                            )}
                          </div>
                          {version.description && (
                            <p className="text-sm text-gray-700 mb-2">{version.description}</p>
                          )}
                        </div>
                      </div>

                      {/* Metadata */}
                      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600 mb-3">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{formatDuration(version.created_at)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>{new Date(version.created_at).toLocaleString()}</span>
                        </div>
                        {version.created_by && (
                          <div className="flex items-center gap-1.5">
                            <User className="w-3.5 h-3.5" />
                            <span>{version.created_by}</span>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleView(version)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          View
                        </button>
                        <button
                          onClick={() => handleExecute(version)}
                          disabled={!isActive}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Play className="w-3.5 h-3.5" />
                          Execute
                        </button>
                        {index < sortedVersions.length - 1 && (
                          <button
                            onClick={() => handleCompare(version)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-md transition-colors"
                          >
                            <GitCompare className="w-3.5 h-3.5" />
                            Compare
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Version Compare Dialog */}
      {compareVersions && (
        <VersionCompare
          isOpen={!!compareVersions}
          onClose={() => setCompareVersions(null)}
          originalVersion={compareVersions.original}
          modifiedVersion={compareVersions.modified}
        />
      )}

      {/* Execute Workflow Dialog */}
      {executeVersion && (
        <ExecuteWorkflowDialog
          isOpen={!!executeVersion}
          onClose={() => setExecuteVersion(null)}
          workflow={executeVersion}
        />
      )}
    </>
  );
}
