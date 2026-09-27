/**
 * SIH 26090: Dexie 4.x IndexedDB Client
 * Type-safe local storage for authorized read caching and offline mutation queuing.
 */

import Dexie, { Table } from 'dexie';

export interface CachedProduct {
  id: string;
  artisan_id: string;
  title: string;
  sku: string;
  price_inr: number;
  stock_quantity: number;
  monthly_production_capacity: number;
  lead_time_days: number;
  status: string;
  craft_name?: string;
  updated_at: string;
  is_local_draft: boolean;
}

export interface CachedRFQ {
  id: string;
  rfq_reference_number: string;
  buyer_id: string;
  buyer_company_name?: string;
  proposed_quantity: number;
  proposed_unit_price: number;
  currency: string;
  status: string;
  message: string;
  counter_unit_price?: number;
  counter_lead_time_days?: number;
  updated_at: string;
}

export interface OfflineMutation {
  local_id: string;
  idempotency_key: string;
  user_id: string;
  entity_type: 'PRODUCT' | 'PRODUCT_MEDIA' | 'RFQ_RESPONSE';
  entity_id: string;
  operation_type: 'CREATE' | 'UPDATE' | 'DELETE' | 'RESPOND_RFQ';
  payload: Record<string, any>;
  client_created_at: string;
  status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'CONFLICT' | 'REJECTED';
  retry_count: number;
  error_message?: string;
  conflict_details?: Record<string, any>;
}

export class CraftLinkOfflineDB extends Dexie {
  products!: Table<CachedProduct, string>;
  rfqs!: Table<CachedRFQ, string>;
  mutations!: Table<OfflineMutation, string>;

  constructor() {
    super('sih26090_offline_db');
    this.version(1).stores({
      products: 'id, artisan_id, title, status, updated_at, is_local_draft',
      rfqs: 'id, rfq_reference_number, buyer_id, status, updated_at',
      mutations: 'local_id, idempotency_key, user_id, entity_type, status, client_created_at'
    });
  }
}

export const offlineDB = new CraftLinkOfflineDB();

/** Purges all local cached data upon user logout */
export async function clearOfflineStorage(): Promise<void> {
  await offlineDB.products.clear();
  await offlineDB.rfqs.clear();
  await offlineDB.mutations.clear();
}

/** Enqueues a new mutation into the offline queue */
export async function enqueueOfflineMutation(mutation: Omit<OfflineMutation, 'status' | 'retry_count'>): Promise<string> {
  const fullMutation: OfflineMutation = {
    ...mutation,
    status: 'PENDING',
    retry_count: 0
  };
  await offlineDB.mutations.put(fullMutation);
  return fullMutation.local_id;
}

/** Retrieves all mutations pending synchronization */
export async function getPendingMutations(): Promise<OfflineMutation[]> {
  return offlineDB.mutations
    .where('status')
    .equals('PENDING')
    .sortBy('client_created_at');
}
