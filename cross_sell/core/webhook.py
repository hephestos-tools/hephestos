from cross_sell.core.executor import execute_workflow
from cross_sell.core.workflow import load_workflow


def process(webhook_data):
    """
        1. find corresponding automation for that webhook and shop
        2. load automation
        3. send graph object to executor
        4. wait for response
        """
    webhook_id = webhook_data.id
    shop_id = webhook_data.shop_id
    if webhook_id is None or shop_id is None:
        return
    else:
        workflow = load_workflow(webhook_data)

    if workflow is None:
        return
    else:
        response = execute_workflow(workflow)
    return response


def get_webhook_repo(param):
    pass


def list_all_webhooks():
    repo = get_webhook_repo(next("get_db()"))
    return repo.list_webhooks()


