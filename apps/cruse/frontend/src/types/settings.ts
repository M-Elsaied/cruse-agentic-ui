export interface KeyInfo {
  provider: string;
  label: string | null;
  key_hint: string | null;
  is_valid: boolean;
  created_at: string | null;
}

export interface KeyListResponse {
  keys: KeyInfo[];
  supported_providers: string[];
}

export interface KeyStoreResponse {
  provider: string;
  key_hint: string | null;
  message: string;
}

export interface KeyValidateResponse {
  valid: boolean;
  message: string;
}

export interface PreferenceResponse {
  preferred_provider: string | null;
  preferred_model: string | null;
  settings: Record<string, unknown>;
}
