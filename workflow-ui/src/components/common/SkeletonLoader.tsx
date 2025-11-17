import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { shimmerVariants } from '@/lib/animations';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

/**
 * Base skeleton component with shimmer animation
 */
export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  animate = true,
}: SkeletonProps) {
  const baseClasses = 'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%]';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  if (animate) {
    return (
      <motion.div
        className={cn(baseClasses, variantClasses[variant], className)}
        style={style}
        variants={shimmerVariants}
        animate="animate"
      />
    );
  }

  return (
    <div
      className={cn(baseClasses, variantClasses[variant], className)}
      style={style}
    />
  );
}

/**
 * Card skeleton loader
 */
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" height={20} />
          <Skeleton variant="text" width="40%" height={16} />
        </div>
        <Skeleton variant="circular" width={40} height={40} />
      </div>
      
      <div className="space-y-2">
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="80%" />
      </div>
      
      <div className="flex gap-2 pt-2">
        <Skeleton variant="rectangular" width={80} height={32} />
        <Skeleton variant="rectangular" width={80} height={32} />
        <Skeleton variant="rectangular" width={80} height={32} />
      </div>
    </div>
  );
}

/**
 * Agent card skeleton
 */
export function AgentCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3 flex-1">
          <Skeleton variant="circular" width={48} height={48} />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="70%" height={20} />
            <Skeleton variant="text" width="50%" height={14} />
          </div>
        </div>
        <Skeleton variant="rectangular" width={60} height={24} className="rounded-full" />
      </div>
      
      <Skeleton variant="text" width="100%" />
      <Skeleton variant="text" width="90%" />
      
      <div className="flex items-center gap-4 pt-2">
        <Skeleton variant="text" width={100} height={14} />
        <Skeleton variant="text" width={100} height={14} />
      </div>
      
      <div className="flex gap-2 pt-2 border-t border-gray-100">
        <Skeleton variant="rectangular" width={70} height={32} />
        <Skeleton variant="rectangular" width={70} height={32} />
        <Skeleton variant="rectangular" width={100} height={32} />
      </div>
    </div>
  );
}

/**
 * Workflow card skeleton
 */
export function WorkflowCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="65%" height={20} />
          <Skeleton variant="text" width="45%" height={14} />
        </div>
        <Skeleton variant="rectangular" width={50} height={24} className="rounded-full" />
      </div>
      
      <div className="space-y-2">
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="85%" />
      </div>
      
      <div className="flex items-center gap-4 pt-2">
        <Skeleton variant="text" width={80} height={14} />
        <Skeleton variant="text" width={80} height={14} />
      </div>
      
      <div className="flex gap-2 pt-2 border-t border-gray-100">
        <Skeleton variant="rectangular" width={60} height={32} />
        <Skeleton variant="rectangular" width={60} height={32} />
        <Skeleton variant="rectangular" width={80} height={32} />
        <Skeleton variant="rectangular" width={70} height={32} />
      </div>
    </div>
  );
}

/**
 * Run card skeleton
 */
export function RunCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="50%" height={16} />
          <Skeleton variant="text" width="70%" height={20} />
        </div>
        <Skeleton variant="rectangular" width={80} height={28} className="rounded-full" />
      </div>
      
      <div className="grid grid-cols-2 gap-4 pt-2">
        <div className="space-y-1">
          <Skeleton variant="text" width={60} height={12} />
          <Skeleton variant="text" width="90%" height={14} />
        </div>
        <div className="space-y-1">
          <Skeleton variant="text" width={60} height={12} />
          <Skeleton variant="text" width="80%" height={14} />
        </div>
      </div>
      
      <div className="flex gap-2 pt-2 border-t border-gray-100">
        <Skeleton variant="rectangular" width={70} height={32} />
        <Skeleton variant="rectangular" width={70} height={32} />
      </div>
    </div>
  );
}

/**
 * Table row skeleton
 */
export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <div className="flex items-center gap-4 p-4 border-b border-gray-200">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === 0 ? '25%' : i === columns - 1 ? '15%' : '20%'}
          height={16}
        />
      ))}
    </div>
  );
}

/**
 * List skeleton with multiple items
 */
export function ListSkeleton({
  count = 6,
  type = 'card',
}: {
  count?: number;
  type?: 'card' | 'agent' | 'workflow' | 'run' | 'table';
}) {
  const SkeletonComponent = {
    card: CardSkeleton,
    agent: AgentCardSkeleton,
    workflow: WorkflowCardSkeleton,
    run: RunCardSkeleton,
    table: TableRowSkeleton,
  }[type];

  if (type === 'table') {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {Array.from({ length: count }).map((_, i) => (
          <TableRowSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonComponent key={i} />
      ))}
    </div>
  );
}

/**
 * Detail page skeleton
 */
export function DetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <Skeleton variant="text" width="40%" height={32} />
        <Skeleton variant="text" width="60%" height={16} />
      </div>

      {/* Content sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <Skeleton variant="text" width="30%" height={20} />
            <Skeleton variant="rectangular" height={200} />
          </div>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <Skeleton variant="text" width="30%" height={20} />
            <div className="space-y-2">
              <Skeleton variant="text" width="100%" />
              <Skeleton variant="text" width="95%" />
              <Skeleton variant="text" width="90%" />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
            <Skeleton variant="text" width="50%" height={20} />
            <div className="space-y-3">
              <Skeleton variant="text" width="100%" />
              <Skeleton variant="text" width="100%" />
              <Skeleton variant="text" width="100%" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Dashboard stat card skeleton
 */
export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton variant="text" width="50%" height={16} />
        <Skeleton variant="circular" width={40} height={40} />
      </div>
      <Skeleton variant="text" width="40%" height={32} />
      <Skeleton variant="text" width="60%" height={14} />
    </div>
  );
}
