export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  subscription_tier: SubscriptionTier;
  created_at: string;
  updated_at: string;
  settings: UserSettings;
  usage_stats: UsageStats;
}

export type SubscriptionTier = 'freemium' | 'creator' | 'business' | 'agency';

export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: NotificationSettings;
  ai_preferences: AIPreferences;
  brand_settings?: BrandSettings;
}

export interface NotificationSettings {
  email_notifications: boolean;
  campaign_updates: boolean;
  billing_alerts: boolean;
  feature_announcements: boolean;
}

export interface AIPreferences {
  preferred_style: 'minimal' | 'modern' | 'classic' | 'bold';
  animation_level: 'none' | 'subtle' | 'smooth' | 'energetic';
  responsiveness_priority: 'mobile' | 'desktop' | 'balanced';
  accessibility_mode: boolean;
}

export interface BrandSettings {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  logo_url?: string;
  brand_guidelines?: string;
}

export interface UsageStats {
  campaigns_generated: number;
  campaigns_this_month: number;
  ai_credits_used: number;
  ai_credits_remaining: number;
  last_active: string;
}