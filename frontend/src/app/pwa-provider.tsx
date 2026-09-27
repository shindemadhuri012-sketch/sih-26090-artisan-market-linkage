'use client';

import React, { useEffect } from 'react';
import { useSync } from '@/lib/offline/useSync';
import { WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';

export function PWAProvider({ children }: { children: React.ReactNode }) {
  const { isOnline, isSyncing, pendingCount, syncError } = useSync();

  useEffect(() => {
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(
          (reg) => {
            console.log('CraftLink ServiceWorker registered with scope: ', reg.scope);
          },
          (err) => {
            console.warn('CraftLink ServiceWorker registration failed: ', err);
          }
        );
      });
    }
  }, []);

  return (
    <>
      {/* Offline / Sync State Banner */}
      {!isOnline && (
        <div className="bg-amber-600 text-white text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2 sticky top-0 z-50 shadow-sm">
          <WifiOff className="h-3.5 w-3.5" />
          <span>Offline Mode Active. Product drafts and RFQ actions are saved locally in IndexedDB and will synchronize once connectivity returns.</span>
        </div>
      )}

      {isOnline && isSyncing && (
        <div className="bg-blue-600 text-white text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2 sticky top-0 z-50 shadow-sm">
          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          <span>Synchronizing {pendingCount} queued change(s) with server...</span>
        </div>
      )}

      {syncError && isOnline && (
        <div className="bg-rose-700 text-white text-xs font-semibold py-1.5 px-4 text-center flex items-center justify-center gap-2 sticky top-0 z-50 shadow-sm">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Sync Alert: {syncError}</span>
        </div>
      )}

      {children}
    </>
  );
}
