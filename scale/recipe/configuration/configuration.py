"""Defines the class that represents a job configuration"""
from __future__ import unicode_literals

from job.execution.configuration.volume import HOST_TYPE, VOLUME_TYPE, Volume
from recipe.configuration.exceptions import InvalidRecipeConfiguration


DEFAULT_PRIORITY = 100


class RecipeConfiguration(object):
    """Represents the configuration for running a recipe"""

    def __init__(self):
        """Constructor
        """

        # Recipes can be configured to have a main (default) workspace for all output files, as well as have a specific
        # workspace for each output name
        self.default_output_workspace = None
        self.output_workspaces = {}  # {Output name: Workspace name}

        self.priority = DEFAULT_PRIORITY

        self.mounts = {}  # {Name: MountConfig}
        self.settings = {}  # {Name: Value}

    def add_mount(self, mount_config):
        """Adds the given mount configuration

        :param mount_config: The mount configuration to add
        :type mount_config: :class:`job.configuration.mount.MountConfig`

        :raises :class:`recipe.configuration.exceptions.InvalidRecipeConfiguration`: If the mount is a duplicate
        """

        if mount_config.name in self.mounts:
            raise InvalidRecipeConfiguration('DUPLICATE_MOUNT', 'Duplicate mount \'%s\'' % mount_config.name)

        self.mounts[mount_config.name] = mount_config

    def add_output_workspace(self, output, workspace):
        """Adds the given output_workspace

        :param output: The output name
        :type output: string
        :param workspace: The workspace name
        :type workspace: string

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the output is a duplicate
        """

        if output in self.output_workspaces:
            raise InvalidRecipeConfiguration('DUPLICATE_WORKSPACE', 'Duplicate output workspace \'%s\'' % output)

        self.output_workspaces[output] = workspace

    def add_setting(self, setting_name, setting_value):
        """Adds the given setting value

        :param setting_name: The setting name
        :type setting_name: string
        :param setting_value: The setting value
        :type setting_value: string

        :raises :class:`recipe.configuration.exceptions.InvalidJobConfiguration`: If the setting is a duplicate or invalid
        """

        if setting_name in self.settings:
            raise InvalidRecipeConfiguration('DUPLICATE_SETTING', 'Duplicate setting \'%s\'' % setting_name)
        if setting_value is None:
            msg = 'The value for setting \'%s\' must be a non-empty string'
            raise InvalidRecipeConfiguration('INVALID_SETTING', msg % setting_name)

        self.settings[setting_name] = setting_value

    def get_mount_volume(self, mount_name, volume_name, container_path, mode):
        """Returns the volume that has been configured for the given mount name. If the given mount is not defined in
        this configuration, None is returned.

        :param mount_name: The name of the mount defined in the job type
        :type mount_name: string
        :param volume_name: The name of the volume
        :type volume_name: string
        :param container_path: The path within the container onto which the volume will be mounted
        :type container_path: string
        :param mode: Either 'ro' for read-only or 'rw' for read-write
        :type mode: string
        :returns: The volume that should be mounted into the job container, possibly None
        :rtype: :class:`job.execution.configuration.volume.Volume`
        """

        if mount_name not in self.mounts:
            return None

        volume = None
        mount_config = self.mounts[mount_name]
        mount_type = mount_config.mount_type
        if mount_type == HOST_TYPE:
            host_path = mount_config.host_path
            volume = Volume(volume_name, container_path, mode, is_host=True, host_path=host_path)
        elif mount_type == VOLUME_TYPE:
            driver = mount_config.driver
            driver_opts = mount_config.driver_opts
            volume = Volume(volume_name, container_path, mode, is_host=False, driver=driver, driver_opts=driver_opts)

        return volume

    def get_output_workspace(self, output):
        """Returns the name of the output workspace that is configured to store the products for the given output name,
        possibly None

        :param output: The name of the output
        :type output: string
        :returns: The name of the workspace for storing the output products, possibly None
        :rtype: string
        """

        workspace = None

        if output in self.output_workspaces:
            workspace = self.output_workspaces[output]
        elif self.default_output_workspace:
            workspace = self.default_output_workspace

        return workspace

    def get_setting_value(self, name):
        """Returns the value of the given setting if defined in this configuration, otherwise returns None

        :param name: The name of the setting
        :type name: string
        :returns: The value of the setting, possibly None
        :rtype: string
        """

        if name in self.settings:
            return self.settings[name]

        return None

    def remove_secret_settings(self, manifest):
        """Removes and returns the secret setting values from this recipe configuration

        :param manifest: The Seed manifest
        :type manifest: :class:`job.seed.manifest.SeedManifest`
        :returns: A dict of secret settings where the key is the setting name and the value is the secret setting value
        :rtype: dict
        """

        secret_settings = {}

        for setting_dict in manifest.get_settings():
            if 'secret' in setting_dict and setting_dict['secret']:
                name = setting_dict['name']
                if name in self.settings:
                    secret_settings[name] = self.settings[name]
                    del self.settings[name]

        return secret_settings