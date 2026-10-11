import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import CsvUploader from './components/CsvUploader';
import TransactionTable from './components/TransactionTable';
import LineItemsPanel from './components/LineItemsPanel';
import {
  getOrganizations,
  getTransactions,
  getLineItems,
  importBankStatement,
  approveMatch,
  rejectMatch,
  ignoreTransaction,
} from './api';

export default function App() {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState('northwind');
  const [transactions, setTransactions] = useState([]);
  const [lineItems, setLineItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadOrganizations = async () => {
    try {
      const orgs = await getOrganizations();
      setOrganizations(orgs);
      if (orgs.length > 0 && !orgs.some((o) => o.slug === currentOrg)) {
        setCurrentOrg(orgs[0].slug);
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const loadData = useCallback(async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [txs, items] = await Promise.all([
        getTransactions(currentOrg),
        getLineItems(currentOrg),
      ]);
      setTransactions(txs);
      setLineItems(items);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [currentOrg]);

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpload = async (file) => {
    setUploadLoading(true);
    try {
      const summary = await importBankStatement(currentOrg, file);
      showToast(`Imported ${summary.imported_count} rows successfully!`);
      await loadData();
      return summary;
    } catch (err) {
      showToast(err.message, 'error');
      throw err;
    } finally {
      setUploadLoading(false);
    }
  };

  const handleApprove = async (matchId) => {
    setActionLoadingId(matchId);
    try {
      await approveMatch(currentOrg, matchId);
      showToast('Match approved and reconciled!');
      await loadData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (matchId) => {
    setActionLoadingId(matchId);
    try {
      await rejectMatch(currentOrg, matchId);
      showToast('Match rejected.');
      await loadData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleIgnore = async (txId) => {
    setActionLoadingId(txId);
    try {
      await ignoreTransaction(currentOrg, txId);
      showToast('Transaction ignored.');
      await loadData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        organizations={organizations}
        currentOrg={currentOrg}
        onSelectOrg={setCurrentOrg}
        onRefresh={loadData}
        loading={loading}
      />

      <main className="main-content">
        <CsvUploader onUpload={handleUpload} loading={uploadLoading} />

        <div className="dashboard-grid">
          <div>
            <TransactionTable
              transactions={transactions}
              onApprove={handleApprove}
              onReject={handleReject}
              onIgnore={handleIgnore}
              actionLoadingId={actionLoadingId}
            />
          </div>

          <div>
            <LineItemsPanel lineItems={lineItems} />
          </div>
        </div>
      </main>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
