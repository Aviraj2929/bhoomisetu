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
  const color = pct >= 85 ? 'text-emerald-400' : pct >= 65 ? 'text-amber-400' : 'text-red-400';
  return <span className={`font-mono font-bold ${color}`}>{pct}%</span>;
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

  return (
    <div className="max-w-7xl mx-auto space-y-8">

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs uppercase font-semibold tracking-wide">Total Documents</span>
            <FileText size={18} />
          </div>
          <p className="text-3xl font-extrabold text-slate-100">{metrics.total_documents}</p>
          <span className="text-xs text-slate-500">Uploaded and tracked</span>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs uppercase font-semibold tracking-wide">Auto-Approved</span>
            <CheckCircle size={18} className="text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold text-emerald-400">{metrics.auto_approval_rate}</p>
          <span className="text-xs text-slate-500">{metrics.auto_approved} documents</span>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs uppercase font-semibold tracking-wide">Avg Field Confidence</span>
            <Activity size={18} className="text-sky-400" />
          </div>
          <p className="text-3xl font-extrabold text-sky-400">
            {metrics.avg_field_confidence > 0
              ? `${(metrics.avg_field_confidence * 100).toFixed(1)}%`
              : '—'}
          </p>
          <span className="text-xs text-slate-500">Across all extracted fields</span>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs uppercase font-semibold tracking-wide">Avg Processing Time</span>
            <Clock size={18} className="text-purple-400" />
          </div>
          <p className="text-3xl font-extrabold text-purple-400">{avgProcessing}</p>
          <span className="text-xs text-slate-500">Per document</span>
        </div>
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-slate-800 border border-amber-500/30 rounded-xl p-5">
          <div className="flex items-center space-x-3 mb-2">
            <AlertTriangle size={18} className="text-amber-400" />
            <span className="text-xs uppercase font-semibold text-slate-400">Pending Verification</span>
          </div>
          <p className="text-2xl font-extrabold text-amber-400">{metrics.action_required.pending_verifications}</p>
          {metrics.action_required.pending_verifications > 0 && (
            <button
              onClick={onOpenVerification}
              className="mt-3 text-xs text-amber-400 hover:text-amber-300 underline transition"
            >
              Open queue →
            </button>
          )}
        </div>

        <div className="bg-slate-800 border border-red-500/30 rounded-xl p-5">
          <div className="flex items-center space-x-3 mb-2">
            <XCircle size={18} className="text-red-400" />
            <span className="text-xs uppercase font-semibold text-slate-400">Failed Processing</span>
          </div>
          <p className="text-2xl font-extrabold text-red-400">{metrics.action_required.validation_failures}</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <div className="flex items-center space-x-3 mb-2">
            <Users size={18} className="text-slate-400" />
            <span className="text-xs uppercase font-semibold text-slate-400">Human Verified</span>
          </div>
          <p className="text-2xl font-extrabold text-slate-100">{metrics.human_verified}</p>
        </div>
      </div>

      {/* Verification Queue Table */}
      {verificationQueue.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
            <h3 className="font-bold text-slate-100 text-sm">Verification Queue</h3>
            <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 rounded-full font-semibold">
              {verificationQueue.length} pending
            </span>
          </div>
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900 border-b border-slate-700 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-5 py-3">Filename</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Weakest Field</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60">
              {verificationQueue.map(item => (
                <tr key={item.document_id} className="hover:bg-slate-700/40 transition">
                  <td className="px-5 py-3 font-mono text-slate-200">{item.original_filename}</td>
                  <td className="px-5 py-3">
                    <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded text-[11px] font-semibold">
                      {item.status}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <ConfidenceBadge value={item.overall_confidence} />
                  </td>
                  <td className="px-5 py-3 font-mono text-slate-400">
                    {item.lowest_confidence_field}
                    {' '}
                    <span className="text-red-400">({Math.round(item.lowest_confidence * 100)}%)</span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => onLoadTask?.(item.document_id, item.original_filename, item.overall_confidence)}
                      className="bg-amber-600 hover:bg-amber-500 text-white font-semibold text-[11px] px-3 py-1.5 rounded transition"
                    >
                      Review →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty queue state */}
      {verificationQueue.length === 0 && metrics.total_documents === 0 && (
        <div className="bg-slate-800/50 border border-slate-700 border-dashed rounded-xl p-12 text-center">
          <Loader2 size={32} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 font-semibold">No documents processed yet</p>
          <p className="text-slate-500 text-sm mt-1">Upload a land record PDF or image to get started.</p>
        </div>
      )}
    </div>
  );
};
