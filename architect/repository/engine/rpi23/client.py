# -*- coding: utf-8 -*-

import time
import os.path
from jinja2 import Environment
import subprocess
from architect.repository.client import BaseClient
from architect.repository.models import Resource

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

    def get_image_block_map(self, image_name):
        image_path = '{}/{}.bmap'.format(self.metadata['image_dir'],
                                         image_name)
        with open(image_path) as file_handler:
            return file_handler.read()

    def get_image_content(self, image_name):
        image_path = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        with open(image_path) as file_handler:
            return file_handler.read()

    def get_image_size(self, image_name):
        image_path = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        if os.path.isfile(imagepath):
            return os.path.getsize(image_path)
        else:
            return None

    def delete_image(self, image_name):
        imagepath = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        if os.path.isfile(imagepath):
            os.remove(imagepath)

    def generate_image(self, config_context):
        config_context['repository'] = self.metadata
        script_file = self.get_script_file(config_context)
        config_template = self.get_config_template()
        config_content = Environment().from_string(config_template).render(config_context)
        with open(self.get_config_file(config_context['image_name']), "w+") as file_handler:
            file_handler.write(config_content)
        duration = None
        try:
            start = time.time()
            cmd_output = subprocess.check_output(script_file,
                                                shell=True,
                                                stderr=subprocess.STDOUT).decode('UTF-8')
            end = time.time()
            duration = end - start
        except subprocess.CalledProcessError as ex:
            cmd_output = ex.output.decode('UTF-8')
        imagepath = os.path.join(self.metadata['image_dir'], '{}.img'.format(config_context['image_name']))
        image = Resource.objects.get(name=config_context['image_name'])
        cache = {
            'config': config_content,
            'command': cmd_output,
            'duration': duration
        }
        if os.path.isfile(imagepath):
            image.status = 'active'
            cache['block_map'] = self.get_image_block_map(config_context['image_name'])
            cache['image_size'] = self.get_image_size(config_context['image_name'])
        else:
            image.status = 'error'
            cache['block_map'] = None
        image.cache = cache
        image.save()
        return True
