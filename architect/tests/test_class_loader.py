
import pytest

from architect.utils import get_module
from django.conf import settings

modules_list = []

# for module_label, module_class in settings.INVENTORY_CLASS_MAPPINGS.items():
#     modules_list.append(('inventory', module_label, module_class))

for module_label, module_class in settings.MANAGER_CLASS_MAPPINGS.items():
    modules_list.append(('manager', module_label, module_class))

for module_label, module_class in settings.MONITOR_CLASS_MAPPINGS.items():
    modules_list.append(('monitor', module_label, module_class))


@pytest.mark.parametrize("module_type,module_key,module_class", modules_list)
def test_load_module(module_type, module_key, module_class):
    assert get_module(module_key,
                      module_type).__name__ == module_class.split('.')[-1]
