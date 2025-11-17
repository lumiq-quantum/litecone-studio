import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import AppLayout from './components/layout/AppLayout';
import LoadingSpinner from './components/common/LoadingSpinner';

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AgentsList = lazy(() => import('./pages/agents/AgentsList'));
const AgentDetail = lazy(() => import('./pages/agents/AgentDetail'));
const WorkflowsList = lazy(() => import('./pages/workflows/WorkflowsList'));
const WorkflowDetail = lazy(() => import('./pages/workflows/WorkflowDetail'));
const WorkflowCreate = lazy(() => import('./pages/workflows/WorkflowCreate'));
const WorkflowEdit = lazy(() => import('./pages/workflows/WorkflowEdit'));
const RunsList = lazy(() => import('./pages/runs/RunsList'));
const RunDetail = lazy(() => import('./pages/runs/RunDetail'));
const Help = lazy(() => import('./pages/Help'));
const NotFound = lazy(() => import('./pages/NotFound'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* Main layout routes */}
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            
            {/* Agent routes */}
            <Route path="agents" element={<AgentsList />} />
            <Route path="agents/:id" element={<AgentDetail />} />
            
            {/* Workflow routes */}
            <Route path="workflows" element={<WorkflowsList />} />
            <Route path="workflows/create" element={<WorkflowCreate />} />
            <Route path="workflows/:id" element={<WorkflowDetail />} />
            <Route path="workflows/:id/edit" element={<WorkflowEdit />} />
            
            {/* Run routes */}
            <Route path="runs" element={<RunsList />} />
            <Route path="runs/:id" element={<RunDetail />} />
            
            {/* Help route */}
            <Route path="help" element={<Help />} />
          </Route>

          {/* 404 Not Found */}
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
