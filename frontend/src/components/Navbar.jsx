import React from 'react';
import { BuildingIcon, RefreshIcon } from './Icons';

export default function Navbar({ organizations, currentOrg, onSelectOrg, onRefresh, loading }) {
    return (
        <header className="navbar">
            <div className="nav-brand">
                <div className="brand-logo">CR</div>
                <div className="brand-text">
                    <h1>CapRecon</h1>
                    <p>Bank Reconciliation Portal</p>
                </div>
            </div>

            <div className="nav-actions">
                <div className="org-select-wrapper">
                    <BuildingIcon size={16} />
                    <select
                        className="org-select"
                        value={currentOrg}
                        onChange={(e) => onSelectOrg(e.target.value)}
                    >
                        {organizations.map((org) => (
                            <option key={org.id} value={org.slug}>
                                {org.name}
                            </option>
                        ))}
                    </select>
                </div>

                <span className="tenant-badge">
                    X-Organization: {currentOrg}
                </span>

                <button
                    className="btn-refresh"
                    onClick={onRefresh}
                    disabled={loading}
                    title="Refresh Data"
                >
                    <RefreshIcon size={16} />
                </button>
            </div>
        </header>
    );
}
