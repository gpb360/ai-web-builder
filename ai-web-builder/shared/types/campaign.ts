import { PlatformType } from './platform';

export interface Campaign {
  id: string;
  user_id: string;
  name: string;
  description: string;
  status: CampaignStatus;
  type: CampaignType;
  platform_source?: PlatformType;
  created_at: string;
  updated_at: string;
  launched_at?: string;
  analytics: CampaignAnalytics;
  components: CampaignComponent[];
  settings: CampaignSettings;
}

export type CampaignStatus = 'draft' | 'generating' | 'ready' | 'launched' | 'paused' | 'archived';

export type CampaignType = 
  | 'landing_page' 
  | 'funnel' 
  | 'email_sequence' 
  | 'complete_campaign'
  | 'component_enhancement';

export interface CampaignComponent {
  id: string;
  name: string;
  type: ComponentType;
  code: string;
  props: ComponentProps;
  preview_url?: string;
  analytics: ComponentAnalytics;
  ai_metadata: AIGenerationMetadata;
}

export type ComponentType = 
  | 'landing_page'
  | 'form'
  | 'header'
  | 'footer'
  | 'hero_section'
  | 'testimonials'
  | 'pricing'
  | 'email_template'
  | 'popup'
  | 'navigation'
  | 'custom';

export interface ComponentProps {
  [key: string]: any;
  className?: string;
  style?: Record<string, any>;
  children?: ComponentProps[];
}

export interface CampaignAnalytics {
  views: number;
  conversions: number;
  conversion_rate: number;
  bounce_rate: number;
  average_session_duration: number;
  revenue_generated: number;
  cost_per_acquisition: number;
}

export interface ComponentAnalytics {
  views: number;
  clicks: number;
  click_through_rate: number;
  conversions: number;
  conversion_rate: number;
  engagement_score: number;
}

export interface CampaignSettings {
  target_audience: string;
  business_type: string;
  goals: string[];
  brand_guidelines?: string;
  performance_requirements?: PerformanceRequirements;
  export_format?: ExportFormat[];
}

export interface PerformanceRequirements {
  max_load_time: number;
  accessibility_level: 'AA' | 'AAA';
  seo_optimization: boolean;
  mobile_optimization: boolean;
}

export type ExportFormat = 'react' | 'html_css' | 'gohighlevel' | 'simvoly' | 'wordpress';

export interface AIGenerationMetadata {
  model_used: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost: number;
  generation_time: number;
  iterations: number;
  user_feedback?: UserFeedback;
}

export interface UserFeedback {
  rating: number; // 1-5
  feedback_text?: string;
  improvements_requested?: string[];
  accepted: boolean;
}