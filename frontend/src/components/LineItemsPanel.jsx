import React from 'react';
import { formatMoney } from '../api';

export default function LineItemsPanel({ lineItems }) {
    const groupedByCall = lineItems.reduce((acc, item) => {
        const callNum = item.capital_call_number || 1;
        if (!acc[callNum]) {
            acc[callNum] = {
                number: callNum,
                dueDate: item.capital_call_due_date,
                items: [],
            };
        }
        acc[callNum].items.push(item);
        return acc;
    }, {});

    const calls = Object.values(groupedByCall);

    return (
        <div className="card">
            <div className="card-header">
                <h2 className="card-title">Capital Call Line Items</h2>
            </div>

            {calls.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No line items found.
                </div>
            ) : (
                calls.map((call) => {
                    const totalCalled = call.items.reduce((sum, i) => sum + parseFloat(i.amount_called), 0);
                    const totalFunded = call.items.reduce((sum, i) => sum + parseFloat(i.amount_funded), 0);
                    const percent = totalCalled > 0 ? Math.min(100, Math.round((totalFunded / totalCalled) * 100)) : 0;

                    return (
                        <div key={call.number} style={{ marginBottom: '1.75rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.25rem' }}>
                                <strong style={{ fontSize: '0.95rem' }}>Capital Call #{call.number}</strong>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                                    Due: {call.dueDate}
                                </span>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                <span>Funded: {formatMoney(totalFunded)} / {formatMoney(totalCalled)}</span>
                                <span>{percent}%</span>
                            </div>

                            <div className="progress-container">
                                <div className="progress-bar" style={{ width: `${percent}%` }} />
                            </div>

                            <div className="table-wrapper" style={{ marginTop: '0.75rem' }}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Investor / Ref</th>
                                            <th>Called</th>
                                            <th>Funded</th>
                                            <th>Remaining</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {call.items.map((item) => (
                                            <tr key={item.id}>
                                                <td>
                                                    <div>{item.investor_name}</div>
                                                    <span style={{ fontSize: '0.75rem', color: '#60a5fa' }}>
                                                        {item.wire_reference}
                                                    </span>
                                                </td>
                                                <td className="text-money">{formatMoney(item.amount_called)}</td>
                                                <td className="text-money" style={{ color: '#34d399' }}>
                                                    {formatMoney(item.amount_funded)}
                                                </td>
                                                <td className="text-money" style={{ color: parseFloat(item.amount_remaining) > 0 ? '#fbbf24' : 'var(--text-subtle)' }}>
                                                    {formatMoney(item.amount_remaining)}
                                                </td>
                                                <td>
                                                    <span className={`badge badge-${item.status}`}>
                                                        {item.status.replace('_', ' ')}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    );
                })
            )}
        </div>
    );
}
