import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { LogUploader } from './components/upload/LogUploader';
import { DataQualityView } from './components/upload/DataQualityView';
import { LogExplorer } from './components/explorer/LogExplorer';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { RecommendationsView } from './components/recommendations/RecommendationsView';
import { VisualizationsDashboard } from './components/visualizations/VisualizationsDashboard';
import { InvestigationView } from './components/investigate/InvestigationView';
import { EvaluationReportView } from './components/recommendations/EvaluationReportView';
import { ExportModal } from './components/export/ExportModal';
import { ProjectSynopsisModal } from './components/info/ProjectSynopsisModal';

import {
  DatasetProfile,
  LogAnalytics,
  ChartRecommendation,
  EvaluationSummary,
  UploadResponse,
} from './types';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('upload');
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [analytics, setAnalytics] = useState<LogAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<ChartRecommendation[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationSummary>({
    total_recommendations: 0,
    accepted_count: 0,
    rejected_count: 0,
    modified_count: 0,
    acceptance_rate: 0,
    evaluations: [],
  });

  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isSynopsisOpen, setIsSynopsisOpen] = useState(false);

  // Check health on mount
  useEffect(() => {
    apiClient
      .checkHealth()
      .then(() => setIsBackendHealthy(true))
      .catch(() => setIsBackendHealthy(false));
  }, []);

  const handleUploadSuccess = (data: UploadResponse) => {
    setUploadData(data);
    // Reset parsed state for new upload
    setProfile(null);
    setAnalytics(null);
    setRecommendations([]);
    setEvaluations({
      total_recommendations: 0,
      accepted_count: 0,
      rejected_count: 0,
      modified_count: 0,
      acceptance_rate: 0,
      evaluations: [],
    });
    setCurrentTab('upload');
  };

  const handleParseComplete = async (result: any) => {
    if (!uploadData) return;
    setIsParsing(true);
    try {
      const datasetId = uploadData.dataset_id;

      // 1. Fetch profile
      const prof = await apiClient.getProfile(datasetId);
      setProfile(prof);

      // 2. Fetch analytics
      const anal = await apiClient.getAnalytics(datasetId);
      setAnalytics(anal);

      // 3. Fetch AI recommendations
      const recs = await apiClient.getRecommendations(datasetId);
      setRecommendations(recs);

      // 4. Fetch evaluations
      const evals = await apiClient.getEvaluations(datasetId);
      setEvaluations(evals);

      // Transition to quality tab to review parsing outcome
      setCurrentTab('quality');
    } catch (err) {
      console.error(err);
    } finally {
      setIsParsing(false);
    }
  };

  const availableServices = analytics ? analytics.service_stats.map((s) => s.service) : [];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      <Header
        profile={profile}
        onOpenExport={() => setIsExportModalOpen(true)}
        onOpenSynopsis={() => setIsSynopsisOpen(true)}
        isBackendHealthy={isBackendHealthy}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          currentTab={currentTab}
          onTabChange={setCurrentTab}
          hasDataset={uploadData !== null}
          isParsed={profile !== null}
          recommendationsCount={recommendations.length}
          acceptanceRate={evaluations.acceptance_rate}
        />

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {currentTab === 'upload' && (
            <LogUploader
              uploadData={uploadData}
              onUploadSuccess={handleUploadSuccess}
              onParseComplete={handleParseComplete}
              isParsing={isParsing}
            />
          )}

          {currentTab === 'quality' && profile && (
            <DataQualityView profile={profile} datasetId={profile.dataset_id} />
          )}

          {currentTab === 'explorer' && profile && (
            <LogExplorer
              datasetId={profile.dataset_id}
              availableServices={availableServices}
            />
          )}

          {currentTab === 'analytics' && analytics && (
            <AnalyticsView analytics={analytics} />
          )}

          {currentTab === 'recommendations' && profile && (
            <RecommendationsView
              datasetId={profile.dataset_id}
              recommendations={recommendations}
              evaluations={evaluations}
              onEvaluationUpdated={setEvaluations}
              onNavigateToChart={() => setCurrentTab('visualizations')}
            />
          )}

          {currentTab === 'visualizations' && analytics && profile && (
            <VisualizationsDashboard
              analytics={analytics}
              profile={profile}
              availableServices={availableServices}
            />
          )}

          {currentTab === 'investigate' && profile && (
            <InvestigationView datasetId={profile.dataset_id} />
          )}

          {currentTab === 'evaluations' && profile && (
            <EvaluationReportView
              evaluations={evaluations}
              recommendations={recommendations}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      {isExportModalOpen && profile && (
        <ExportModal
          datasetId={profile.dataset_id}
          filename={profile.filename}
          onClose={() => setIsExportModalOpen(false)}
        />
      )}

      {isSynopsisOpen && (
        <ProjectSynopsisModal onClose={() => setIsSynopsisOpen(false)} />
      )}
    </div>
  );
};

export default App;

