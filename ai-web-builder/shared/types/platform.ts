export type PlatformType = 'gohighlevel' | 'simvoly' | 'wordpress' | 'custom';

export interface PlatformIntegration {
  id: string;
  user_id: string;
  platform_type: PlatformType;
  connection_status: ConnectionStatus;
  credentials: PlatformCredentials;
  last_sync: string;
  sync_status: SyncStatus;
  account_info: PlatformAccountInfo;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'pending';
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'completed';

export interface PlatformCredentials {
  // GoHighLevel
  ghl_api_key?: string;
  ghl_location_id?: string;
  
  // Simvoly
  simvoly_api_key?: string;
  simvoly_user_id?: string;
  
  // WordPress
  wp_site_url?: string;
  wp_username?: string;
  wp_application_password?: string;
  
  // Encrypted storage
  encrypted_data?: string;
}

export interface PlatformAccountInfo {
  account_name: string;
  account_email: string;
  plan_type?: string;
  usage_limits?: Record<string, number>;
  features_available?: string[];
}

export interface PlatformAnalysis {
  id: string;
  integration_id: string;
  analyzed_at: string;
  summary: AnalysisSummary;
  campaigns: AnalyzedCampaign[];
  recommendations: Recommendation[];
  migration_assessment?: MigrationAssessment;
}

export interface AnalysisSummary {
  total_campaigns: number;
  total_pages: number;
  total_forms: number;
  average_conversion_rate: number;
  top_performing_campaign: string;
  areas_for_improvement: string[];
  ai_confidence_score: number;
}

export interface AnalyzedCampaign {
  platform_id: string;
  name: string;
  type: string;
  status: string;
  performance_score: number;
  issues_found: Issue[];
  improvement_opportunities: ImprovementOpportunity[];
  estimated_uplift: number;
}

export interface Issue {
  type: IssueType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: string;
  fix_effort: 'easy' | 'moderate' | 'complex';
}

export type IssueType = 
  | 'performance'
  | 'accessibility'
  | 'seo'
  | 'mobile_responsiveness'
  | 'conversion_optimization'
  | 'user_experience'
  | 'technical';

export interface ImprovementOpportunity {
  title: string;
  description: string;
  expected_impact: string;
  implementation_effort: 'low' | 'medium' | 'high';
  roi_estimate: number;
  ai_generated_solution?: string;
}

export interface Recommendation {
  id: string;
  type: RecommendationType;
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  implementation_steps: string[];
  expected_results: string;
  ai_generated_code?: string;
  estimated_time_to_implement: number; // hours
}

export type RecommendationType = 
  | 'component_improvement'
  | 'new_component'
  | 'layout_optimization'
  | 'content_enhancement'
  | 'technical_fix'
  | 'migration_suggestion';

export interface MigrationAssessment {
  complexity_score: number; // 1-10
  estimated_time: number; // hours
  estimated_cost: number; // USD
  risk_factors: RiskFactor[];
  migration_strategy: MigrationStrategy;
  timeline: MigrationTimeline[];
}

export interface RiskFactor {
  factor: string;
  impact: 'low' | 'medium' | 'high';
  mitigation_strategy: string;
}

export interface MigrationStrategy {
  approach: 'gradual' | 'parallel' | 'complete_replacement';
  phases: MigrationPhase[];
  rollback_plan: string;
  testing_strategy: string;
}

export interface MigrationPhase {
  phase_number: number;
  name: string;
  description: string;
  deliverables: string[];
  estimated_duration: number; // days
  dependencies: string[];
}

export interface MigrationTimeline {
  date: string;
  milestone: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  details: string;
}