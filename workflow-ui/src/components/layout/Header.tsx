import { Menu } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>

        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-2">
          <span className="text-lg font-bold text-gray-900">
            {import.meta.env.VITE_APP_NAME || 'Workflow Manager'}
          </span>
        </div>

        {/* Right side actions - placeholder for future features */}
        <div className="flex items-center gap-2">
          {/* Future: User menu, notifications, etc. */}
        </div>
      </div>
    </header>
  );
}
