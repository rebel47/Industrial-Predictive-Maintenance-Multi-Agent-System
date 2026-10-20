import {
  AssetInfo,
  Scenario,
  TelemetryResponse,
  InvestigationResult,
  DocumentItem,
  ApprovalPayload,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${BASE_URL}${url}`;
  const res = await fetch(fullUrl, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorText || res.statusText}`);
  }

  return res.json();
}

export async function getHealth(): Promise<{ status: string; service: string; registered_assets: number }> {
  return fetchJson('/api/v1/health');
}

export async function getAssets(): Promise<AssetInfo[]> {
  return fetchJson('/api/v1/assets');
}

export async function getScenarios(): Promise<Scenario[]> {
  return fetchJson('/api/v1/scenarios');
}

export async function getTelemetry(
  assetId: string = 'P-104',
  faultType: string = 'INNER_RACE_FAULT'
): Promise<TelemetryResponse> {
  return fetchJson(`/api/v1/telemetry?asset_id=${encodeURIComponent(assetId)}&fault_type=${encodeURIComponent(faultType)}`);
}

export async function getDocuments(): Promise<DocumentItem[]> {
  return fetchJson('/api/v1/documents');
}

export async function runInvestigation(
  assetId: string,
  userQuestion: string,
  faultType?: string,
  telemetryOverride?: any
): Promise<InvestigationResult> {
  return fetchJson('/api/v1/investigate', {
    method: 'POST',
    body: JSON.stringify({
      asset_id: assetId,
      user_question: userQuestion,
      fault_type: faultType,
      telemetry_override: telemetryOverride,
    }),
  });
}

export async function submitApproval(
  invId: string,
  payload: ApprovalPayload
): Promise<{ investigation_id: string; approval_status: string; audit_entry: string }> {
  return fetchJson(`/api/v1/investigate/${encodeURIComponent(invId)}/approve`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getInvestigation(invId: string): Promise<any> {
  return fetchJson(`/api/v1/investigate/${encodeURIComponent(invId)}`);
}
