export interface Component {
  id: string;
  name: string;
  code: string;
  framework: 'react' | 'vue' | 'svelte';
  props: ComponentProp[];
  preview_url?: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  category: string;
}

export interface ComponentProp {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  default_value?: any;
  description?: string;
}

export interface ComponentGenerationRequest {
  prompt: string;
  style_preferences?: StylePreferences;
  framework: 'react' | 'vue' | 'svelte';
  reference_image?: File;
}

export interface StylePreferences {
  theme: 'light' | 'dark' | 'auto';
  color_scheme?: string[];
  animation_level: 'none' | 'subtle' | 'smooth' | 'energetic';
  responsiveness: boolean;
  accessibility: boolean;
}