import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, RefreshCw, X, Clock } from 'lucide-react';

import { API_BASE } from '../config';

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
    <div className="gov-card max-w-2xl mx-auto">
      <div className="gov-card-title flex items-center gap-2">
        <Upload size={16} aria-hidden="true" />
        <h3>Upload Land Record Document</h3>
      </div>

      <div className="p-4 space-y-4">
        <p className="text-sm">
          Accepted formats: PDF, PNG, JPEG, TIFF (up to 50 MB). Data extraction starts automatically after upload.
        </p>

        {!uploadedDocId && (
          <div
            onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed p-8 text-center cursor-pointer ${
              isDragOver ? 'border-saffron bg-amber-50' : 'border-navy bg-navy-light hover:bg-white'
            }`}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
              className="hidden"
            />
            <FileText size={34} className="text-navy mx-auto mb-2" aria-hidden="true" />
            <span className="text-sm font-semibold text-navy">
              {file ? file.name : 'Click or drag to select a land record scan'}
            </span>
            <span className="block text-xs mt-1 text-gray-600">
              {file
                ? `${(file.size / 1024 / 1024).toFixed(2)} MB – ready to upload`
                : 'Khasra, Khatauni, Jamabandi, Pahani, 7/12 extract, etc.'}
            </span>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-alert border-l-8 flex items-start gap-2" role="alert">
            <AlertCircle size={16} className="text-alert mt-0.5 flex-shrink-0" />
            <p className="text-sm text-alert">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-alert" aria-label="Dismiss error">
              <X size={16} />
            </button>
          </div>
        )}

        {uploadedDocId && pipelineStatus && (
          <div className={`p-4 border border-l-8 space-y-2 ${
            isFailed ? 'bg-red-50 border-alert' : isTerminal ? 'bg-india-greenLight border-india-green' : 'bg-navy-light border-navy'
          }`} role="status">
            <div className="flex items-center gap-2">
              {isFailed ? (
                <AlertCircle size={16} className="text-alert flex-shrink-0" />
              ) : isTerminal ? (
                <CheckCircle size={16} className="text-india-green flex-shrink-0" />
              ) : (
                <RefreshCw size={16} className="text-navy animate-spin flex-shrink-0" />
              )}
              <span className={`text-sm font-semibold ${isFailed ? 'text-alert' : isTerminal ? 'text-india-green' : 'text-navy'}`}>
                {STATUS_LABELS[pipelineStatus] ?? pipelineStatus}
              </span>
            </div>
            {!isTerminal && (
              <div className="flex items-center gap-1.5 text-xs">
                <Clock size={12} />
                <span>Processing in background. This page updates automatically.</span>
              </div>
            )}
            <p className="text-xs text-gray-600">Document ID: {uploadedDocId.slice(0, 16)}…</p>
            {isTerminal && !isFailed && (
              <button
                onClick={() => { setUploadedDocId(null); setPipelineStatus(null); }}
                className="text-sm text-navy underline"
              >
                Upload another document
              </button>
            )}
          </div>
        )}

        {!uploadedDocId && (
          <button onClick={handleUpload} disabled={!file || uploading} className="gov-btn w-full flex items-center justify-center gap-2">
            {uploading ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Uploading...</span>
              </>
            ) : (
              <span>Upload and start extraction</span>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
