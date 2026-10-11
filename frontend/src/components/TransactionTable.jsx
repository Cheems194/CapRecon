import React, { useState } from 'react';
import { formatMoney } from '../api';
import { CheckIcon, CrossIcon, BanIcon } from './Icons';

export default function TransactionTable({
    transactions,
    onApprove,
    onReject,
    onIgnore,
    actionLoadingId,
}) {
    const [filter, setFilter] = useState('all');

    const filtered = transactions.filter((tx) => {
        if (filter === 'all') return true;
        return tx.status === filter;
    });

    return (
        <div className="card">
            <div className="card-header">
                <h2 className="card-title">Bank Transactions</h2>

                <div style={{ display: 'flex', gap: '0.35rem' }}>
                    {['all', 'suggested', 'needs_review', 'reconciled', 'ignored'].map((tab) => (
                        <button
                            key={tab}
                            className="btn btn-ignore"
                            style={{
                                fontSize: '0.75rem',
                                padding: '0.25rem 0.6rem',
                                background: filter === tab ? '#334155' : 'transparent',
                                color: filter === tab ? '#fff' : 'var(--text-muted)',
                            }}
                            onClick={() => setFilter(tab)}
                        >
                            {tab.replace('_', ' ')}
                        </button>
                    ))}
                </div>
            </div>

            <div className="table-wrapper">
                {filtered.length === 0 ? (
                    <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        No transactions found for this view.
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Date / Ref</th>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Suggested Match</th>
                                <th>Reason</th>
                                <th style={{ textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((tx) => {
                                const proposedMatch = tx.matches?.find((m) => m.status === 'proposed');
                                const approvedMatch = tx.matches?.find((m) => m.status === 'approved');
                                const displayMatch = approvedMatch || proposedMatch;

                                const isCredit = tx.transaction_type === 'credit';
                                const isActionable = tx.status === 'suggested' || tx.status === 'needs_review';

                                return (
                                    <tr key={tx.id}>
                                        <td>
                                            <div>{tx.date}</div>
                                            <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)' }}>
                                                {tx.bank_reference}
                                            </span>
                                        </td>

                                        <td style={{ maxWidth: '240px', wordBreak: 'break-word' }}>
                                            {tx.description}
                                        </td>

                                        <td className={`text-money ${isCredit ? 'credit-amount' : 'debit-amount'}`}>
                                            {formatMoney(tx.amount)}
                                        </td>

                                        <td>
                                            <span className={`badge badge-${tx.status}`}>
                                                {tx.status.replace('_', ' ')}
                                            </span>
                                        </td>

                                        <td>
                                            {displayMatch ? (
                                                <div>
                                                    <strong>{displayMatch.investor_name}</strong>
                                                    <div style={{ fontSize: '0.75rem', color: '#60a5fa' }}>
                                                        {displayMatch.wire_reference}
                                                    </div>
                                                </div>
                                            ) : (
                                                <span style={{ color: 'var(--text-subtle)' }}>—</span>
                                            )}
                                        </td>

                                        <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: '220px' }}>
                                            {displayMatch?.reason || tx.review_reason || '—'}
                                        </td>

                                        <td style={{ textAlign: 'right' }}>
                                            <div style={{ display: 'inline-flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                                                {proposedMatch && (
                                                    <>
                                                        <button
                                                            className="btn btn-approve"
                                                            onClick={() => onApprove(proposedMatch.id)}
                                                            disabled={actionLoadingId === proposedMatch.id}
                                                            title="Approve Match"
                                                        >
                                                            <CheckIcon size={14} />
                                                            Approve
                                                        </button>

                                                        <button
                                                            className="btn btn-reject"
                                                            onClick={() => onReject(proposedMatch.id)}
                                                            disabled={actionLoadingId === proposedMatch.id}
                                                            title="Reject Match"
                                                        >
                                                            <CrossIcon size={14} />
                                                        </button>
                                                    </>
                                                )}

                                                {isActionable && (
                                                    <button
                                                        className="btn btn-ignore"
                                                        onClick={() => onIgnore(tx.id)}
                                                        disabled={actionLoadingId === tx.id}
                                                        title="Ignore Transaction"
                                                    >
                                                        <BanIcon size={14} />
                                                        Ignore
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
