from __future__ import unicode_literals

import django
from django.test import TestCase, TransactionTestCase
from mock import patch

import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from ingest.models import Ingest, Strike
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from storage.exceptions import InvalidDataTypeTag


class TestIngestAddDataTypeTag(TestCase):
    def setUp(self):
        django.setup()

    def test_valid(self):
        """Tests calling add_data_type_tag() with valid tags"""

        ingest = Ingest()
        ingest.add_data_type_tag('Hello1')
        ingest.add_data_type_tag('foo_BAR')
        tags = ingest.get_data_type_tags()

        correct_set = set()
        correct_set.add('Hello1')
        correct_set.add('foo_BAR')

        self.assertSetEqual(tags, correct_set)

    def test_same_tag(self):
        """Tests calling add_data_type_tag() with the same tag twice"""

        ingest = Ingest()
        ingest.add_data_type_tag('Hello1')
        ingest.add_data_type_tag('Hello1')
        tags = ingest.get_data_type_tags()

        correct_set = set()
        correct_set.add('Hello1')

        self.assertSetEqual(tags, correct_set)


class TestIngestGetDataTypeTags(TestCase):
    def setUp(self):
        django.setup()

    def test_tags(self):
        """Tests calling get_data_type_tags() with tags"""

        ingest = Ingest(data_type_tags=['A','B','c'])
        tags = ingest.get_data_type_tags()

        correct_set = set()
        correct_set.add('A')
        correct_set.add('B')
        correct_set.add('c')

        self.assertSetEqual(tags, correct_set)

    def test_no_tags(self):
        """Tests calling get_data_type_tags() with no tags"""

        ingest = Ingest()
        tags = ingest.get_data_type_tags()

        self.assertSetEqual(tags, set())


class TestStrikeManagerCreateStrikeProcess(TransactionTestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()
        add_message_backend(AMQPMessagingBackend)

        self.workspace = storage_test_utils.create_workspace()
        self.recipe = recipe_test_utils.create_recipe_type_v6()

    @patch('ingest.models.CommandMessageManager')
    def test_successful_v6(self, mock_msg_mgr):
        """Tests calling StrikeManager.create_strike successfully with v6 config"""

        config = {
            'version': '6',
            'workspace': self.workspace.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'foo',
                'data_types': ['test1','test2'],
                'new_workspace': self.workspace.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': self.recipe.name,
                'revision_num': self.recipe.revision_num
            },
        }

        config = StrikeConfigurationV6(config).get_configuration()
        strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)
        self.assertEqual(strike.job.status, 'QUEUED')
        
    @patch('ingest.models.CommandMessageManager')
    def test_update_strike(self, mock_msg_mgr):
        """Tests calling StrikeManager.create_strike successfully with v6 config"""

        config = {
            'version': '6',
            'workspace': self.workspace.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'foo',
                'data_types': ['test1','test2'],
                'new_workspace': self.workspace.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': self.recipe.name,
                'revision_num': self.recipe.revision_num
            },
        }

        config = StrikeConfigurationV6(config).get_configuration()
        strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)
        self.assertEqual(strike.job.status, 'QUEUED')
        config = {
                    'version': '6',
                    'workspace': self.workspace.name,
                    'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
                    'files_to_ingest': [{
                        'filename_regex': 'foo',
                        'data_types': ['test1','test2'],
                        'new_workspace': self.workspace.name,
                        'new_file_path': 'my/new_path'
                    }],
                    'recipe': {
                        'name': self.recipe.name,
                        'revision_num': self.recipe.revision_num
                    },
                }
        config = StrikeConfigurationV6(config).get_configuration()
        Strike.objects.edit_strike(strike.id, 'my_title2', 'my_description2', config)
        strike = Strike.objects.get_details(strike.id)
        self.assertEqual(strike.title, 'my_title2')
        self.assertEqual(strike.description, 'my_description2')
        self.assertEqual(strike.configuration['files_to_ingest'][0]['new_file_path'], 'my/new_path')




