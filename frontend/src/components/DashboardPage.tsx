import React from 'react';
import { FileText, CheckCircle, AlertTriangle, Clock, Activity, XCircle, Loader2, Users } from 'lucide-react';
import { DashboardMetrics } from '../types';

interface VerificationQueueItem {
  document_id: string;
  original_filename: string;
  status: string;
  overall_confidence: number;
  lowest_confidence_field: string;
  lowest_confidence: number;
}

interface DashboardProps {
  metrics: DashboardMetrics;
  onOpenVerification: () => void;
  verificationQueue?: VerificationQueueItem[];
  onLoadTask?: (documentId: string, filename: string, conf: number) => void;
}

const ConfidenceBadge: React.FC<{ value: number }> = ({ value }) => {
  const pct = Math.round(value * 100);
  const color = pct >= 85 ? 'text-india-green' : pct >= 65 ? 'text-warn' : 'text-alert';
  return <span className={`font-bold ${color}`}>{pct}%</span>;
};

export const DashboardPage: React.FC<DashboardProps> = ({
  metrics,
  onOpenVerification,
  verificationQueue = [],
  onLoadTask,
}) => {
  const avgProcessing = metrics.avg_processing_time_sec
    ? `${metrics.avg_processing_time_sec}s`
    : '—';

  const Kpi: React.FC<{ label: string; value: React.ReactNode; note: string; icon: React.ReactNode; accent?: string }> = ({ label, value, note, icon, accent = 'border-t-navy' }) => (
    <div className={`gov-card border-t-4 ${accent} p-4`}>
      <div className="flex items-center justify-between text-navy mb-2">
        <span className="text-sm font-semibold">{label}</span>
        {icon}
      </div>
      <p className="text-3xl font-bold text-ink">{value}</p>
      <span className="text-xs text-gray-600">{note}</span>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-navy border-b-2 border-saffron pb-1 inline-block">Dashboard Overview</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Total Documents" value={metrics.total_documents} note="Uploaded and tracked" icon={<FileText size={18} />} />
        <Kpi label="Auto-Approved" value={metrics.auto_approval_rate} note={`${metrics.auto_approved} documents`} icon={<CheckCircle size={18} className="text-india-green" />} accent="border-t-india-green" />
        <Kpi
          label="Avg Field Confidence"
          value={metrics.avg_field_confidence > 0 ? `${(metrics.avg_field_confidence * 100).toFixed(1)}%` : '—'}
          note="Across all extracted fields"
          icon={<Activity size={18} />}
        />
        <Kpi label="Avg Processing Time" value={avgProcessing} note="Per document" icon={<Clock size={18} />} accent="border-t-saffron" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="gov-card border-l-4 border-l-saffron p-4">
          <div className="flex items-center gap-2 mb-1 text-warn">
            <AlertTriangle size={18} />
            <span className="text-sm font-semibold">Pending Verification</span>
          </div>
          <p className="text-2xl font-bold text-ink">{metrics.action_required.pending_verifications}</p>
          {metrics.action_required.pending_verifications > 0 && (
            <button onClick={onOpenVerification} className="mt-2 text-sm text-navy underline hover:text-navy-dark">
              Open queue
            </button>
          )}
        </div>

        <div className="gov-card border-l-4 border-l-alert p-4">
          <div className="flex items-center gap-2 mb-1 text-alert">
            <XCircle size={18} />
            <span className="text-sm font-semibold">Failed Processing</span>
          </div>
          <p className="text-2xl font-bold text-ink">{metrics.action_required.validation_failures}</p>
        </div>

        <div className="gov-card border-l-4 border-l-india-green p-4">
          <div className="flex items-center gap-2 mb-1 text-india-green">
            <Users size={18} />
            <span className="text-sm font-semibold">Human Verified</span>
          </div>
          <p className="text-2xl font-bold text-ink">{metrics.human_verified}</p>
        </div>
      </div>

      {verificationQueue.length > 0 && (
        <div className="gov-card overflow-x-auto">
          <div className="gov-card-title flex items-center justify-between">
            <h3>Verification Queue</h3>
            <span className="bg-saffron text-ink text-xs font-bold px-2 py-0.5">{verificationQueue.length} pending</span>
          </div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                <th className="gov-th">S.No.</th>
                <th className="gov-th">Filename</th>
                <th className="gov-th">Status</th>
                <th className="gov-th">Confidence</th>
                <th className="gov-th">Weakest Field</th>
                <th className="gov-th text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {verificationQueue.map((item, i) => (
                <tr key={item.document_id} className="odd:bg-white even:bg-paper">
                  <td className="gov-td">{i + 1}</td>
                  <td className="gov-td font-semibold">{item.original_filename}</td>
                  <td className="gov-td">
                    <span className="bg-amber-100 text-warn border border-saffron px-2 py-0.5 text-xs font-semibold">{item.status}</span>
                  </td>
                  <td className="gov-td"><ConfidenceBadge value={item.overall_confidence} /></td>
                  <td className="gov-td">
                    {item.lowest_confidence_field}{' '}
                    <span className="text-alert">({Math.round(item.lowest_confidence * 100)}%)</span>
                  </td>
                  <td className="gov-td text-right">
                    <button onClick={() => onLoadTask?.(item.document_id, item.original_filename, item.overall_confidence)} className="gov-btn !py-1 !text-xs">
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {verificationQueue.length === 0 && metrics.total_documents === 0 && (
        <div className="gov-card border-dashed p-10 text-center">
          <Loader2 size={30} className="text-navy mx-auto mb-3" />
          <p className="font-semibold text-navy">No documents processed yet</p>
          <p className="text-sm mt-1">Upload a land record PDF or image using the form above to get started.</p>
        </div>
      )}
    </div>
  );
};
