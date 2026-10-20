export interface AssetInfo {
  asset_id: string;
  model: string;
  driver: string;
  de_bearing: string;
  nde_bearing?: string | null;
  iso_class: string;
}

export interface Scenario {
  id: string;
  title: string;
  fault_type: string;
  asset_id: string;
  question: string;
}

export interface TelemetryPoint {
  time_idx: number;
  timestamp: string;
  vibration_rms: number;
  temperature: number;
  motor_current: number;
  discharge_pressure_bar: number;
}

export interface SpectrumPoint {
  freq: number;
  amp: number;
}

export interface CharacteristicFrequency {
  label: string;
  frequency: number;
  color: string;
}

export interface TelemetryResponse {
  asset_id: string;
  fault_type: string;
  telemetry: TelemetryPoint[];
  spectrum: SpectrumPoint[];
  characteristic_frequencies: CharacteristicFrequency[];
  thresholds: {
    vibration_alert: number;
    vibration_trip: number;
    temp_warning: number;
    temp_trip: number;
  };
}

export interface EvidenceItem {
  evidence_id: string;
  source_type: 'sensor' | 'internal' | 'web' | string;
  source_reference: string;
  claim: string;
  supports: string[];
  contradicts: string[];
  confidence_score?: number;
  raw_content?: string;
}

export interface Hypothesis {
  failure_mode: string;
  status: 'supported' | 'plausible' | 'unlikely' | string;
  confidence: number;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  missing_tests: string[];
  explanation: string;
}

export interface MaintenanceAction {
  step_order: number;
  action: string;
  urgency: 'immediate' | 'scheduled' | string;
  requires_loto: boolean;
  safety_hazards: string[];
  parts_to_verify: string[];
  evidence_references: string[];
}

export interface MaintenancePlan {
  plan_title: string;
  required_signoff_role: string;
  actions: MaintenanceAction[];
}

export interface InvestigationResult {
  investigation_id: string;
  asset_id: string;
  verification_status: string;
  approval_status: string;
  primary_hypothesis?: Hypothesis | null;
  evidence_count: number;
  final_report: string;
  state: {
    sensor_findings?: {
      iso_severity?: {
        zone: string;
        severity: string;
        vibration_rms_mm_s: number;
      };
      ml_classification?: {
        predicted_class: string;
        confidence: number;
      };
    };
    hypotheses?: Hypothesis[];
    merged_evidence?: EvidenceItem[];
    maintenance_plan?: MaintenancePlan;
    verification_status?: string;
    approval_status?: string;
    engineer_notes?: string | null;
  };
}

export interface DocumentSection {
  chunk_id: string;
  section: string;
  content: string;
}

export interface DocumentItem {
  document_id: string;
  title: string;
  equipment_model: string;
  document_type: string;
  revision_date: string;
  sections: DocumentSection[];
}

export interface ApprovalPayload {
  decision: 'APPROVED' | 'REJECTED';
  engineer_name: string;
  engineer_role: string;
  comments: string;
}
