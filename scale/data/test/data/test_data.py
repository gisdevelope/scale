from __future__ import unicode_literals

import django

from django.test.testcases import TestCase
from mock import MagicMock

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


class TestData(TestCase):
    """Tests related to the Data class"""

    def setUp(self):
        django.setup()

    def test_add_value(self):
        """Tests calling Data.add_value()"""

        data = Data()

        file_value = FileValue('input_1', [123])
        data.add_value(file_value)

        json_value = JsonValue('input_2', {'foo': 'bar'})
        data.add_value(json_value)

        self.assertSetEqual(set(data.values.keys()), {'input_1', 'input_2'})

        # Duplicate value
        dup_value = FileValue('input_1', [123])
        with self.assertRaises(InvalidData) as context:
            data.add_value(dup_value)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_VALUE')

    def test_add_value_from_output_data(self):
        """Tests calling Data.add_value_from_output_data()"""

        data = Data()
        output_data = Data()

        file_value = FileValue('output_1', [1, 2, 3])
        output_data.add_value(file_value)
        json_value = JsonValue('output_2', 'hello')
        output_data.add_value(json_value)

        data.add_value_from_output_data('input_1', 'output_1', output_data)
        self.assertSetEqual(set(data.values.keys()), {'input_1'})
        self.assertListEqual(data.values['input_1'].file_ids, [1, 2, 3])

        # Duplicate parameter
        with self.assertRaises(InvalidData) as context:
            data.add_value_from_output_data('input_1', 'output_1', output_data)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_VALUE')

        # Missing parameter
        with self.assertRaises(InvalidData) as context:
            data.add_value_from_output_data('input_1', 'output_3', output_data)
        self.assertEqual(context.exception.error.name, 'MISSING_VALUE')

    def test_merge(self):
        """Tests calling Data.validate()"""

        data = Data()
        data.add_value(FileValue('input_1', [123]))
        data.add_value(JsonValue('input_2', 100))
        data.add_value(JsonValue('extra_input_1', 'hello'))
        data.add_value(JsonValue('extra_input_2', 'there'))

        data2 = Data()
        data2.add_value(FileValue('input_1', [125]))
        data2.add_value(FileValue('input_3', [1234]))
        data2.add_value(JsonValue('input_2', 101))
        data2.add_value(JsonValue('extra_input_1', 'hello'))
        data2.add_value(JsonValue('extra_input_2', 'there'))

        data.merge(data2)

        self.assertSetEqual(set(data.values.keys()), {'input_1', 'input_2', 'input_3', 'extra_input_1', 'extra_input_2'})
        self.assertListEqual(data.values['input_1'].file_ids, [123,125])
        self.assertListEqual(data.values['input_2'].value, [100, 101])
        self.assertListEqual(data.values['input_3'].file_ids, [1234])
        self.assertListEqual(data.values['extra_input_1'].value, ['hello', 'hello'])
        self.assertListEqual(data.values['extra_input_2'].value, ['there', 'there'])

        data3 = Data()
        data3.add_value(JsonValue('input_1', 123))

        with self.assertRaises(InvalidData) as context:
            data.merge(data3)

    def test_validate(self):
        """Tests calling Data.validate()"""

        interface = Interface()
        data = Data()

        interface.add_parameter(FileParameter('input_1', ['application/json']))
        interface.add_parameter(JsonParameter('input_2', 'integer'))
        data.add_value(FileValue('input_1', [123]))
        data.add_value(JsonValue('input_2', 100))
        data.add_value(JsonValue('extra_input_1', 'hello'))
        data.add_value(JsonValue('extra_input_2', 'there'))

        # Valid data
        data.validate(interface)
        # Ensure extra data values are removed
        self.assertSetEqual(set(data.values.keys()), {'input_1', 'input_2'})

        # Data is missing required input 3
        interface.add_parameter(FileParameter('input_3', ['image/gif'], required=True))
        with self.assertRaises(InvalidData) as context:
            data.validate(interface)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')

        data.add_value(FileValue('input_3', [999]))  # Input 3 taken care of now

        # Invalid data
        interface.add_parameter(JsonParameter('input_4', 'string'))
        mock_value = MagicMock()
        mock_value.name = 'input_4'
        mock_value.validate.side_effect = InvalidData('MOCK', '')
        data.add_value(mock_value)
        with self.assertRaises(InvalidData) as context:
            data.validate(interface)
        self.assertEqual(context.exception.error.name, 'MOCK')
