from cross_sell.models import WebhookEvents
from core.repository.base_repository import BaseRepository


class WebhookRepository(BaseRepository):

    @staticmethod
    def save(webhook: WebhookEvents) -> WebhookEvents:
        webhook.save()
        return webhook

    @staticmethod
    def get_all():
        e = ''
        return e
