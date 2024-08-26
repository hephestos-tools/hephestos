# """
# class AutomationRepository:
#     def __init__(self, db: Session):
#         self.db = db
#
#     def get_automation_by_webhook_shop(self, webhook_id, shop_id: int):
#         return (self.db.query(Automation).filter(Automation.shop_id == shop_id and Automation.webhook_id == webhook_id)
#                 .first())
#
#
# def get_automation_repository(db: Session):
#     return AutomationRepository(db)
#
#
# class NodesRepository:
#     def __init__(self, db: Session):
#         self.db = db
#
#      sql = text(
#                 SELECT nodes.id, nodes.node_type, edges.from_node_id, edges.to_node_id
#                 FROM nodes
#                 JOIN edges ON nodes.id = edges.from_node_id
#                 WHERE auto_id=:autoId
#                 ORDER BY nodes.id
#             )
#
#
#     def get_nodes(self, automation_id: int):
#         # SQL query to join nodes and edges
#         query = (
#             self.db.query(Node, Node.id, Node.node_type, Edge.from_node_id, Edge.to_node_id)
#             .join(Edge, Node.id == Edge.from_node_id)
#             .filter(Node.auto_id == automation_id)
#         )
#
#         # Fetch all results
#         return query.all()
#
#
# def get_nodes_repository(db: Session):
#     return NodesRepository(db)
#
#
# class WebhookRepository:
#     def __init__(self, db: Session):
#         self.db = db
#
#     def list_webhooks(self):
#
#         return self.db.query(WebhookSubscribed).all()
#
#
# def get_webhook_repo(db: Session):
#     return WebhookRepository(db)
# """

from cross_sell.models import Webhooks


class WebhookRepository:

    @staticmethod
    def save_webhook(app, webhook_data, shop_id, event_type):
        webhook = Webhooks(
            app=app,
            webhook_data=webhook_data,
            shop_id=shop_id,
            event_type=event_type
        )
        webhook.save()
        return webhook

    @staticmethod
    def get_all_webhooks():
        e = Webhooks.objects.all()
        return e
