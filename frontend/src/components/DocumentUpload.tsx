import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, RefreshCw, X, Clock } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

interface UploadProps {
  onUploadSuccess: () => void;
}

type PipelineStatus =
  | 'UPLOADED' | 'QUEUED' | 'PROCESSING' | 'OCR_PROCESSING' | 'OCR_COMPLETE'
  | 'EXTRACTION_PROCESSING' | 'EXTRACTION_COMPLETE' | 'VALIDATING'
  | 'VALIDATION_COMPLETE' | 'REQUIRES_VERIFICATION' | 'NEEDS_VERIFICATION'
  | 'APPROVED' | 'VERIFIED' | 'REJECTED' | 'FAILED';

const TERMINAL_STATUSES: PipelineStatus[] = [
  'REQUIRES_VERIFICATION', 'NEEDS_VERIFICATION', 'APPROVED', 'VERIFIED', 'REJECTED', 'FAILED'
];

const STATUS_LABELS: Record<string, string> = {
  UPLOADED: 'Document stored',
  QUEUED: 'Queued for processing',
  PROCESSING: 'Starting pipeline...',
  OCR_PROCESSING: 'Running OCR / document understanding...',
  OCR_COMPLETE: 'OCR complete',
  EXTRACTION_PROCESSING: 'Extracting fields...',
  EXTRACTION_COMPLETE: 'Field extraction complete',
  VALIDATING: 'Validating fields & checking duplicates...',
  VALIDATION_COMPLETE: 'Validation complete',
  REQUIRES_VERIFICATION: '✓ Processing done — requires human verification',
  NEEDS_VERIFICATION: '✓ Processing done — requires human verification',
  APPROVED: '✓ Auto-approved (high confidence)',
  VERIFIED: '✓ Human verified',
  REJECTED: '✗ Document rejected',
  FAILED: '✗ Processing failed — check backend logs',
};

export const DocumentUpload: React.FC<UploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedDocId, setUploadedDocId] = useState<string | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Poll pipeline status after upload ────────────────────────────────────
  useEffect(() => {
    if (!uploadedDocId) return;

    const poll = () => {
      fetch(`${API_BASE}/documents/${uploadedDocId}/status`)
        .then(res => res.json())
        .then(data => {
          const status: PipelineStatus = data.status;
          setPipelineStatus(status);

          if (TERMINAL_STATUSES.includes(status)) {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            onUploadSuccess(); // Refresh dashboard metrics
          }
        })
        .catch(() => {
          // Don't stop polling on a transient network error
        });
    };

    poll(); // Immediate first poll
    pollIntervalRef.current = setInterval(poll, 1500);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [uploadedDocId, onUploadSuccess]);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setUploadedDocId(null);
    setPipelineStatus(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadedDocId(null);
    setPipelineStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/documents/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${response.status}`);
      }

      const data = await response.json();
      setUploadedDocId(data.document_id);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setError(err.message || 'Upload failed. Make sure the backend is running.');
    } finally {
      setUploading(false);
    }
  };

  const isTerminal = pipelineStatus && TERMINAL_STATUSES.includes(pipelineStatus as PipelineStatus);
  const isFailed = pipelineStatus === 'FAILED' || pipelineStatus === 'REJECTED';

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl space-y-4 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center space-x-3 border-b border-slate-700 pb-3">
        <Upload className="text-emerald-400" size={22} />
        <div>
          <h3 className="font-bold text-slate-100 text-sm">Upload Land Record Document</h3>
          <p className="text-xs text-slate-400">
            Supports PDF, PNG, JPEG, TIFF up to 50 MB. AI extraction runs automatically.
          </p>
        </div>
      </div>

      {/* Drop zone */}
      {!uploadedDocId && (
        <div
          onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer ${
            isDragOver
              ? 'border-emerald-400 bg-emerald-500/10'
              : 'border-slate-700 hover:border-emerald-500/50 bg-slate-900/50'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
            className="hidden"
          />
          <FileText size={36} className="text-slate-500 mx-auto mb-2" />
          <span className="text-sm font-semibold text-slate-200">
            {file ? file.name : 'Click or drag to select a land record scan'}
          </span>
          <span className="block text-xs text-slate-500 mt-1">
            {file
              ? `${(file.size / 1024 / 1024).toFixed(2)} MB — ready to upload`
              : 'Khasra, Khatauni, Pahani, 7/12 extract, etc.'}
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-900/30 border border-red-500/30 rounded-lg flex items-start space-x-2">
          <AlertCircle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-red-300">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Pipeline status tracker */}
      {uploadedDocId && pipelineStatus && (
        <div className={`p-4 rounded-xl border space-y-2 ${
          isFailed
            ? 'bg-red-900/20 border-red-500/30'
            : isTerminal
            ? 'bg-emerald-900/20 border-emerald-500/30'
            : 'bg-slate-900/80 border-slate-700'
        }`}>
          <div className="flex items-center space-x-2">
            {isFailed ? (
              <AlertCircle size={14} className="text-red-400 flex-shrink-0" />
            ) : isTerminal ? (
              <CheckCircle size={14} className="text-emerald-400 flex-shrink-0" />
            ) : (
              <RefreshCw size={14} className="text-sky-400 animate-spin flex-shrink-0" />
            )}
            <span className={`text-xs font-semibold ${
              isFailed ? 'text-red-300' : isTerminal ? 'text-emerald-300' : 'text-sky-300'
            }`}>
              {STATUS_LABELS[pipelineStatus] ?? pipelineStatus}
            </span>
          </div>
          {!isTerminal && (
            <div className="flex items-center space-x-1.5 text-xs text-slate-500">
              <Clock size={11} />
              <span>Processing in background — this page will update automatically</span>
            </div>
          )}
          <p className="text-[11px] text-slate-500 font-mono">doc: {uploadedDocId.slice(0, 16)}…</p>
          {isTerminal && !isFailed && (
            <button
              onClick={() => { setUploadedDocId(null); setPipelineStatus(null); }}
              className="text-xs text-emerald-400 hover:text-emerald-300 underline mt-1"
            >
              Upload another document
            </button>
          )}
        </div>
      )}

      {/* Upload button */}
      {!uploadedDocId && (
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-2.5 rounded-lg text-xs font-semibold shadow transition flex items-center justify-center space-x-2 ${
            file && !uploading
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
              : 'bg-slate-700 text-slate-500 cursor-not-allowed'
          }`}
        >
          {uploading ? (
            <>
              <RefreshCw size={14} className="animate-spin" />
              <span>Uploading...</span>
            </>
          ) : (
            <span>Upload & Start AI Extraction Pipeline</span>
          )}
        </button>
      )}
    </div>
  );
};
