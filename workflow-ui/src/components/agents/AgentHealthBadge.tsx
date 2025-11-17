import { Activity, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentHealthResponse } from '@/types';

interface AgentHealthBadgeProps {
  health?: AgentHealthResponse;
  isLoading?: boolean;
  showResponseTime?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function AgentHealthBadge({
  health,
  isLoading = false,
  showResponseTime = false,
  size = 'md',
}: AgentHealthBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  if (isLoading) {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full font-medium bg-gray-100 text-gray-600',
          sizeClasses[size]
        )}
      >
        <Loader2 className={cn('animate-spin', iconSizes[size])} />
        Checking...
      </span>
    );
  }

  if (!health) {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full font-medium bg-gray-100 text-gray-500',
          sizeClasses[size]
        )}
      >
        <Activity className={iconSizes[size]} />
        Unknown
      </span>
    );
  }

  const isHealthy = health.status === 'healthy';

  return (
    <div className="inline-flex items-center gap-2">
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full font-medium',
          isHealthy
            ? 'bg-green-100 text-green-800'
            : 'bg-red-100 text-red-800',
          sizeClasses[size]
        )}
      >
        {isHealthy ? (
          <Activity className={iconSizes[size]} />
        ) : (
          <AlertCircle className={iconSizes[size]} />
        )}
        {isHealthy ? 'Healthy' : 'Unhealthy'}
      </span>
      {showResponseTime && health.response_time_ms !== undefined && (
        <span className="text-xs text-gray-500">
          {health.response_time_ms}ms
        </span>
      )}
    </div>
  );
}
