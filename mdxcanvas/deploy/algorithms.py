def tarjan_scc(graph):
    """Return strongly connected components for a mapping of nodes to successors."""
    next_index = 0
    stack = []
    indices = {}
    lowlinks = {}
    active = set()
    components = []

    def visit(node):
        nonlocal next_index
        indices[node] = lowlinks[node] = next_index
        next_index += 1
        stack.append(node)
        active.add(node)
        for successor in graph.get(node, ()):
            if successor not in graph:
                continue
            if successor not in indices:
                visit(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in active:
                lowlinks[node] = min(lowlinks[node], indices[successor])
        if lowlinks[node] == indices[node]:
            component = []
            while True:
                item = stack.pop()
                active.remove(item)
                component.append(item)
                if item == node:
                    break
            components.append(component)

    for node in graph:
        if node not in indices:
            visit(node)
    return components
