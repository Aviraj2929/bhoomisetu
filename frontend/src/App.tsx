import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { DashboardPage } from './components/DashboardPage';
import { VerificationWorkspace } from './components/VerificationWorkspace';
import { DigitizedRecordsPage } from './components/DigitizedRecordsPage';
import { DocumentUpload } from './components/DocumentUpload';
import { DashboardMetrics, DocumentVerificationTask } from './types';

import { API_BASE } from './config';

interface VerificationQueueItem {
  document_id: string;
  original_filename: string;
  status: string;
  overall_confidence: number;
  lowest_confidence_field: string;
  lowest_confidence: number;
}

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [verificationTask, setVerificationTask] = useState<DocumentVerificationTask | null>(null);
  const [verificationQueue, setVerificationQueue] = useState<VerificationQueueItem[]>([]);
  const [loadingTask, setLoadingTask] = useState(false);

  // ── Fetch live dashboard metrics ─────────────────────────────────────────
  const fetchMetrics = useCallback(() => {
    fetch(`${API_BASE}/analytics/metrics`)
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => {
        console.error('Dashboard metrics fetch failed:', err);
        // Only use zeros as fallback – do not show fake numbers
        setMetrics({
          total_documents: 0,
          auto_approved: 0,
          needs_verification: 0,
          human_verified: 0,
          auto_approval_rate: '0%',
          avg_processing_time_sec: 0,
          avg_field_confidence: 0,
          action_required: {
            pending_verifications: 0,
            validation_failures: 0,
            duplicate_suspects: 0,
          },
        });
      });
  }, []);

  // ── Fetch verification queue from backend ─────────────────────────────────
  const fetchVerificationQueue = useCallback(() => {
    fetch(`${API_BASE}/verification/tasks`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setVerificationQueue(data);
        }
      })
      .catch(err => console.error('Verification queue fetch failed:', err));
  }, []);

  useEffect(() => {
    fetchMetrics();
    fetchVerificationQueue();
  }, [fetchMetrics, fetchVerificationQueue]);

  // ── Load a specific verification task ────────────────────────────────────
  const loadVerificationTask = useCallback(async (documentId: string, filename: string, overallConf: number) => {
    setLoadingTask(true);
    setVerificationTask(null);

    try {
      const res = await fetch(`${API_BASE}/verification/records/${documentId}/verification`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const task: DocumentVerificationTask = {
        document_id: documentId,
        filename: filename,
        status: data.status,
        overall_confidence: data.overall_confidence ?? overallConf,
        image_url: '',    // Could be extended to serve the stored image
        fields: (data.fields || []).map((f: any) => ({
          field_id: f.field_id,
          field_name: f.field_name,
          raw_value: f.value ?? '',
          normalized_value: f.normalized_value ?? f.value ?? '',
          confidence: f.confidence ?? 0,
          source_bbox: f.source_bbox ?? [0, 0, 0, 0],
          source_page: f.source_page ?? 1,
          is_verified: f.is_verified ?? false,
          warning: f.confidence < 0.75
            ? `Low confidence (${Math.round(f.confidence * 100)}%) – please verify`
            : null,
        })),
      };

      setVerificationTask(task);
      setActiveTab('verification');
    } catch (err) {
      console.error('Failed to load verification task:', err);
      alert(`Could not load verification details for document ${documentId}. Is the backend running?`);
    } finally {
      setLoadingTask(false);
    }
  }, []);

  // ── Open the first pending task from the queue ────────────────────────────
  const openNextVerificationTask = useCallback(() => {
    if (verificationQueue.length === 0) {
      alert('No documents are currently in the verification queue.');
      return;
    }
    const first = verificationQueue[0];
    loadVerificationTask(first.document_id, first.original_filename, first.overall_confidence);
  }, [verificationQueue, loadVerificationTask]);

  const handleUploadSuccess = useCallback(() => {
    fetchMetrics();
    fetchVerificationQueue();
  }, [fetchMetrics, fetchVerificationQueue]);

  const handleVerificationComplete = useCallback(() => {
    fetchMetrics();
    fetchVerificationQueue();
    setVerificationTask(null);
    setActiveTab('dashboard');
  }, [fetchMetrics, fetchVerificationQueue]);

  return (
    <div className="min-h-screen bg-paper text-ink flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main id="main-content" className="flex-1 p-4 md:p-6 space-y-6">
        {activeTab === 'dashboard' && (
          <>
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />

            {/* Verification queue summary */}
            {verificationQueue.length > 0 && (
              <div className="max-w-7xl mx-auto">
                <div className="bg-amber-50 border border-saffron border-l-8 p-4 flex flex-wrap items-center justify-between gap-3" role="status">
                  <div>
                    <p className="text-sm font-semibold text-warn">
                      {verificationQueue.length} document{verificationQueue.length > 1 ? 's' : ''} pending verification
                    </p>
                    <p className="text-sm text-ink mt-0.5">
                      Most urgent: <strong>{verificationQueue[0].original_filename}</strong>
                      {' '}– lowest confidence field: <strong>{verificationQueue[0].lowest_confidence_field}</strong>
                      {' '}({Math.round(verificationQueue[0].lowest_confidence * 100)}%)
                    </p>
                  </div>
                  <button onClick={openNextVerificationTask} disabled={loadingTask} className="gov-btn">
                    {loadingTask ? 'Loading...' : 'Open most urgent task'}
                  </button>
                </div>
              </div>
            )}

            {metrics && (
              <DashboardPage
                metrics={metrics}
                onOpenVerification={openNextVerificationTask}
                verificationQueue={verificationQueue}
                onLoadTask={loadVerificationTask}
              />
            )}
          </>
        )}

        {activeTab === 'verification' && verificationTask && (
          <VerificationWorkspace task={verificationTask} onSaveCorrections={handleVerificationComplete} />
        )}

        {activeTab === 'verification' && !verificationTask && !loadingTask && (
          <div className="max-w-2xl mx-auto gov-card p-8 text-center space-y-3">
            <p className="text-lg font-semibold text-navy">No verification task selected</p>
            <p className="text-sm">Upload a document, or open a task from the queue on the Dashboard.</p>
            <button onClick={() => setActiveTab('dashboard')} className="gov-btn-alt">Back to Dashboard</button>
          </div>
        )}

        {activeTab === 'verification' && loadingTask && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-3">
              <div className="w-8 h-8 border-4 border-navy border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm">Loading verification task...</p>
            </div>
          </div>
        )}

        {activeTab === 'records' && <DigitizedRecordsPage />}
      </main>

      <Footer />
    </div>
  );
};

export default App;
