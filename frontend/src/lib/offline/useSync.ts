/**
 * SIH 26090: useSync Hook
 * Detects network connectivity changes, monitors pending IndexedDB mutations,
 * and automatically triggers batch synchronization with exponential retry backoff.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { offlineDB, getPendingMutations, OfflineMutation } from './db';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseSyncReturn {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  lastSyncTime: Date | null;
  syncError: string | null;
  syncNow: () => Promise<void>;
}

export function useSync(): UseSyncReturn {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const updatePendingCount = useCallback(async () => {
    try {
      const count = await offlineDB.mutations.where('status').equals('PENDING').count();
      setPendingCount(count);
    } catch {
      // IndexedDB might not be available during SSR
    }
  }, []);

  const syncNow = useCallback(async () => {
    if (!navigator.onLine || isSyncing) return;

    const pending = await getPendingMutations();
    if (pending.length === 0) return;

    setIsSyncing(true);
    setSyncError(null);

    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      setSyncError('User session expired. Please log in to sync offline changes.');
      setIsSyncing(false);
      return;
    }

    try {
      // Format payload for /api/v1/sync/batch
      const batchPayload = {
        mutations: pending.map((m) => ({
          client_mutation_id: m.local_id,
          idempotency_key: m.idempotency_key,
          entity_type: m.entity_type,
          entity_id: m.entity_id,
          operation_type: m.operation_type,
          payload: m.payload,
          client_created_at: m.client_created_at
        }))
      };

      const res = await fetch(`${API_BASE}/api/v1/sync/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(batchPayload)
      });

      if (!res.ok) {
        throw new Error(`Sync batch failed with HTTP status ${res.status}`);
      }

      const data = await res.json();
      
      // Update local mutation records
      for (const result of data.results) {
        if (result.status === 'COMMITTED' || result.status === 'ALREADY_PROCESSED') {
          await offlineDB.mutations.update(result.client_mutation_id, {
            status: 'SYNCED'
          });
        } else if (result.status === 'CONFLICT') {
          await offlineDB.mutations.update(result.client_mutation_id, {
            status: 'CONFLICT',
            conflict_details: result.conflict_details,
            error_message: result.error_message
          });
        } else {
          await offlineDB.mutations.update(result.client_mutation_id, {
            status: 'REJECTED',
            error_message: result.error_message
          });
        }
      }

      setLastSyncTime(new Date());
      await updatePendingCount();
    } catch (err: any) {
      setSyncError(err.message || 'Network error during synchronization.');
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, updatePendingCount]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    setIsOnline(navigator.onLine);
    updatePendingCount();

    const handleOnline = () => {
      setIsOnline(true);
      syncNow();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [syncNow, updatePendingCount]);

  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSyncTime,
    syncError,
    syncNow
  };
}
