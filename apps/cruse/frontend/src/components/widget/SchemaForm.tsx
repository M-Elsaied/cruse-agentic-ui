'use client';

import { useCallback, useMemo } from 'react';
import Form from '@rjsf/mui';
import type { RJSFSchema, UiSchema, RegistryWidgetsType, IChangeEvent, ObjectFieldTemplateProps } from '@rjsf/utils';
import validator from '@rjsf/validator-ajv8';
import { motion } from 'framer-motion';
import { SliderField } from '@/components/widget/fields/SliderField';
import { RatingField } from '@/components/widget/fields/RatingField';
import { FileUploadField } from '@/components/widget/fields/FileUploadField';
import { DateField } from '@/components/widget/fields/DateField';
import { MultiSelectField } from '@/components/widget/fields/MultiSelectField';

interface SchemaFormProps {
  schema: RJSFSchema;
  formData: Record<string, unknown>;
  onChange: (formData: Record<string, unknown>) => void;
}

/**
 * Build a uiSchema from the JSON Schema's x-ui hints.
 * Maps widget agent's x-ui.widget values to RJSF widget names or custom widgets.
 */
function buildUiSchema(schema: RJSFSchema): UiSchema {
  const uiSchema: UiSchema = {
    'ui:submitButtonOptions': { norender: true },
  };
  const properties = schema.properties || {};

  for (const [key, fieldSchema] of Object.entries(properties)) {
    const field = fieldSchema as Record<string, any>;
    const xui = field['x-ui'] || {};
    const widgetHint: string | undefined = xui.widget;

    if (widgetHint === 'textarea') {
      uiSchema[key] = { 'ui:widget': 'textarea' };
    } else if (widgetHint === 'slider') {
      uiSchema[key] = { 'ui:widget': 'slider' };
    } else if (widgetHint === 'rating') {
      uiSchema[key] = { 'ui:widget': 'rating' };
    } else if (widgetHint === 'radio') {
      uiSchema[key] = { 'ui:widget': 'radio' };
    } else if (widgetHint === 'checkbox') {
      uiSchema[key] = { 'ui:widget': 'checkbox' };
    } else if (widgetHint === 'file') {
      uiSchema[key] = { 'ui:widget': 'file' };
    } else if (field.format === 'date' || field.format === 'date-time') {
      uiSchema[key] = { 'ui:widget': 'date' };
    } else if (
      field.type === 'array' &&
      field.items?.enum
    ) {
      uiSchema[key] = { 'ui:widget': 'multiselect' };
    }
  }

  return uiSchema;
}

function StaggeredObjectFieldTemplate(props: ObjectFieldTemplateProps) {
  return (
    <div>
      {props.title && <legend>{props.title}</legend>}
      {props.description && <p>{props.description}</p>}
      {props.properties.map((prop, index) => (
        <motion.div
          key={prop.name}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: index * 0.08, ease: 'easeOut' }}
        >
          {prop.content}
        </motion.div>
      ))}
    </div>
  );
}

const customWidgets: RegistryWidgetsType = {
  slider: SliderField,
  rating: RatingField,
  file: FileUploadField,
  date: DateField,
  multiselect: MultiSelectField,
};

export function SchemaForm({ schema, formData, onChange }: SchemaFormProps) {
  const uiSchema = useMemo(() => buildUiSchema(schema), [schema]);

  const handleChange = useCallback(
    (e: IChangeEvent) => {
      if (e.formData) {
        onChange(e.formData);
      }
    },
    [onChange]
  );

  return (
    <Form
      schema={schema}
      uiSchema={uiSchema}
      formData={formData}
      validator={validator}
      widgets={customWidgets}
      templates={{ ObjectFieldTemplate: StaggeredObjectFieldTemplate }}
      onChange={handleChange}
      liveValidate={false}
      showErrorList={false}
      noHtml5Validate
    />
  );
}
