import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, LayoutDashboard, Users, Workflow, PlayCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Command {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
  keywords?: string[];
}

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const commands: Command[] = [
    {
      id: 'dashboard',
      label: 'Go to Dashboard',
      icon: LayoutDashboard,
      action: () => navigate('/'),
      keywords: ['home', 'dashboard'],
    },
    {
      id: 'agents',
      label: 'Go to Agents',
      icon: Users,
      action: () => navigate('/agents'),
      keywords: ['agents', 'services'],
    },
    {
      id: 'workflows',
      label: 'Go to Workflows',
      icon: Workflow,
      action: () => navigate('/workflows'),
      keywords: ['workflows', 'definitions'],
    },
    {
      id: 'runs',
      label: 'Go to Runs',
      icon: PlayCircle,
      action: () => navigate('/runs'),
      keywords: ['runs', 'executions', 'history'],
    },
    {
      id: 'create-workflow',
      label: 'Create New Workflow',
      icon: Workflow,
      action: () => navigate('/workflows/new'),
      keywords: ['create', 'new', 'workflow'],
    },
  ];

  const filteredCommands = commands.filter((command) => {
    const searchLower = search.toLowerCase();
    return (
      command.label.toLowerCase().includes(searchLower) ||
      command.keywords?.some((keyword) => keyword.includes(searchLower))
    );
  });

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setIsOpen((prev) => !prev);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const executeCommand = (command: Command) => {
    command.action();
    setIsOpen(false);
    setSearch('');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Command Palette */}
          <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] px-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="w-full max-w-lg bg-white rounded-lg shadow-2xl overflow-hidden"
            >
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
                <Search className="w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search commands..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="flex-1 outline-none text-gray-900 placeholder-gray-400"
                  autoFocus
                />
                <kbd className="px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 rounded">
                  ESC
                </kbd>
              </div>

              {/* Commands List */}
              <div className="max-h-96 overflow-y-auto">
                {filteredCommands.length > 0 ? (
                  <div className="py-2">
                    {filteredCommands.map((command) => (
                      <button
                        key={command.id}
                        onClick={() => executeCommand(command)}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
                      >
                        <command.icon className="w-5 h-5 text-gray-400" />
                        <span className="text-sm text-gray-900">{command.label}</span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-gray-500">
                    <p className="text-sm">No commands found</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Navigate with arrow keys</span>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2 py-1 font-semibold bg-white border border-gray-200 rounded">
                      ⌘K
                    </kbd>
                    <span>to toggle</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
