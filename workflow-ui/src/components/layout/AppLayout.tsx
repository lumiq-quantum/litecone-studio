import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import MobileSidebar from './MobileSidebar';
import Header from './Header';
import Breadcrumbs from './Breadcrumbs';
import PageTransition from './PageTransition';
import CommandPalette from './CommandPalette';

export default function AppLayout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <Sidebar />

      {/* Mobile Sidebar */}
      <MobileSidebar isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />

      {/* Command Palette */}
      <CommandPalette />

      {/* Main Content */}
      <div className="lg:pl-64">
        <Header onMenuClick={() => setIsMobileMenuOpen(true)} />

        <main className="p-4 lg:p-6">
          <Breadcrumbs />
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
