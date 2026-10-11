import React, { useState, useRef } from 'react';
import { UploadIcon, AlertTriangleIcon, CheckIcon, FileSpreadsheetIcon } from './Icons';

export default function CsvUploader({ onUpload, loading }) {
    const [selectedFile, setSelectedFile] = useState(null);
    const [summary, setSummary] = useState(null);
    const [showErrors, setShowErrors] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
            setSummary(null);
        }
    };

    const handleUploadSubmit = async () => {
        if (!selectedFile) return;
        try {
            const result = await onUpload(selectedFile);
            setSummary(result);
            setSelectedFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        } catch {
        }
    };

    return (
        <div className="card">
            <div className="card-header">
                <h2 className="card-title">
                    <FileSpreadsheetIcon size={18} />
                    Import Bank Statement
                </h2>
            </div>

            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                    id="csv-file-input"
                />

                <label
                    htmlFor="csv-file-input"
                    className="btn btn-ignore"
                    style={{ cursor: 'pointer', padding: '0.6rem 1rem' }}
                >
                    <UploadIcon size={16} />
                    {selectedFile ? selectedFile.name : 'Choose CSV File'}
                </label>

                <button
                    className="btn btn-primary"
                    onClick={handleUploadSubmit}
                    disabled={!selectedFile || loading}
                >
                    {loading ? 'Importing...' : 'Upload & Reconcile'}
                </button>
            </div>

            {summary && (
                <div style={{ marginTop: '1.25rem', padding: '1rem', background: '#1e293b', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#34d399', fontSize: '0.88rem' }}>
                            <CheckIcon size={16} />
                            <strong>{summary.imported_count}</strong> Imported
                        </span>
                        <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                            <strong>{summary.duplicate_count}</strong> Duplicates Skipped
                        </span>
                        {summary.errors && summary.errors.length > 0 && (
                            <span
                                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#fb7185', fontSize: '0.88rem', cursor: 'pointer', textDecoration: 'underline' }}
                                onClick={() => setShowErrors(!showErrors)}
                            >
                                <AlertTriangleIcon size={16} />
                                <strong>{summary.errors.length}</strong> Row Errors ({showErrors ? 'Hide' : 'View'})
                            </span>
                        )}
                    </div>

                    {showErrors && summary.errors && summary.errors.length > 0 && (
                        <div style={{ marginTop: '0.85rem', maxHeight: '180px', overflowY: 'auto' }}>
                            <table style={{ fontSize: '0.8rem' }}>
                                <thead>
                                    <tr>
                                        <th style={{ width: '80px' }}>Line</th>
                                        <th>Reason</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {summary.errors.map((err, idx) => (
                                        <tr key={idx}>
                                            <td style={{ color: '#fb7185' }}>Line {err.line}</td>
                                            <td>{err.message}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
