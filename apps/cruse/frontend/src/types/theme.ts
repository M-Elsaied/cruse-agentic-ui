export interface CssDoodleTheme {
  type: 'css-doodle';
  grid: string;
  seed?: string | null;
  rules: string;
  vars?: Record<string, string>;
  description?: string;
}

export interface GradientColorStop {
  color: string;
  stop: string;
}

export interface GradientTheme {
  type: 'gradient';
  mode: 'linear' | 'radial' | 'conic';
  angle?: string;
  shape?: string;
  colors: GradientColorStop[];
  description?: string;
}

export type BackgroundTheme = CssDoodleTheme | GradientTheme;
