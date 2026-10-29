import React from 'react';
import {
  UploadCloud,
  FileCheck2,
  TableProperties,
  BarChart3,
  Sparkles,
  PieChart,
  HelpCircle,
  ClipboardCheck,
} from 'lucide-react';

export type NavTab =
  | 'upload'
  | 'quality'
  | 'explorer'
  | 'analytics'
  | 'recommendations'
  | 'visualizations'
  | 'investigate'
  | 'evaluations';

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  hasDataset: boolean;
  isParsed: boolean;
  recommendationsCount: number;
  acceptanceRate: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  hasDataset,
  isParsed,
  recommendationsCount,
  acceptanceRate,
}) => {
  const navItems = [
    {
      id: 'upload' as NavTab,
      label: 'Upload & Parse',
      description: 'Format detection & intake',
      icon: UploadCloud,
      enabled: true,
    },
    {
      id: 'quality' as NavTab,
      label: 'Data Quality',
      description: 'Parser validation & failures',
      icon: FileCheck2,
      enabled: isParsed,
    },
    {
      id: 'explorer' as NavTab,
      label: 'Log Explorer',
      description: 'Search, filter & raw lines',
      icon: TableProperties,
      enabled: isParsed,
    },
    {
      id: 'analytics' as NavTab,
      label: 'Analytics & KPIs',
      description: 'Metrics, spikes & services',
      icon: BarChart3,
      enabled: isParsed,
    },
    {
      id: 'recommendations' as NavTab,
      label: 'AI Recommendations',
      description: 'Intelligent chart proposals',
      icon: Sparkles,
      badge: recommendationsCount > 0 ? recommendationsCount.toString() : undefined,
      enabled: isParsed,
    },
    {
      id: 'visualizations' as NavTab,
      label: 'Interactive Charts',
      description: 'Recharts visual dashboard',
      icon: PieChart,
      enabled: isParsed,
    },
    {
      id: 'investigate' as NavTab,
      label: 'AI Investigation',
      description: 'SRE factual query analysis',
      icon: HelpCircle,
      enabled: isParsed,
    },
    {
      id: 'evaluations' as NavTab,
      label: 'Evaluation Tracking',
      description: 'User decisions & accuracy',
      icon: ClipboardCheck,
      badge: isParsed ? `${acceptanceRate}%` : undefined,
      enabled: isParsed,
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 min-h-[calc(100vh-61px)]">
      <div className="p-4 border-b border-slate-100">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Navigation Workflow
        </p>
      </div>

      <nav className="p-3 space-y-1 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          const isDisabled = !item.enabled;

          return (
            <button
              key={item.id}
              onClick={() => !isDisabled && onTabChange(item.id)}
              disabled={isDisabled}
              className={`w-full flex items-start space-x-3 px-3 py-2.5 rounded-lg text-left transition-all ${
                isActive
                  ? 'bg-indigo-50/80 text-indigo-900 font-semibold border border-indigo-100 shadow-2xs'
                  : isDisabled
                  ? 'opacity-40 cursor-not-allowed text-slate-400'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon
                className={`w-5 h-5 mt-0.5 shrink-0 ${
                  isActive ? 'text-indigo-600' : isDisabled ? 'text-slate-400' : 'text-slate-500'
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs truncate">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold font-mono ${
                        isActive
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 truncate">{item.description}</p>
              </div>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-100 bg-slate-50/60 text-[11px] text-slate-500">
        <p className="font-semibold text-slate-700">DVP College Project</p>
        <p className="text-[10px] text-slate-400 mt-0.5">
          AI-Assisted Log File Parser &amp; Visual Analytics
        </p>
      </div>
    </aside>
  );
};

