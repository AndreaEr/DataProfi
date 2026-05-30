import { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  Columns,
  Grid3x3,
  Zap,
  CircleDot,
  Sparkles,
  Clock,
  GitCompareArrows,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  MapPin,
  Database,
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import ColumnProfileView from './components/ColumnProfile';
import IndexRecommender from './components/IndexRecommender';
import MLReadinessView from './components/MLReadiness';
import BeforeAfter from './components/BeforeAfter';
import DataExplorer from './components/DataExplorer';
import TimeseriesView from './components/TimeseriesView';
import CorrelationView from './components/CorrelationView';
import GeoView from './components/GeoView';
import SchemaView from './components/SchemaView';
import Methodology from './components/Methodology';
import type { DatasetInfo } from './types';

type Tab = 'dashboard' | 'columns' | 'explorer' | 'timeseries' | 'correlations' | 'geo' | 'schema' | 'indexes' | 'ml' | 'clean' | 'methodology';

const NAV_ITEMS: { id: Tab; label: string; icon: LucideIcon }[] = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'columns', label: 'Columns', icon: Columns },
  { id: 'explorer', label: 'Explorer', icon: Grid3x3 },
  { id: 'timeseries', label: 'Temporal', icon: Clock },
  { id: 'correlations', label: 'Correlations', icon: GitCompareArrows },
  { id: 'geo', label: 'Spatial', icon: MapPin },
  { id: 'schema', label: 'Schema', icon: Database },
  { id: 'indexes', label: 'Indexes', icon: Zap },
  { id: 'ml', label: 'ML Readiness', icon: CircleDot },
  { id: 'clean', label: 'Cleaning', icon: Sparkles },
  { id: 'methodology', label: 'Methodology', icon: BookOpen },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleReset = () => {
    setDataset(null);
    setActiveTab('dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex flex-col bg-brand-900 transition-all duration-200 ${
          sidebarCollapsed ? 'w-[68px]' : 'w-[240px]'
        }`}
      >
        <div className="flex items-center gap-3 px-4 py-5 border-b border-brand-800">
          <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm font-bold">D</span>
          </div>
          {!sidebarCollapsed && (
            <div>
              <h1 className="text-base font-semibold text-white tracking-tight">DataProfi</h1>
              <p className="text-[10px] text-brand-300 leading-tight">Data Quality Platform</p>
            </div>
          )}
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {dataset &&
            NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`sidebar-link w-full ${
                    activeTab === item.id
                      ? 'bg-white/15 text-white'
                      : 'text-brand-300 hover:bg-white/10 hover:text-white'
                  }`}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon size={16} />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </button>
              );
            })}
          {!dataset && (
            <>
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`sidebar-link w-full ${
                  activeTab === 'dashboard'
                    ? 'bg-white/15 text-white'
                    : 'text-brand-300 hover:bg-white/10 hover:text-white'
                }`}
                title={sidebarCollapsed ? 'Overview' : undefined}
              >
                <LayoutDashboard size={16} />
                {!sidebarCollapsed && <span>Overview</span>}
              </button>
              <button
                onClick={() => setActiveTab('methodology')}
                className={`sidebar-link w-full ${
                  activeTab === 'methodology'
                    ? 'bg-white/15 text-white'
                    : 'text-brand-300 hover:bg-white/10 hover:text-white'
                }`}
                title={sidebarCollapsed ? 'Methodology' : undefined}
              >
                <BookOpen size={16} />
                {!sidebarCollapsed && <span>Methodology</span>}
              </button>
            </>
          )}
        </nav>

        <div className="px-3 py-3 border-t border-brand-800">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center py-2 rounded-lg text-brand-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>

      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-200 ${
          sidebarCollapsed ? 'ml-[68px]' : 'ml-[240px]'
        }`}
      >
        <header className="sticky top-0 z-20 bg-white border-b border-slate-200">
          <div className="flex items-center justify-between px-6 py-3.5">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-slate-800">
                {NAV_ITEMS.find((n) => n.id === activeTab)?.label || 'Overview'}
              </h2>
              {dataset && (
                <span className="badge bg-brand-50 text-brand-700 border border-brand-100">
                  {dataset.name}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {dataset && (
                <>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-50">
                      <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                      {dataset.rows.toLocaleString()} rows
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-50">
                      {dataset.columns} columns
                    </span>
                  </div>
                  <button onClick={handleReset} className="btn-secondary text-xs">
                    New Dataset
                  </button>
                </>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 p-6 max-w-[1200px] w-full mx-auto">
          {activeTab === 'dashboard' && (
            <Dashboard dataset={dataset} onDatasetLoaded={setDataset} />
          )}
          {activeTab === 'columns' && dataset && (
            <ColumnProfileView datasetId={dataset.id} />
          )}
          {activeTab === 'indexes' && dataset && (
            <IndexRecommender datasetId={dataset.id} />
          )}
          {activeTab === 'ml' && dataset && (
            <MLReadinessView datasetId={dataset.id} />
          )}
          {activeTab === 'clean' && dataset && (
            <BeforeAfter datasetId={dataset.id} />
          )}
          {activeTab === 'explorer' && dataset && (
            <DataExplorer datasetId={dataset.id} columns={dataset.column_names} />
          )}
          {activeTab === 'timeseries' && dataset && (
            <TimeseriesView datasetId={dataset.id} />
          )}
          {activeTab === 'correlations' && dataset && (
            <CorrelationView datasetId={dataset.id} />
          )}
          {activeTab === 'geo' && dataset && (
            <GeoView datasetId={dataset.id} />
          )}
          {activeTab === 'schema' && dataset && (
            <SchemaView datasetId={dataset.id} />
          )}
          {activeTab === 'methodology' && (
            <Methodology />
          )}
          {!dataset && activeTab !== 'dashboard' && activeTab !== 'methodology' && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-brand-50 flex items-center justify-center mx-auto mb-3">
                  <LayoutDashboard size={20} className="text-brand-500" />
                </div>
                <p className="text-sm text-slate-500">Load a dataset to get started</p>
              </div>
            </div>
          )}
        </main>

        <footer className="border-t border-slate-200/80 bg-white px-6 py-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>DataProfi v1.0.0</span>
            <span>Built by Andrea</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
