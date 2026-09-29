import React, { useState, useEffect } from 'react';
import { Database, CheckCircle, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';

import { API_BASE } from '../config';

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
      <span className="bg-india-greenLight text-india-green border border-india-green px-2 py-0.5 text-xs font-semibold inline-flex items-center gap-1">
        <CheckCircle size={12} />
        <span>{status}</span>
      </span>
    );
  }
  if (s.includes('VERIFICATION')) {
    return (
      <span className="bg-amber-100 text-warn border border-saffron px-2 py-0.5 text-xs font-semibold inline-flex items-center gap-1">
        <AlertTriangle size={12} />
        <span>{status}</span>
      </span>
    );
  }
  return (
    <span className="bg-paper text-ink border border-line px-2 py-0.5 text-xs font-semibold">{status}</span>
  );
};

export const DigitizedRecordsPage: React.FC = () => {
  const [records, setRecords] = useState<LandRecord[]>([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    fetchRecords();
  }, []);

  const dash = <span className="text-gray-400">—</span>;

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-saffron pb-2">
        <div className="flex items-center gap-3">
          <Database size={22} className="text-navy" aria-hidden="true" />
          <div>
            <h2 className="text-xl font-bold text-navy">Digitized Master Land Records</h2>
            <p className="text-sm">Validated, audit-backed land entries extracted from uploaded documents</p>
          </div>
        </div>
        <button onClick={fetchRecords} className="gov-btn-alt flex items-center gap-2">
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={26} className="animate-spin mr-3 text-navy" />
          <span className="text-sm">Loading records from database...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-alert border-l-8 p-4" role="alert">
          <div className="flex items-center gap-2 text-alert">
            <AlertTriangle size={18} />
            <p className="text-sm font-semibold">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="gov-card border-dashed p-12 text-center">
          <Database size={34} className="text-navy mx-auto mb-3" />
          <p className="font-semibold text-navy text-lg">No digitized records yet</p>
          <p className="text-sm mt-1">Upload and process a land record document to see it listed here.</p>
        </div>
      )}

      {!loading && !error && records.length > 0 && (
        <div className="gov-card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                <th className="gov-th">S.No.</th>
                <th className="gov-th">File</th>
                <th className="gov-th">Khata No.</th>
                <th className="gov-th">Khasra / Survey No.</th>
                <th className="gov-th">Registered Owner</th>
                <th className="gov-th">Area</th>
                <th className="gov-th">Village / Tehsil</th>
                <th className="gov-th">District</th>
                <th className="gov-th">Confidence</th>
                <th className="gov-th">Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec, i) => (
                <tr key={rec.record_id} className="odd:bg-white even:bg-paper">
                  <td className="gov-td">{i + 1}</td>
                  <td className="gov-td max-w-[140px] truncate" title={rec.original_filename}>{rec.original_filename}</td>
                  <td className="gov-td font-semibold">{rec.khata_number ?? dash}</td>
                  <td className="gov-td font-semibold text-navy">{rec.survey_number ?? dash}</td>
                  <td className="gov-td font-semibold">{rec.owner_name ?? dash}</td>
                  <td className="gov-td">{rec.plot_area ? `${rec.plot_area} ${rec.area_unit ?? ''}` : dash}</td>
                  <td className="gov-td">{[rec.village, rec.tehsil].filter(Boolean).join(', ') || dash}</td>
                  <td className="gov-td">{rec.district ?? dash}</td>
                  <td className="gov-td">
                    <span className={`font-bold ${
                      rec.overall_confidence >= 0.85 ? 'text-india-green' : rec.overall_confidence >= 0.65 ? 'text-warn' : 'text-alert'
                    }`}>
                      {rec.overall_confidence > 0 ? `${Math.round(rec.overall_confidence * 100)}%` : '—'}
                    </span>
                  </td>
                  <td className="gov-td"><StatusBadge status={rec.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
