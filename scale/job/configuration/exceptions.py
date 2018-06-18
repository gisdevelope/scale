"""Defines exceptions that can occur when interacting with configuration"""
from __future__ import unicode_literals

from error.exceptions import ScaleError
from util.exceptions import ValidationException


class InvalidExecutionConfiguration(Exception):
    """Exception indicating that the provided execution configuration JSON was invalid
    """

    pass


class InvalidJobConfiguration(ValidationException):
    """Exception indicating that the provided job configuration was invalid
    """

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidJobConfiguration, self).__init__(name, description)


class MissingMount(ScaleError):
    """Error class indicating that a required mount volume is missing
    """

    def __init__(self, name):
        """Constructor

        :param name: The name of the missing mount
        :type name: string
        """

        super(MissingMount, self).__init__(10, 'missing-mount')
        self.name = name

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'Required mount %s was not provided' % self.name


class MissingSetting(ScaleError):
    """Error class indicating that a required setting value is missing
    """

    def __init__(self, setting):
        """Constructor

        :param setting: The name of the missing setting
        :type setting: string
        """

        super(MissingSetting, self).__init__(6, 'missing-setting')
        self.setting = setting

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'Required setting %s was not provided' % self.setting
