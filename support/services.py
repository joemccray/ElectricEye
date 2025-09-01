from django.conf import settings
from freshdesk.api import API


def _client() -> API:
    return API(
        settings.FRESHDESK_DOMAIN,
        settings.FRESHDESK_API_KEY,
        version=2,
    )


def create_ticket(subject: str, email: str, description: str, tags: list = None):
    a = _client()
    return a.tickets.create_ticket(
        subject,
        email=email,
        description=description,
        tags=tags or [],
    )
