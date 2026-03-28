import React, { useState, useRef } from 'react';
import { Toaster, toast } from 'sonner';
import AppHeader from './components/AppHeader';
import UploadSection from './components/UploadSection';
import PreviewSection from './components/PreviewSection';
import AuditSummaryCards from './components/AuditSummaryCards';
import AuditPanels from './components/AuditPanels';
import ReadinessScorePanel from './components/ReadinessScorePanel';
import DownloadReportSection from './components/DownloadReportSection';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * App-level state machine:
 *   empty           — no file chosen
 *   file_selected   — file chosen, client-side validated
 *   uploading       — /api/parse in progress
 *   parsed          — parse OK, preview visible, ready for audit
 *   parse_error     — /api/parse failed
 *   auditing        — /api/audit in progress
 *   complete        — audit OK, all panels populated
 *   audit_error     — /api/audit failed (parsed state preserved)
 */

export default function App() {
  const [appState, setAppState] = useState('empty');
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetCol, setTargetCol] = useState('');

  // Parse result
  const [parseResult, setParseResult] = useState(null);  // { meta, preview, column_info, warnings }
  const [parseError, setParseError] = useState(null);    // { code, message, hint }

  // Audit result
  const [auditData, setAuditData] = useState(null);
  const [auditError, setAuditError] = useState(null);    // string

  // ──────────────────────────────────────────────
  // Step 1: File selection (client-side validation)
  // ──────────────────────────────────────────────
  const handleFileSelect = (file) => {
    if (!file) return;

    // Client-side extension check
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv') {
      setParseError({
        code: 'unsupported_file_type',
        message: `"${file.name}" is not a CSV file. Only .csv files are accepted.`,
        hint: 'Save your data as a .csv file and try again.',
      });
      setAppState('parse_error');
      return;
    }

    // Client-side size check (50 MB)
    const MAX_BYTES = 50 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      setParseError({
        code: 'too_large',
        message: `File "${file.name}" is ${(file.size / 1024 / 1024).toFixed(1)} MB — exceeds the 50 MB limit.`,
        hint: 'Split the file into smaller parts or reduce the number of rows.',
      });
      setAppState('parse_error');
      return;
    }

    // Soft-check: 0 bytes
    if (file.size === 0) {
      setParseError({
        code: 'empty_file',
        message: 'The selected file is empty (0 bytes).',
        hint: 'Ensure the CSV contains at least a header row and one data row.',
      });
      setAppState('parse_error');
      return;
    }

    setSelectedFile(file);
    setParseError(null);
    setAuditError(null);
    setAuditData(null);
    setParseResult(null);
    setAppState('file_selected');
  };

  // ──────────────────────────────────────────────
  // Step 2: Upload & Parse  →  /api/parse
  // ──────────────────────────────────────────────
  const handleUploadAndParse = async () => {
    if (!selectedFile) return;
    setAppState('uploading');
    setParseError(null);
    setParseResult(null);
    setAuditData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${BACKEND_URL}/api/parse`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      // Structured parse error returned by /api/parse
      if (data.parse_error) {
        setParseError({ code: data.code, message: data.message, hint: data.hint || '' });
        setAppState('parse_error');
        return;
      }

      // HTTP error
      if (!res.ok) {
        setParseError({
          code: 'server_error',
          message: data.detail || `Server error (HTTP ${res.status})`,
          hint: 'Try again. If the problem persists, verify the file is a valid CSV.',
        });
        setAppState('parse_error');
        return;
      }

      setParseResult(data);
      setAppState('parsed');

      const warnCount = data.warnings?.length || 0;
      if (warnCount > 0) {
        toast.warning(`Parsed with ${warnCount} warning${warnCount > 1 ? 's' : ''}`, {
          description: data.warnings[0],
        });
      } else {
        toast.success('File parsed successfully', {
          description: `${data.meta.rows} rows × ${data.meta.cols} columns detected.`,
        });
      }
    } catch (err) {
      setParseError({
        code: 'network_error',
        message: 'Could not reach the server.',
        hint: 'Check your network connection and try again.',
      });
      setAppState('parse_error');
    }
  };

  // ──────────────────────────────────────────────
  // Step 3: Run Full Audit  →  /api/audit
  // ──────────────────────────────────────────────
  const _runAudit = async (tCol) => {
    if (!selectedFile) return;
    setAppState('auditing');
    setAuditError(null);
    setAuditData(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (tCol) formData.append('target_col', tCol);

    try {
      const res = await fetch(`${BACKEND_URL}/api/audit`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data.detail || `Server error (HTTP ${res.status})`;
        setAuditError(msg);
        setAppState('audit_error');
        toast.error('Audit failed', { description: msg });
        return;
      }

      setAuditData(data);
      setAppState('complete');
      toast.success('Audit complete', {
        description: `${data.meta.rows} rows \u00d7 ${data.meta.cols} columns analysed.`,
      });
    } catch (err) {
      setAuditError('Could not reach the server.');
      setAppState('audit_error');
      toast.error('Audit failed', { description: 'Network error.' });
    }
  };

  const handleRunAudit = () => _runAudit(targetCol);

  const handleTargetColChange = (col) => {
    setTargetCol(col);
    if (appState === 'complete' && selectedFile) {
      _runAudit(col);
    }
  };

  // ──────────────────────────────────────────────
  // Reset
  // ──────────────────────────────────────────────
  const handleReset = () => {
    setAppState('empty');
    setSelectedFile(null);
    setParseResult(null);
    setParseError(null);
    setAuditData(null);
    setAuditError(null);
    setTargetCol('');
  };

  // ──────────────────────────────────────────────
  // Download report
  // ──────────────────────────────────────────────
  const handleDownloadReport = async () => {
    if (!auditData) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(auditData),
      });
      if (!res.ok) throw new Error('Report generation failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'audit_report.txt';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded');
    } catch (e) {
      toast.error('Download failed', { description: e.message });
    }
  };

  // Derived state flags for child components
  const isComplete = appState === 'complete';
  const isAuditing = appState === 'auditing';
  const isParsed = appState === 'parsed' || appState === 'audit_error';
  const isUploading = appState === 'uploading';
  const isLocked = appState === 'empty' || appState === 'file_selected';

  // What to use as preview data
  const previewData = isComplete
    ? { preview: auditData?.preview, meta: auditData?.meta }
    : isParsed
    ? { preview: parseResult?.preview, meta: parseResult?.meta }
    : null;

  return (
    <div className="App">
      <Toaster richColors position="top-right" />
      <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* 1. Header */}
        <AppHeader />

        <div className="space-y-6 pb-16">
          {/* 2. CSV Upload */}
          <UploadSection
            appState={appState}
            selectedFile={selectedFile}
            parseResult={parseResult}
            parseError={parseError}
            auditError={auditError}
            onFileSelect={handleFileSelect}
            onUploadAndParse={handleUploadAndParse}
            onRunAudit={handleRunAudit}
            onReset={handleReset}
          />

          {/* 3. Dataset Preview */}
          <PreviewSection
            isLocked={isLocked}
            isUploading={isUploading}
            isParsed={isParsed}
            isAuditing={isAuditing}
            isComplete={isComplete}
            previewData={previewData}
            parseWarnings={parseResult?.warnings || auditData?.parse_warnings || []}
          />

          {/* 4. Audit Summary Cards */}
          <AuditSummaryCards
            isLocked={isLocked || isParsed}
            isAuditing={isAuditing}
            isComplete={isComplete}
            auditData={auditData}
          />

          {/* 5. Detailed Audit Panels */}
          <AuditPanels
            isLocked={isLocked || isParsed}
            isAuditing={isAuditing}
            isComplete={isComplete}
            auditData={auditData}
            targetCol={targetCol}
            onTargetColChange={handleTargetColChange}
            columnNames={auditData?.meta?.column_names || parseResult?.meta?.column_names || []}
          />

          {/* 6. Modeling Readiness Score */}
          <ReadinessScorePanel
            isLocked={isLocked || isParsed}
            isAuditing={isAuditing}
            isComplete={isComplete}
            readiness={auditData?.readiness}
          />

          {/* 7. Download Report */}
          <DownloadReportSection
            isComplete={isComplete}
            onDownload={handleDownloadReport}
          />
        </div>
      </div>
    </div>
  );
}
