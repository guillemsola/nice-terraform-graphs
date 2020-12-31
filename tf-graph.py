import pygraphviz as pgv
import networkx as nx
import re

# TODO change scope to function
toRemove = []


def RemoveNodes(graph):
    rootNode = '[root] root'
    RemoveMetadata(graph, rootNode)
    # i = 0

    while toRemove:
        remove = toRemove.pop()
        try:
            print(f'Contract {remove[0]} with {remove[1]}')

            # Colorize steps for debug
            # graph.nodes[remove[1]]['style'] = 'filled'
            # graph.nodes[remove[1]]['fillcolor'] = '1'
            # graph.nodes[remove[0]]['style'] = 'filled'
            # graph.nodes[remove[0]]['fillcolor'] = '2'
            # graph.nodes[remove[0]]['colorscheme'] = 'dark28'

            # out = nx.nx_agraph.to_agraph(graph)
            # edge = out.get_edge(remove[0], remove[1])
            # edge.attr['color'] = 'red'
            # edge.attr['style'] = 'bold'
            # out.layout(prog="dot")
            # out.draw(f'steps/step_{i:03}.png')
            # i += 1
            # graph.nodes[remove[0]]['style'] = ''
            # End Colorize steps

            graph = nx.contracted_nodes(graph, remove[0], remove[1], self_loops=False)
        except KeyError:
            print(f'Cannot contract {remove[0]} with {remove[1]}')

    graph.remove_node(rootNode)

    return graph


def RemoveMetadata(graph, node):
    successors = graph.successors(node)
    # ignore provider|output|data|meta|provisioner|var even if are from a module
    selector = re.compile('\[root\] (module\..*\.)?(provider|output|meta|provisioner|var|data)')

    for successor in successors:
        if selector.match(successor):
            print(successor)
            toRemove.append((node, successor))
        RemoveMetadata(graph, successor)


def AddIcons(graph):
    selector = re.compile('\[root\] (module\..*\.)?(.*)\.')

    for node in graph.nodes():
        match = selector.match(node)
        if match is not None and match.group(2):
            image = match.group(2).split('_', 1)
            if re.match('.*aws$', image[0]):
                graph.nodes[node]['image'] = f'images/aws/{image[1]}.png'


def RemoveSelfPointingNodes(graph):
    toDelete = []

    for edge in graph.edges:
        if edge[0] == edge[1]:
            toDelete.append(edge[0])
    for delete in toDelete:
        graph.remove_edge(delete, delete)


def RemoveDuplicatePointingNodes(graph):
    toDelete = []
    toCompareEdges = []

    for edge in graph.edges:
        toCompareEdges.append(edge)

    for edge in graph.edges:
        for dupe in toCompareEdges:
            if edge[0] == dupe[1] and edge[1] == dupe[0]:
                toDelete.append(edge)
                toCompareEdges.remove(edge)
                break

    for delete in toDelete:
        graph.remove_edge(delete[0], delete[1])

    agraph = nx.nx_agraph.to_agraph(graph)
    for edge in graph.edges:
        aedge = agraph.get_edge(edge[0], edge[1])
        aedge.attr['arrowhead'] = 'none'

    return nx.DiGraph(agraph)


def colorizeGraph(graph):
    selector = re.compile(
        '\[root\] (module\..*\.)?(provider|output|data|meta|provisioner|var)')

    colors = {'provider': '1', 'output': '3', 'data': '6',
              'meta': '4', 'provisioner': '5', 'var': '2'}

    for node in graph.nodes:
        nodeType = selector.match(node)
        if nodeType:
            graph.nodes[node]['colorscheme'] = 'dark28'
            graph.nodes[node]['style'] = 'filled'
            graph.nodes[node]['fillcolor'] = colors.get(nodeType.group(2), '8')
            graph.nodes[node]['color'] = colors.get(nodeType.group(2), '8')


def CreatePng(graph, fileName):
    out = nx.nx_agraph.to_agraph(graph)
    out.layout(prog="dot")
    out.draw(fileName)


dot = pgv.AGraph('samples/ec2_api.dot')
graph = nx.DiGraph(dot)

# graph = nx.drawing.nx_agraph.read_dot('samples/ecs_fargate.dot')
# graph = nx.Graph(nx.drawing.nx_pydot.read_dot('samples/ecs_fargate.dot'))

# view = nx.subgraph_view(graph, filter_edge = nx.classes.filters.hide_diedges)
# for e in view.edges():
#     print(e)

colorizeGraph(graph)

AddIcons(graph)

CreatePng(graph, 'input.png')

graph = RemoveNodes(graph)
# This is not needed with contracted nodes with self_loop false
# RemoveSelfPointingNodes(graph)

# TODO Find root node programatically

graph = RemoveDuplicatePointingNodes(graph)

nx.drawing.nx_agraph.write_dot(graph, "output.dot")

CreatePng(graph, 'output.png')
