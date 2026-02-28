import type { RJSFSchema, UiSchema } from '@rjsf/utils';

export interface FieldUIHints {
  widget?: 'textarea' | 'slider' | 'rating' | 'radio' | 'checkbox' | 'file';
  minDate?: string;
  maxDate?: string;
  accept?: string;
  maxFiles?: number;
  maxSize?: number;
}

export interface WidgetCardDefinition {
  title: string;
  description: string;
  icon?: string;
  color?: string;
  schema: RJSFSchema;
  uiSchema?: UiSchema;
  display?: boolean;
}
