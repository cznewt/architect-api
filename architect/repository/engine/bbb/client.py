# -*- coding: utf-8 -*-

import os.path
from jinja2 import Environment
from subprocess import Popen,PIPE
from celery.utils.log import get_logger
from architect.repository.client import BaseClient

logger = get_logger(__name__)


class BbbClient(BaseClient):

    def __init__(self, **kwargs):
        super(BbbClient, self).__init__(**kwargs)

    def check_status(self):
        return True

    def get_script_file(self):
        script_file = '{}/script.sh'.format(self.metadata)
        return script_file

    def get_image_types(self):
        return (
            ('bbb-armhf-debian-stretch-4.9', 'BeagleBone Black ARM, Debian Stretch, kernel 4.9'),
            ('bbb-armhf-debian-stretch-4.14', 'BeagleBone Black ARM, Debian Stretch, kernel 4.14'),
            ('bbb-armhf-debian-buster-4.14', 'BeagleBone Black ARM, Debian Buster, kernel 4.14'),
            ('bbx15-armhf-debian-stretch-4.9', 'BeagleBoard X15 ARM, Debian Stretch, kernel 4.9'),
            ('bbx15-armhf-debian-stretch-4.14', 'BeagleBoard X15 ARM, Debian Stretch, kernel 4.14'),
            ('bbx15-armhf-debian-buster-4.14', 'BeagleBoard X15 ARM, Debian Buster, kernel 4.14'),
        )

    def get_script_file(self, config_context):
        platform = config_context['type'].split('-')[0]
        script_file = 'cd {}; ./gen-image.sh {} {} {}'.format(self.metadata['builder_dir'],
                                                              config_context['image_name'],
                                                              config_context['hostname'],
                                                              platform)
        return script_file

    def get_config_file(self, image):
        config_file = '{}/configs/{}.conf'.format(self.metadata['builder_dir'],
                                                  image)
        return config_file

    def get_config_template(self):
        base_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(base_path, "templates/config.sh")
        with open(path) as file_handler:
            data = file_handler.read()
        return data

    def generate_image(self, config_context):
        config_context['repository'] = self.metadata
        script_file = self.get_script_file(config_context)
        config_template = self.get_config_template()
        print(self.metadata)
        config_content = Environment().from_string(config_template).render(config_context)
        with open(self.get_config_file(config_context['image_name']), "w+") as file_handler:
            file_handler.write(config_content)
        Process=Popen(script_file,
                      shell=True,
                      stdin=PIPE,
                      stderr=PIPE)
        print(Process.communicate())
        return True
