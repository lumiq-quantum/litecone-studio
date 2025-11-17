import { motion } from 'framer-motion';
import {
  Clock,
  Loader2,
  CheckCircle2,
  XCircle,
  Ban,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { pulseVariants } from '@/lib/animations';
import type { RunStatus } from '@/types';

interface RunStatusBadgeProps {
  status: RunStatus;
  className?: string;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

interface StatusConfig {
  label: string;
  icon: LucideIcon;
  bgColor: string;
  textColor: string;
  borderColor: string;
  iconColor: string;
}

const statusConfigs: Record<RunStatus, StatusConfig> = {
  PENDING: {
    label: 'Pending',
    icon: Clock,
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-200',
    iconColor: 'text-yellow-600',
  },
  RUNNING: {
    label: 'Running',
    icon: Loader2,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-600',
  },
  COMPLETED: {
    label: 'Completed',
    icon: CheckCircle2,
    bgColor: 'bg-green-50',
    textColor: 'text-green-800',
    borderColor: 'border-green-200',
    iconColor: 'text-green-600',
  },
  FAILED: {
    label: 'Failed',
    icon: XCircle,
    bgColor: 'bg-red-50',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
    iconColor: 'text-red-600',
  },
  CANCELLED: {
    label: 'Cancelled',
    icon: Ban,
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-800',
    borderColor: 'border-gray-200',
    iconColor: 'text-gray-600',
  },
};

const sizeClasses = {
  sm: {
    badge: 'px-2 py-0.5 text-xs',
    icon: 'w-3 h-3',
  },
  md: {
    badge: 'px-2.5 py-1 text-sm',
    icon: 'w-4 h-4',
  },
  lg: {
    badge: 'px-3 py-1.5 text-base',
    icon: 'w-5 h-5',
  },
};

export default function RunStatusBadge({
  status,
  className,
  showIcon = true,
  size = 'md',
}: RunStatusBadgeProps) {
  const config = statusConfigs[status];
  const Icon = config.icon;
  const sizes = sizeClasses[size];

  return (
    <motion.span
      variants={pulseVariants}
      initial="initial"
      animate={status === 'RUNNING' ? 'pulse' : 'initial'}
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full border',
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizes.badge,
        className
      )}
    >
      {showIcon && (
        <Icon
          className={cn(
            sizes.icon,
            config.iconColor,
            status === 'RUNNING' && 'animate-spin'
          )}
        />
      )}
      <span>{config.label}</span>
    </motion.span>
  );
}
