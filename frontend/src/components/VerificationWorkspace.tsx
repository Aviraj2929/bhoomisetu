import React, { useState, useEffect } from 'react';
import { DocumentVerificationTask, ExtractedField } from '../types';
import { AlertCircle, CheckCircle, Eye, Edit3, ZoomIn, ZoomOut, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ValidationRuleResult {
  rule_id: string;
  field_name: string;
  severity: string;
  status: string;
  message: string;
  source: string;
}

interface SuspectedDuplicate {
  duplicate_probability: number;
  is_duplicate_suspect: boolean;
  matching_features: string[];
  explanation: string;
}

interface WorkspaceProps {
  task: DocumentVerificationTask;
  onSaveCorrections: (updatedFields: ExtractedField[]) => void;
}

export const VerificationWorkspace: React.FC<WorkspaceProps> = ({ task, onSaveCorrections }) => {
  const [fields, setFields] = useState<ExtractedField[]>(task.fields);
  const [activeFieldId, setActiveFieldId] = useState<string | null>(task.fields[0]?.field_id || null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [validationResults, setValidationResults] = useState<ValidationRuleResult[]>([]);
  const [duplicates, setDuplicates] = useState<SuspectedDuplicate[]>([]);

  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/verification/records/${task.document_id}/verification`)
      .then(res => res.json())
      .then(data => {
        if (data.fields && data.fields.length > 0) {
          setFields(data.fields);
        }
        if (data.validation_results) {
          setValidationResults(data.validation_results);
        }
        if (data.suspected_duplicates) {
          setDuplicates(data.suspected_duplicates);
        }
      })
      .catch(() => {
        // Fallback to initial task data
      });
  }, [task.document_id]);

  const activeField = fields.find(f => f.field_id === activeFieldId);

  const handleFieldChange = async (id: string, value: string) => {
    setFields(fields.map(f => f.field_id === id ? { ...f, raw_value: value, confidence: 1.0, is_verified: true } : f));
    
    try {
      await fetch(`http://localhost:8000/api/v1/verification/fields/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value, reason: 'Human verifier UI correction' })
      });
    } catch (err) {
      console.error('Failed to log field patch');
    }
  };

  const handleApproveAll = async () => {
    try {
      await fetch(`http://localhost:8000/api/v1/verification/records/${task.document_id}/approve`, {
        method: 'POST'
      });
    } catch (err) {
      console.error('Failed to approve record');
    }
    onSaveCorrections(fields.map(f => ({ ...f, is_verified: true })));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] bg-slate-950">
      {/* Action Header */}
      <div className="bg-slate-900 border-b border-slate-800 px-6 py-2.5 flex items-center justify-between">
        <div className="flex items-center space-x-3 text-xs">
          <span className="text-slate-400">Document:</span>
          <strong className="text-slate-200">{task.filename}</strong>
          <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded font-mono">
            Overall Conf: {(task.overall_confidence * 100).toFixed(0)}%
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleApproveAll}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded-lg shadow transition flex items-center space-x-1.5"
          >
            <CheckCircle size={14} />
            <span>Approve & Complete Task (Ctrl+Enter)</span>
          </button>
        </div>
      </div>

      {/* 3-Pane Grid Workspace */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* LEFT PANE: Document Scan Canvas (5 Columns) */}
        <div className="col-span-5 border-r border-slate-800 bg-slate-950 p-4 relative flex flex-col items-center justify-center overflow-hidden">
          <div className="absolute top-4 right-4 z-10 flex space-x-1 bg-slate-800 p-1 rounded-lg border border-slate-700">
            <button onClick={() => setZoomLevel(prev => Math.min(prev + 0.25, 2.5))} className="p-1.5 text-slate-300 hover:text-white">
              <ZoomIn size={16} />
            </button>
            <button onClick={() => setZoomLevel(prev => Math.max(prev - 0.25, 0.75))} className="p-1.5 text-slate-300 hover:text-white">
              <ZoomOut size={16} />
            </button>
          </div>

          <div className="relative overflow-auto max-h-full max-w-full border border-slate-800 rounded shadow-2xl bg-white" style={{ transform: `scale(${zoomLevel})` }}>
            {/* SVG Rendered Document Mock Scan */}
            <svg width="450" height="600" viewBox="0 0 450 600" className="bg-amber-50">
              <text x="30" y="50" fill="#334155" fontSize="18" fontWeight="bold">प्रारूप खसरा (Khasra Register)</text>
              <text x="30" y="90" fill="#475569" fontSize="12">ग्राम: खजूरी कलां | तहसील: हुजूर | जिला: भोपाल</text>
              <line x1="30" y1="110" x2="420" y2="110" stroke="#cbd5e1" strokeWidth="2" />
              
              {/* Text Fields */}
              <text x="30" y="160" fill="#1e293b" fontSize="14">1. खाता संख्या / Khata No: 45</text>
              <text x="30" y="220" fill="#1e293b" fontSize="14">2. खातेदार का नाम: राम साहाय</text>
              <text x="30" y="280" fill="#1e293b" fontSize="14">3. खसरा संख्या / Khasra No: 123/4</text>
              <text x="30" y="340" fill="#1e293b" fontSize="14">4. क्षेत्रफल (Hectare): 1.250</text>

              {/* Bounding Box Highlights for Active Selected Field */}
              {activeField && activeField.source_bbox && (
                <rect
                  x={activeField.source_bbox[0]}
                  y={activeField.source_bbox[1] / 2}
                  width={Math.max(activeField.source_bbox[2] - activeField.source_bbox[0], 120)}
                  height="30"
                  fill="rgba(245, 158, 11, 0.25)"
                  stroke="#f59e0b"
                  strokeWidth="3"
                  className="animate-pulse"
                />
              )}
            </svg>
          </div>
        </div>

        {/* MIDDLE PANE: OCR Source Evidence & Validation Engine Results (3 Columns) */}
        <div className="col-span-3 border-r border-slate-800 bg-slate-900 p-5 overflow-y-auto space-y-5">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
            OCR Evidence & Validation Results
          </h3>

          {/* Validation Engine Rule Results */}
          {validationResults.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Rule Validation Checks</span>
              <div className="space-y-1.5">
                {validationResults.map((val, idx) => (
                  <div key={idx} className={`p-2.5 rounded-lg border text-xs ${
                    val.status === 'PASS' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
                    val.status === 'WARNING' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
                    'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  }`}>
                    <div className="flex items-center justify-between font-semibold">
                      <span>{val.rule_id}: {val.field_name}</span>
                      <span>{val.status}</span>
                    </div>
                    <p className="text-[11px] mt-1 opacity-90">{val.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suspected Duplicates Alert */}
          {duplicates.length > 0 && (
            <div className="bg-amber-500/10 border border-amber-500/40 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center space-x-2 text-amber-400 font-bold text-xs">
                <AlertTriangle size={16} />
                <span>Suspected Duplicate Flagged</span>
              </div>
              {duplicates.map((dup, idx) => (
                <div key={idx} className="text-xs text-slate-300 space-y-1">
                  <p>Probability: <strong className="text-amber-300">{(dup.duplicate_probability * 100).toFixed(0)}%</strong></p>
                  <p className="text-[11px] text-slate-400">{dup.explanation}</p>
                </div>
              ))}
            </div>
          )}

          {activeField ? (
            <div className="space-y-4 pt-2 border-t border-slate-800">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Active Selected Field</span>
                <p className="font-bold text-sm text-emerald-400">{activeField.field_name}</p>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">Raw Recognized Snippet</span>
                <p className="font-mono text-sm text-slate-200 bg-slate-950 p-2 rounded">{activeField.raw_value}</p>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase">OCR Confidence Score</span>
                <div className="flex items-center space-x-3">
                  <div className="flex-1 bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${activeField.confidence >= 0.85 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                      style={{ width: `${activeField.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-300">
                    {(activeField.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Select a field on the right pane to inspect source evidence.</p>
          )}
        </div>

        {/* RIGHT PANE: Targeted Form Fields (4 Columns) */}
        <div className="col-span-4 bg-slate-900 p-5 overflow-y-auto space-y-4">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
            Targeted Extracted Fields
          </h3>

          <div className="space-y-3">
            {fields.map(field => {
              const isLowConfidence = field.confidence < 0.85;
              const isSelected = activeFieldId === field.field_id;

              return (
                <div
                  key={field.field_id}
                  onClick={() => setActiveFieldId(field.field_id)}
                  className={`p-4 rounded-xl border transition cursor-pointer ${
                    isSelected
                      ? 'bg-slate-800 border-emerald-500 ring-1 ring-emerald-500'
                      : isLowConfidence
                      ? 'bg-amber-500/10 border-amber-500/40 hover:bg-slate-800/80'
                      : 'bg-slate-800/50 border-slate-700/60 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                      {field.field_name}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        field.confidence >= 0.85
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {(field.confidence * 100).toFixed(0)}% Conf
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={field.raw_value || ''}
                      onChange={e => handleFieldChange(field.field_id, e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  {field.warning && (
                    <p className="mt-2 text-[11px] text-amber-400 flex items-center space-x-1">
                      <AlertCircle size={12} />
                      <span>{field.warning}</span>
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
