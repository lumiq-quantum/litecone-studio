/**
 * Mini chart components for dashboard visualizations
 */
import { motion } from 'framer-motion';

interface SuccessRateChartProps {
  successRate: number;
}

export function SuccessRateChart({ successRate }: SuccessRateChartProps) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (successRate / 100) * circumference;

  return (
    <div className="flex items-center justify-center">
      <div className="relative w-24 h-24">
        <svg className="transform -rotate-90 w-24 h-24">
          {/* Background circle */}
          <circle
            cx="48"
            cy="48"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-gray-200"
          />
          {/* Progress circle */}
          <motion.circle
            cx="48"
            cy="48"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
            strokeLinecap="round"
            className={successRate >= 80 ? 'text-green-500' : successRate >= 50 ? 'text-yellow-500' : 'text-red-500'}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold text-gray-900">{successRate}%</span>
        </div>
      </div>
    </div>
  );
}

interface StatusDistributionChartProps {
  data: {
    completed: number;
    failed: number;
    running: number;
    pending: number;
  };
}

export function StatusDistributionChart({ data }: StatusDistributionChartProps) {
  const total = data.completed + data.failed + data.running + data.pending;
  
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    );
  }

  const completedPercent = (data.completed / total) * 100;
  const failedPercent = (data.failed / total) * 100;
  const runningPercent = (data.running / total) * 100;
  const pendingPercent = (data.pending / total) * 100;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-gray-600">Completed</span>
        </div>
        <span className="font-medium text-gray-900">{data.completed}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <motion.div
          className="bg-green-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${completedPercent}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-gray-600">Failed</span>
        </div>
        <span className="font-medium text-gray-900">{data.failed}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <motion.div
          className="bg-red-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${failedPercent}%` }}
          transition={{ duration: 0.5, delay: 0.1 }}
        />
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-gray-600">Running</span>
        </div>
        <span className="font-medium text-gray-900">{data.running}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <motion.div
          className="bg-blue-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${runningPercent}%` }}
          transition={{ duration: 0.5, delay: 0.2 }}
        />
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <span className="text-gray-600">Pending</span>
        </div>
        <span className="font-medium text-gray-900">{data.pending}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <motion.div
          className="bg-yellow-500 h-2 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pendingPercent}%` }}
          transition={{ duration: 0.5, delay: 0.3 }}
        />
      </div>
    </div>
  );
}
