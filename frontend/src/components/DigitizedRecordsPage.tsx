import React, { useState, useEffect } from 'react';
import { Database, CheckCircle, AlertTriangle, Loader2, RefreshCw, Trash2 } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

interface LandRecord {
  record_id: string;
  document_id: string;
  original_filename: string;
  status: string;
  overall_confidence: number;
  owner_name?: string | null;
  survey_number?: string | null;
  khata_number?: string | null;
  plot_area?: string | null;
  area_unit?: string | null;
  village?: string | null;
  tehsil?: string | null;
  district?: string | null;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const s = status.toUpperCase();
  if (s === 'APPROVED' || s === 'VERIFIED') {
    return (
      <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-full text-[11px] font-semibold inline-flex items-center space-x-1">
        <CheckCircle size={11} />
        <span>{status}</span>
      </span>
    );
  }
  if (s.includes('VERIFICATION')) {
    return (
      <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-1 rounded-full text-[11px] font-semibold inline-flex items-center space-x-1">
        <AlertTriangle size={11} />
        <span>{status}</span>
      </span>
    );
  }
  return (
    <span className="bg-slate-700 text-slate-300 border border-slate-600 px-2.5 py-1 rounded-full text-[11px] font-semibold">
      {status}
    </span>
  );
};

export const DigitizedRecordsPage: React.FC = () => {
  const [records, setRecords] = useState<LandRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecords = () => {
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/records/`)
      .then(res => {
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        return res.json();
      })
      .then(data => {
        setRecords(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        setError(`Failed to load records: ${err.message}. Is the backend running?`);
        setLoading(false);
      });
  };

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all database history and digitized records? This action cannot be undone.")) {
      return;
    }

    setClearing(true);
    try {
      const res = await fetch(`${API_BASE}/records/`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRecords([]);
    } catch (err: any) {
      alert(`Failed to clear history: ${err.message}`);
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <Database size={22} className="text-emerald-400" />
          <div>
            <h2 className="text-xl font-bold text-slate-100">Digitized Master Land Records</h2>
            <p className="text-xs text-slate-400">
              Validated and audit-backed land entries extracted from uploaded documents
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchRecords}
            disabled={loading || clearing}
            className="flex items-center space-x-2 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 hover:border-slate-600 px-3 py-1.5 rounded-lg transition disabled:opacity-50"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleClearHistory}
            disabled={clearing || records.length === 0}
            className="flex items-center space-x-1.5 text-xs font-semibold text-rose-400 hover:text-rose-300 bg-rose-500/10 border border-rose-500/30 hover:bg-rose-500/20 disabled:opacity-40 disabled:cursor-not-allowed px-3 py-1.5 rounded-lg transition"
          >
            <Trash2 size={13} />
            <span>{clearing ? 'Clearing...' : 'Clear History'}</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48 text-slate-500">
          <Loader2 size={28} className="animate-spin mr-3" />
          <span className="text-sm">Loading records from database...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6 text-center">
          <AlertTriangle size={24} className="text-red-400 mx-auto mb-2" />
          <p className="text-red-300 text-sm font-semibold">{error}</p>
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="bg-slate-800/50 border border-slate-700 border-dashed rounded-xl p-16 text-center">
          <Database size={36} className="text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 font-semibold text-lg">No digitized records yet</p>
          <p className="text-slate-500 text-sm mt-1">
            Upload and process a land record document to see it appear here.
          </p>
        </div>
      )}

      {!loading && !error && records.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900 border-b border-slate-700 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-4 py-3">File</th>
                <th className="px-4 py-3">Khata No</th>
                <th className="px-4 py-3">Khasra No</th>
                <th className="px-4 py-3">Registered Owner</th>
                <th className="px-4 py-3">Area</th>
                <th className="px-4 py-3">Village / Tehsil</th>
                <th className="px-4 py-3">District</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 font-mono">
              {records.map(rec => (
                <tr key={rec.record_id} className="hover:bg-slate-700/40 transition">
                  <td className="px-4 py-3 font-sans text-slate-400 text-[11px] max-w-[120px] truncate" title={rec.original_filename}>
                    {rec.original_filename}
                  </td>
                  <td className="px-4 py-3 font-bold text-slate-100">
                    {rec.khata_number ?? <span className="text-slate-600 italic">—</span>}
                  </td>
                  <td className="px-4 py-3 text-emerald-400 font-bold">
                    {rec.survey_number ?? <span className="text-slate-600 italic">—</span>}
                  </td>
                  <td className="px-4 py-3 font-sans font-semibold text-slate-100">
                    {rec.owner_name ?? <span className="text-slate-600 italic font-normal">—</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-200">
                    {rec.plot_area
                      ? `${rec.plot_area} ${rec.area_unit ?? ''}`
                      : <span className="text-slate-600 italic">—</span>}
                  </td>
                  <td className="px-4 py-3 font-sans text-slate-300">
                    {[rec.village, rec.tehsil].filter(Boolean).join(', ') || <span className="text-slate-600 italic">—</span>}
                  </td>
                  <td className="px-4 py-3 font-sans text-slate-400">
                    {rec.district ?? <span className="text-slate-600 italic">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`font-bold font-sans ${
                      rec.overall_confidence >= 0.85 ? 'text-emerald-400'
                        : rec.overall_confidence >= 0.65 ? 'text-amber-400'
                        : 'text-red-400'
                    }`}>
                      {rec.overall_confidence > 0 ? `${Math.round(rec.overall_confidence * 100)}%` : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={rec.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
