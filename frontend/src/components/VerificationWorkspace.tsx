import React, { useState, useEffect } from 'react';
import { DocumentVerificationTask, ExtractedField } from '../types';
import { API_BASE } from '../config';
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
    fetch(`${API_BASE}/verification/records/${task.document_id}/verification`)
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
      await fetch(`${API_BASE}/verification/fields/${id}`, {
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
      await fetch(`${API_BASE}/verification/records/${task.document_id}/approve`, {
        method: 'POST'
      });
    } catch (err) {
      console.error('Failed to approve record');
    }
    onSaveCorrections(fields.map(f => ({ ...f, is_verified: true })));
  };

  const confColor = (c: number) => (c >= 0.85 ? 'text-india-green' : 'text-warn');

  return (
    <div className="flex flex-col bg-white border border-line max-w-[1600px] mx-auto" style={{ minHeight: 'calc(100vh - 260px)' }}>
      {/* Action header */}
      <div className="bg-navy text-white px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span>Document:</span>
          <strong>{task.filename}</strong>
          <span className="bg-saffron text-ink px-2 py-0.5 text-xs font-bold">
            Overall confidence: {(task.overall_confidence * 100).toFixed(0)}%
          </span>
        </div>
        <button onClick={handleApproveAll} className="bg-india-green hover:bg-green-800 text-white font-semibold text-sm px-4 py-2 flex items-center gap-1.5 border border-white/30">
          <CheckCircle size={14} />
          <span>Approve and complete task</span>
        </button>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12">
        {/* LEFT: document scan */}
        <div className="lg:col-span-5 border-b lg:border-b-0 lg:border-r border-line bg-paper p-4 relative flex flex-col items-center justify-center overflow-hidden">
          <div className="absolute top-3 right-3 z-10 flex bg-white border border-line" role="group" aria-label="Zoom">
            <button onClick={() => setZoomLevel(prev => Math.min(prev + 0.25, 2.5))} className="p-1.5 text-navy hover:bg-navy-light" aria-label="Zoom in">
              <ZoomIn size={16} />
            </button>
            <button onClick={() => setZoomLevel(prev => Math.max(prev - 0.25, 0.75))} className="p-1.5 text-navy hover:bg-navy-light border-l border-line" aria-label="Zoom out">
              <ZoomOut size={16} />
            </button>
          </div>

          <div className="relative overflow-auto max-h-full max-w-full border border-line bg-white" style={{ transform: `scale(${zoomLevel})` }}>
            <svg width="450" height="600" viewBox="0 0 450 600" className="bg-amber-50">
              <text x="30" y="50" fill="#334155" fontSize="18" fontWeight="bold">प्रारूप खसरा (Khasra Register)</text>
              <text x="30" y="90" fill="#475569" fontSize="12">ग्राम: खजूरी कलां | तहसील: हुजूर | जिला: भोपाल</text>
              <line x1="30" y1="110" x2="420" y2="110" stroke="#cbd5e1" strokeWidth="2" />
              <text x="30" y="160" fill="#1e293b" fontSize="14">1. खाता संख्या / Khata No: 45</text>
              <text x="30" y="220" fill="#1e293b" fontSize="14">2. खातेदार का नाम: राम साहाय</text>
              <text x="30" y="280" fill="#1e293b" fontSize="14">3. खसरा संख्या / Khasra No: 123/4</text>
              <text x="30" y="340" fill="#1e293b" fontSize="14">4. क्षेत्रफल (Hectare): 1.250</text>
              {activeField && activeField.source_bbox && (
                <rect
                  x={activeField.source_bbox[0]}
                  y={activeField.source_bbox[1] / 2}
                  width={Math.max(activeField.source_bbox[2] - activeField.source_bbox[0], 120)}
                  height="30"
                  fill="rgba(255, 153, 51, 0.25)"
                  stroke="#ff9933"
                  strokeWidth="3"
                />
              )}
            </svg>
          </div>
        </div>

        {/* MIDDLE: evidence and validation */}
        <div className="lg:col-span-3 border-b lg:border-b-0 lg:border-r border-line bg-white p-4 overflow-y-auto space-y-4">
          <h3 className="font-bold text-sm text-navy border-b-2 border-saffron pb-1">OCR Evidence and Validation Results</h3>

          {validationResults.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm font-semibold">Rule validation checks</span>
              <div className="space-y-1.5">
                {validationResults.map((val, idx) => (
                  <div key={idx} className={`p-2.5 border border-l-8 text-sm ${
                    val.status === 'PASS' ? 'bg-india-greenLight border-india-green text-india-green'
                    : val.status === 'WARNING' ? 'bg-amber-50 border-saffron text-warn'
                    : 'bg-red-50 border-alert text-alert'
                  }`}>
                    <div className="flex items-center justify-between font-semibold">
                      <span>{val.rule_id}: {val.field_name}</span>
                      <span>{val.status}</span>
                    </div>
                    <p className="text-xs mt-1 text-ink">{val.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {duplicates.length > 0 && (
            <div className="bg-amber-50 border border-saffron border-l-8 p-3 space-y-2">
              <div className="flex items-center gap-2 text-warn font-bold text-sm">
                <AlertTriangle size={16} />
                <span>Suspected duplicate flagged</span>
              </div>
              {duplicates.map((dup, idx) => (
                <div key={idx} className="text-sm space-y-1">
                  <p>Probability: <strong>{(dup.duplicate_probability * 100).toFixed(0)}%</strong></p>
                  <p className="text-xs">{dup.explanation}</p>
                </div>
              ))}
            </div>
          )}

          {activeField ? (
            <div className="space-y-3 pt-2 border-t border-line">
              <div className="bg-navy-light border border-line p-3">
                <span className="text-xs font-semibold text-navy">Selected field</span>
                <p className="font-bold text-sm text-navy">{activeField.field_name}</p>
              </div>
              <div className="bg-navy-light border border-line p-3">
                <span className="text-xs font-semibold text-navy">Raw recognized text</span>
                <p className="text-sm bg-white border border-line p-2 mt-1">{activeField.raw_value}</p>
              </div>
              <div className="bg-navy-light border border-line p-3 space-y-1">
                <span className="text-xs font-semibold text-navy">OCR confidence</span>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-white border border-line h-3">
                    <div
                      className={`h-full ${activeField.confidence >= 0.85 ? 'bg-india-green' : 'bg-saffron'}`}
                      style={{ width: `${activeField.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold">{(activeField.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm">Select a field on the right to see its source evidence.</p>
          )}
        </div>

        {/* RIGHT: extracted fields */}
        <div className="lg:col-span-4 bg-white p-4 overflow-y-auto space-y-3">
          <h3 className="font-bold text-sm text-navy border-b-2 border-saffron pb-1">Extracted Fields</h3>

          <div className="space-y-3">
            {fields.map(field => {
              const isLowConfidence = field.confidence < 0.85;
              const isSelected = activeFieldId === field.field_id;
              return (
                <div
                  key={field.field_id}
                  onClick={() => setActiveFieldId(field.field_id)}
                  className={`p-3 border cursor-pointer ${
                    isSelected ? 'border-navy border-2 bg-navy-light'
                    : isLowConfidence ? 'border-saffron bg-amber-50 hover:bg-navy-light'
                    : 'border-line bg-white hover:bg-navy-light'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <label htmlFor={`f-${field.field_id}`} className="text-sm font-semibold text-navy">
                      {field.field_name}
                    </label>
                    <span className={`text-xs font-bold ${confColor(field.confidence)}`}>
                      {(field.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <input
                    id={`f-${field.field_id}`}
                    type="text"
                    value={field.raw_value || ''}
                    onChange={e => handleFieldChange(field.field_id, e.target.value)}
                    className="w-full bg-white border border-line px-3 py-1.5 text-sm text-ink focus:border-navy focus:outline-none"
                  />
                  {field.warning && (
                    <p className="mt-1.5 text-xs text-warn flex items-center gap-1">
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
