def execute_workflow(workflow):
    """
    #TODO 1. create a dag object, topological sort -  write our own \n
    #TODO 2. iterate over graph and execute nodes\n
    #TODO 3. add logic for each node

    :param workflow:
    :return:

    db = next(get_db())
    node_repo = get_nodes_repository(db)
    nodes = node_repo.get_nodes(workflow.id)

    workflow_dag = nx.DiGraph()
    for edge in nodes:
        workflow_dag.add_edge(edge.from_node_id, edge.to_node_id)

    execute(workflow_dag, nodes)
"""


def execute(workflow_dag, nodes):
    edge_view = workflow_dag.edges
    for u, v in edge_view:
        _execute_node(nodes[u].id, nodes[u].node_type)


def _execute_node(node_id, next_node_id, node_type):
    """
    #TODO: Write a node factory
    """
    if (node_type == "trigger"):
        """ execute_trigger_node(node_id) """
