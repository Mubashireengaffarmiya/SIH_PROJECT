// API type definitions for SMART-LM

export interface OCRWord {
  text: string;
  confidence: number;
  bbox: [number, number, number, number];
}

export interface OCRResult {
  words: OCRWord[];
  full_text: string;
  engine: string;
  success: boolean;
  error: string | null;
}

export interface ImageQualityResult {
  quality: 'GOOD' | 'ACCEPTABLE' | 'POOR';
  blur_score: number;
  brightness: number;
  contrast: number;
  message: string;
  width: number;
  height: number;
}

export interface ExtractedField {
  value: string | null;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  evidence_text: string | null;
}

export interface ExtractionResult {
  product_name: ExtractedField;
  mrp: ExtractedField;
  net_quantity: ExtractedField;
  manufacturer: ExtractedField;
  manufacturing_date: ExtractedField;
  consumer_care: ExtractedField;
  country_of_origin: ExtractedField;
  best_before: ExtractedField;
  unit_sale_price: ExtractedField;
}

export interface VLMField {
  value: string | null;
  confidence: number | null;
  evidence_text: string | null;
  source_image: string | null;
  bounding_box: unknown[] | null;
  status: string;
}

export interface VLMResult {
  status: string;
  engine: string;
  pipeline_version: string | null;
  fields: Record<string, VLMField>;
  source_image: string | null;
  error: string | null;
}

export interface HybridField {
  ocr_value: string | null;
  vlm_value: string | null;
  final_value: string | null;
  status: string;
  needs_review: boolean;
}

export type ComplianceStatus = 'COMPLIANT' | 'NON-COMPLIANT' | 'NEEDS REVIEW' | 'NOT APPLICABLE' | 'NOT VERIFIABLE';

export interface RuleEvaluation {
  requirement: string;
  extracted_value: string | null;
  expected_requirement: string;
  rule_reference: string;
  evidence: string | null;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  result: ComplianceStatus;
}

export interface ComplianceResult {
  overall_status: ComplianceStatus;
  overall_confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  evaluations: RuleEvaluation[];
  summary: string;
}

export interface AnalysisResponse {
  inspection_id: string;
  image_quality: ImageQualityResult;
  ocr: OCRResult;
  extraction: ExtractionResult;
  vlm: VLMResult;
  hybrid_extraction: Record<string, HybridField>;
  compliance: ComplianceResult;
  created_at: string;
  is_demo: boolean;
}

export interface InspectionSummary {
  inspection_id: string;
  created_at: string;
  product_name: string | null;
  status: ComplianceStatus;
  overall_confidence: string | null;
  image_quality: string | null;
  violation_count: number;
  is_demo: boolean;
}

export interface DeclarationOut {
  field_name: string;
  extracted_value: string | null;
  confidence: string | null;
  status: string | null;
  evidence_text: string | null;
}

export interface RuleEvaluationOut {
  requirement: string;
  extracted_value: string | null;
  expected_requirement: string;
  rule_reference: string;
  evidence: string | null;
  confidence: string | null;
  result: ComplianceStatus;
}

export interface InspectionDetail {
  inspection_id: string;
  created_at: string;
  product_name: string | null;
  status: ComplianceStatus;
  overall_confidence: string | null;
  image_quality: string | null;
  image_path: string | null;
  is_demo: boolean;
  declarations: DeclarationOut[];
  evaluations: RuleEvaluationOut[];
}

export interface DashboardStats {
  total: number;
  compliant: number;
  violations: number;
  needs_review: number;
  recent: InspectionSummary[];
}
