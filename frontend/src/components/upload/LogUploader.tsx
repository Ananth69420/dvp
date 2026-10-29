import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ArrowRight,
  Layers,
  Sparkles,
  FileCheck2,
} from 'lucide-react';
import { UploadResponse, SampleItem } from '../../types';
import { apiClient } from '../../api/client';

interface LogUploaderProps {
  uploadData: UploadResponse | null;
  onUploadSuccess: (data: UploadResponse) => void;
  onParseComplete: (result: any) => void;
  isParsing: boolean;
}

export const LogUploader: React.FC<LogUploaderProps> = ({
  uploadData,
  onUploadSuccess,
  onParseComplete,
  isParsing,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [loadingSample, setLoadingSample] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    apiClient
      .getSamples()
      .then((res) => setSamples(res.samples))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (uploadData) {
      setSelectedFormat(uploadData.detected_format);
    }
  }, [uploadData]);

  const handleFileDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const data = await apiClient.uploadLog(file);
      onUploadSuccess(data);
    } catch (err: any) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const loadSample = async (sampleName: string) => {
    setUploadError(null);
    setLoadingSample(true);
    try {
      const data = await apiClient.loadSample(sampleName);
      onUploadSuccess(data);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to load sample');
    } finally {
      setLoadingSample(false);
    }
  };

  const triggerParse = async () => {
    if (!uploadData) return;
    setUploadError(null);
    try {
      const result = await apiClient.parseLog(uploadData.dataset_id, selectedFormat);
      onParseComplete(result);
    } catch (err: any) {
      setUploadError(err.message || 'Parsing failed');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Intro Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Log File Intake &amp; Parsing</h2>
        <p className="text-sm text-slate-500 mt-1">
          Upload raw log streams (.log, .txt, .csv, .jsonl) or load realistic synthetic datasets to inspect parsing engine behavior, schema mapping, and error resilience.
        </p>

        {/* Synthetic Samples Quick Bar */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-600 mb-2.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Quick-Load Synthetic Demonstration Logs:</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
            {samples.map((s) => (
              <button
                key={s.name}
                onClick={() => loadSample(s.name)}
                disabled={loadingSample || isUploading}
                className="text-left p-2.5 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/40 transition-all text-xs bg-slate-50/50 group"
              >
                <div className="font-semibold text-slate-800 truncate group-hover:text-indigo-700">
                  {s.name}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">{s.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleFileDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all bg-white ${
          isDragging
            ? 'border-indigo-500 bg-indigo-50/30 ring-4 ring-indigo-50'
            : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".log,.txt,.csv,.json,.jsonl"
          className="hidden"
        />

        <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-3 shadow-2xs">
          <UploadCloud className="w-6 h-6" />
        </div>

        <h3 className="text-base font-semibold text-slate-800">
          Drag and drop your raw log file here
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Supports common microservice logs, Python stack traces, Apache/Nginx web logs, JSON Lines, and CSV tables (up to 50MB).
        </p>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || loadingSample}
          className="mt-4 px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 transition-colors shadow-xs"
        >
          {isUploading ? 'Uploading...' : 'Browse Local Files'}
        </button>

        {uploadError && (
          <div className="mt-4 flex items-center justify-center space-x-2 text-rose-600 text-xs font-medium bg-rose-50 p-2.5 rounded-lg border border-rose-200 max-w-md mx-auto">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Uploaded File & Format Confirmation */}
      {uploadData && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">{uploadData.filename}</h4>
                <div className="flex items-center space-x-3 text-xs text-slate-500 mt-0.5">
                  <span>{(uploadData.file_size_bytes / 1024).toFixed(1)} KB</span>
                  <span>•</span>
                  <span>{uploadData.total_lines} raw lines</span>
                </div>
              </div>
            </div>

            <button
              onClick={triggerParse}
              disabled={isParsing}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 shadow-sm transition-all"
            >
              <span>{isParsing ? 'Parsing Engine Running...' : 'Execute Parser Engine'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Format Identification & Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                <span>Identified Parser Format</span>
                <span className="text-[10px] text-emerald-700 font-bold px-1.5 py-0.2 bg-emerald-50 rounded border border-emerald-200">
                  Confidence: {(uploadData.detection_confidence * 100).toFixed(0)}%
                </span>
              </label>
              <span className="text-[11px] text-slate-400">You can override the parser format below</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {uploadData.candidates.map((cand) => {
                const isSelected = selectedFormat === cand.format_id;
                return (
                  <button
                    key={cand.format_id}
                    onClick={() => setSelectedFormat(cand.format_id)}
                    className={`p-3 rounded-lg border text-left transition-all text-xs ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-100 font-semibold text-indigo-900'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/30 text-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate">{cand.name}</span>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Fit score: {(cand.confidence * 100).toFixed(0)}%
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Raw Lines Preview */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-slate-400" />
                Raw Log Stream Preview (First {uploadData.preview_lines.length} lines)
              </span>
            </div>
            <div className="bg-slate-900 text-slate-100 p-3.5 rounded-lg font-mono text-[11px] overflow-x-auto max-h-56 leading-relaxed">
              {uploadData.preview_lines.map((line, idx) => (
                <div key={idx} className="flex space-x-3 hover:bg-slate-800/60 px-1 rounded">
                  <span className="text-slate-500 select-none w-8 text-right shrink-0">
                    {idx + 1}
                  </span>
                  <span className="text-slate-200 whitespace-pre">{line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
