# -*- coding: utf-8 -*-

import time
import os.path
from jinja2 import Environment
import subprocess
from celery.utils.log import get_logger
from architect.repository.client import BaseClient
from architect.repository.models import Resource

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
        script_file = 'cd {}; ./gen-image.sh {} {} {} {}'.format(self.metadata['builder_dir'],
                                                                 config_context['image_name'],
                                                                 config_context['hostname'],
                                                                 platform,
                                                                 self.metadata['image_dir'])
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

    def get_image_block_map(self, image_name):
        map_path = '{}/{}.bmap'.format(self.metadata['image_dir'],
                                       image_name)
        if os.path.isfile(map_path):
            with open(map_path) as file_handler:
                return file_handler.read()
        return None

    def get_image_content(self, image_name):
        image_path = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        with open(image_path) as file_handler:
            return file_handler.read()

    def get_image_size(self, image_name):
        image_path = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        if os.path.isfile(image_path):
            return os.path.getsize(image_path)
        else:
            return None

    def delete_image(self, image_name):
        image_path = '{}/{}.img'.format(self.metadata['image_dir'],
                                        image_name)
        map_path = '{}/{}.bmap'.format(self.metadata['image_dir'],
                                       image_name)
        if os.path.isfile(image_path):
            os.remove(image_path)
        if os.path.isfile(map_path):
            os.remove(map_path)


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
        image_path = os.path.join(self.metadata['image_dir'], '{}.img'.format(config_context['image_name']))
        image = Resource.objects.get(name=config_context['image_name'])
        cache = {
            'config': config_content,
            'command': cmd_output,
            'duration': duration
        }
        if os.path.isfile(image_path):
            image.status = 'active'
            cache['block_map'] = self.get_image_block_map(config_context['image_name'])
            cache['image_size'] = self.get_image_size(config_context['image_name'])
        else:
            image.status = 'error'
            cache['block_map'] = None
        image.cache = cache
        image.save()

        return True
