# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from architect.inventory.models import Inventory
from architect.manager.engine.saltstack.client import SaltStackClient
from architect.manager.models import Manager
from celery.utils.log import get_logger

logger = get_logger(__name__)


class ProcessEventView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessEventView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_kwargs = {
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        }
        update_client = SaltStackClient(**manager_kwargs)
        metadata['manager'] = kwargs.get('master_id')
        update_client.process_resource_metadata('salt_event', metadata)
        cache_client = SaltStackClient(**manager_kwargs)
        cache_client.refresh_cache()
        return JsonResponse({'success': 'Event synced.'})


class ProcessMinionView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessMinionView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        manager = Manager.objects.get(name=kwargs.get('master_id'))
        for minion_id, minion_data in data.items():
            client = manager.client()
            client.process_resource_metadata('salt_minion', {minion_id: minion_data['grain']})
            client.process_resource_metadata('salt_service', {minion_id: minion_data['pillar']})
            client.process_resource_metadata('salt_lowstate', {minion_id: minion_data['lowstate']})
            client.process_relation_metadata()
            client.save()
        return JsonResponse({'success': 'Minion metadata synced.'})


class ProcessClassView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessClassView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        inventory = Inventory.objects.get(name=kwargs.get('master_id'))
        inventory.client().classify_node(data['name'], data['data'])
        return JsonResponse({'success': 'Node classified.'})
