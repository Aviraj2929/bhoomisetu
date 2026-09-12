export interface ExtractedField {
  field_id: string;
  field_name: string;
  raw_value: string;
  normalized_value: string;
  confidence: number;
  source_bbox: number[]; // [x_min, y_min, x_max, y_max]
  source_page: number;
  is_verified: boolean;
  warning?: string | null;
}

export interface DocumentVerificationTask {
  document_id: string;
  filename: string;
  status: string;
  overall_confidence: number;
  image_url: string;
  fields: ExtractedField[];
}

export interface DashboardMetrics {
  total_documents: number;
  auto_approved: number;
  needs_verification: number;
  human_verified: number;
  auto_approval_rate: string;
  avg_processing_time_sec: number;
  avg_field_confidence: number;
  action_required: {
    pending_verifications: number;
    validation_failures: number;
    duplicate_suspects: number;
  };
}
