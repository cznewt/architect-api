# -*- coding: utf-8 -*-

import os.path
from jinja2 import Environment
from subprocess import Popen,PIPE
from architect.repository.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class Rpi23Client(BaseClient):

    def __init__(self, **kwargs):
        super(Rpi23Client, self).__init__(**kwargs)

    def check_status(self):
        return True

    def get_image_types(self):
        return (
            ('rpi2-armhf-debian-stretch-4.9', 'Raspberry Pi 2 ARM, Debian Stretch, kernel 4.9'),
            ('rpi3-armhf-debian-stretch-4.9', 'Raspberry Pi 3 ARM, Debian Stretch, kernel 4.9'),
            ('rpi3-arm64-debian-stretch-4.9', 'Raspberry Pi 3 ARM64, Debian Stretch, kernel 4.9'),
        )

    def get_script_file(self, config_context):
        script_file = 'cd {}; ./gen-image.sh {}'.format(self.metadata['builder_dir'],
                                                        config_context['image_name'])
        return script_file

    def get_config_file(self, image):
        config_file = '{}/templates/{}'.format(self.metadata['builder_dir'],
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
        config_content = Environment().from_string(config_template).render(config_context)
        with open(self.get_config_file(config_context['image_name']), "w+") as file_handler:
            file_handler.write(config_content)
        Process=Popen(script_file,
                      shell=True,
                      stdin=PIPE,
                      stderr=PIPE)
        print(Process.communicate())
        return True
