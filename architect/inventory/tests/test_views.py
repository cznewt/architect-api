
import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize("view", ["inventory:inventory_list"])
def test_view_inventory_list(client, view):
    url = reverse(view)
    response = client.get(url)
    # content = response.content.decode(encoding=response.charset)
    assert response.status_code == 200
