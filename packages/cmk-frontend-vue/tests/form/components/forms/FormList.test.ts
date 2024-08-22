import { fireEvent, render, screen } from '@testing-library/vue'
import FormList from '@/form/components/forms/FormList.vue'
import type * as FormSpec from '@/form/components/vue_formspec_components'
import { renderFormWithData } from '../cmk-form-helper'

const stringValidators: FormSpec.Validator[] = [
  {
    type: 'length_in_range',
    min_value: 1,
    max_value: 20,
    error_message: 'String length must be between 1 and 20'
  }
]

const stringFormSpec: FormSpec.String = {
  type: 'string',
  title: 'barTitle',
  help: 'barHelp',
  validators: stringValidators,
  input_hint: ''
}

const spec: FormSpec.List = {
  type: 'list',
  title: 'fooTitle',
  help: 'fooHelp',
  validators: [],
  element_template: stringFormSpec,
  element_default_value: '',
  editable_order: false,
  add_element_label: 'Add element',
  remove_element_label: 'Remove element',
  no_element_label: 'No element'
}

test('FormList renders backend validation messages', async () => {
  render(FormList, {
    props: {
      spec,
      data: [],
      backendValidation: [{ location: [], message: 'Backend error message', invalid_value: '' }]
    }
  })

  screen.getByText('Backend error message')
})

test.skip('FormList updated backend child validation shows validation error', async () => {
  const { rerender } = render(FormList, {
    props: {
      spec,
      data: ['some value'],
      backendValidation: []
    }
  })

  expect(screen.queryByText('Backend error message')).toBeNull()

  await rerender({
    spec,
    data: ['some value'],
    backendValidation: [
      { location: ['0'], message: 'Backend error message', invalid_value: 'other value' }
    ]
  })

  screen.getByText('Backend error message')
  const textbox = screen.getByRole<HTMLInputElement>('textbox')
  expect(textbox.value).toBe('other value')
})

test('FormList local child validation overwrites backend validation', async () => {
  render(FormList, {
    props: {
      spec,
      data: ['some value'],
      backendValidation: [
        { location: ['0'], message: 'Backend error message', invalid_value: 'other value' }
      ]
    }
  })

  const textbox = await screen.findByRole<HTMLInputElement>('textbox')
  await fireEvent.update(textbox, '')

  screen.getByText('String length must be between 1 and 20')
  expect(screen.queryByText('Backend error message')).toBeNull()
})

test('FormList shows frontend validation on existing element', async () => {
  render(FormList, {
    props: {
      spec,
      data: ['some_value'],
      backendValidation: []
    }
  })

  const textbox = await screen.findByRole<HTMLInputElement>('textbox')
  await fireEvent.update(textbox, '')

  screen.getByText('String length must be between 1 and 20')
})

const dictSpec: FormSpec.Dictionary = {
  type: 'dictionary',
  title: 'dictTitle',
  help: 'fooHelp',
  layout: 'one_column',
  validators: [],
  groups: [],
  elements: [
    {
      ident: 'bar',
      required: true,
      default_value: 'baz',
      parameter_form: stringFormSpec
    }
  ]
}

const listSpec: FormSpec.List = {
  type: 'list',
  title: 'fooTitle',
  help: 'fooHelp',
  validators: [],
  element_template: dictSpec,
  element_default_value: {},
  editable_order: false,
  add_element_label: 'Add element',
  remove_element_label: 'Remove element',
  no_element_label: 'No element'
}

test('FormList adds two new elements and enters data', async () => {
  const { getCurrentData } = renderFormWithData({
    spec: listSpec,
    data: [],
    backendValidation: []
  })

  const addElementButton = await screen.getByText('Add element')
  await fireEvent.click(addElementButton)
  await fireEvent.click(addElementButton)

  const element = await screen.getAllByRole('textbox')
  await fireEvent.update(element[0]!, '1234')
  expect(getCurrentData()).toMatch('[{"bar":"1234"},{"bar":"baz"}]')
})
