class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, node_type=None, automation_id=None):
        if node_id is None:
            raise ValueError("Node ID cannot be None")
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                'node_type': node_type,
                'automation_id': automation_id,
            }
            self.edges[node_id] = []

    def add_nodes(self, nodes):
        for node_id, node_type, automation_id in nodes:
            self.add_node(node_id, node_type, automation_id)

    def add_edge(self, from_node_id, to_node_id):
        if from_node_id is None or to_node_id is None:
            raise ValueError("Node IDs cannot be None")
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise ValueError("Both nodes must exist in the graph")
        self.edges[from_node_id].append(to_node_id)
        if self.is_cyclic():
            self.edges[from_node_id].remove(to_node_id)
            raise ValueError("Adding this edge would create a cycle")

    def add_edges(self, edges):
        for from_node_id, to_node_id in edges:
            self.add_edge(from_node_id, to_node_id)

    def is_cyclic_util(self, node_id, visited, rec_stack):
        stack = [(node_id, iter(self.edges.get(node_id, [])))]
        while stack:
            current, children = stack[-1]
            visited.add(current)
            rec_stack.add(current)

            for child in children:
                if child not in visited:
                    stack.append((child, iter(self.edges.get(child, []))))
                    break
                elif child in rec_stack:
                    return True
            else:
                rec_stack.remove(current)
                stack.pop()
        return False

    def is_cyclic(self):
        visited = set()
        rec_stack = set()

        for node_id in self.nodes:
            if node_id not in visited:
                if self.is_cyclic_util(node_id, visited, rec_stack):
                    return True

        return False

    def topological_sort_util(self, node_id, visited, stack):
        temp_stack = [node_id]
        while temp_stack:
            current = temp_stack[-1]
            if current not in visited:
                visited.add(current)
                temp_stack.extend(n for n in self.edges.get(current, []) if n not in visited)
            else:
                if current not in stack:
                    stack.append(current)
                temp_stack.pop()

    def topological_sort(self):
        if self.is_cyclic():
            raise ValueError("Graph contains a cycle, topological sort not possible")

        visited = set()
        stack = []

        for node_id in self.nodes:
            if node_id not in visited:
                self.topological_sort_util(node_id, visited, stack)

        return stack[::-1]  # Return reversed stack
