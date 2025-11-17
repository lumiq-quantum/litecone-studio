import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Generate breadcrumb items from path
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', href: '/' },
  ];

  let currentPath = '';
  pathnames.forEach((segment, index) => {
    currentPath += `/${segment}`;
    
    // Format the segment for display
    let label = segment.charAt(0).toUpperCase() + segment.slice(1);
    
    // Replace hyphens with spaces
    label = label.replace(/-/g, ' ');
    
    // Don't make the last item a link
    const isLast = index === pathnames.length - 1;
    
    breadcrumbs.push({
      label,
      href: isLast ? undefined : currentPath,
    });
  });

  // Don't show breadcrumbs on home page
  if (pathnames.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-2 text-sm">
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          const isFirst = index === 0;

          return (
            <li key={crumb.href || crumb.label} className="flex items-center gap-2">
              {index > 0 && (
                <ChevronRight className="w-4 h-4 text-gray-400" aria-hidden="true" />
              )}
              
              {crumb.href ? (
                <Link
                  to={crumb.href}
                  className={cn(
                    'flex items-center gap-1 hover:text-blue-600 transition-colors',
                    isFirst ? 'text-gray-600' : 'text-gray-500'
                  )}
                >
                  {isFirst && <Home className="w-4 h-4" />}
                  {crumb.label}
                </Link>
              ) : (
                <span
                  className={cn(
                    'flex items-center gap-1',
                    isLast ? 'text-gray-900 font-medium' : 'text-gray-500'
                  )}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {isFirst && <Home className="w-4 h-4" />}
                  {crumb.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
