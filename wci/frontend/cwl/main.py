import json
from pathlib import Path
from typing import Dict, List, Tuple, Final

from graph_tool.all import *


class NodeType:
    TASK: Final = 'task'
    IO: Final = 'io'
    MAIN: Final = 'main'


def _find_vertex_by_id(g: Graph, vertex_id: str) -> Vertex:
    for v in g.vertices():
        if g.vp.id[v] == vertex_id:
            return v


def _get_id_mapping(steps: List[Dict]) -> List[Tuple]:
    m = []
    for s in steps:
        m.append((s['id'], s['run']))
    return m


def _process_main(g: Graph, main: Dict) -> Graph:
    run_steps = main.get('steps', [])
    id_mapping = _get_id_mapping(run_steps)
    for s in run_steps:
        inputs = s.get('in', [])
        # outputs = s.get('out', [])
        for i in inputs:
            for m in id_mapping:
                i['source'] = i['source'].replace(f'{m[0]}/', f'{m[1]}/')
                i['id'] = i['id'].replace(f'{m[0]}/', f'{m[1]}/')
            v1 = _find_vertex_by_id(g, i['source'])
            v2 = _find_vertex_by_id(g, i['id'])
            g.add_edge(v1, v2)
    return g


def _create_new_graph() -> Graph:
    g = Graph()
    g.vp.id = g.new_vertex_property('string')
    g.vp.type = g.new_vertex_property('string')
    g.vp.data = g.new_vertex_property('python::object')
    g.vp.metadata = g.new_vertex_property('python::object')
    return g


def _get_io(step: Dict) -> (List[Dict], List[Dict]):
    return step.get('inputs', []), step.get('outputs', [])


def _get_id(step: Dict) -> str:
    return step['id']


def _process_workflow_step(g: Graph, step: Dict) -> Graph:
    main_vertex = g.add_vertex()
    g.vp.id[main_vertex] = step['id'].replace('.cwl', '')
    g.vp.type[main_vertex] = NodeType.MAIN

    inputs, _ = _get_io(step)

    for step_input in inputs:
        input_vertex = g.add_vertex()
        g.vp.id[input_vertex] = _get_id(step_input)
        g.vp.type[input_vertex] = NodeType.IO
        g.add_edge(main_vertex, input_vertex)
    g = _process_main(g, step)
    return g


def _process_cmd_step(g: Graph, step: Dict) -> Graph:
    task_vertex = g.add_vertex()
    g.vp.id[task_vertex] = step['id'].replace('.cwl', '')
    g.vp.type[task_vertex] = NodeType.TASK

    inputs, outputs = _get_io(step)

    for step_input in inputs:
        input_vertex = g.add_vertex()
        g.vp.id[input_vertex] = _get_id(step_input)
        g.vp.type[input_vertex] = NodeType.IO
        g.add_edge(input_vertex, task_vertex)

    for step_output in outputs:
        output_vertex = g.add_vertex()
        g.vp.id[output_vertex] = _get_id(step_output)
        g.vp.type[output_vertex] = NodeType.IO
        g.add_edge(task_vertex, output_vertex)

    return g


def _combine_io(g: Graph) -> Graph:
    to_remove = []
    to_add = []
    for g_e in g.edges():
        out_vertex = g_e.source()
        in_vertex = g_e.target()
        if g.vp.type[out_vertex] == g.vp.type[in_vertex] == NodeType.IO:
            to_remove.append(in_vertex)
            for in_e in in_vertex.out_edges():
                to_add.append((out_vertex, in_e.target()))
    for edge in to_add:
        g.add_edge(edge[0], edge[1])

    for v in reversed(sorted(to_remove)):
        g.remove_vertex(v)
    return g


def parse(path_to_file: Path) -> Graph:
    with open(path_to_file) as f:
        workflow = json.load(f)

    steps = workflow.get('$graph', [])

    workflow_graph = _create_new_graph()

    for step in steps:
        step_class = step.get('class')
        if step_class == 'Workflow':
            workflow_graph = _process_workflow_step(workflow_graph, step)
        elif step_class == 'CommandLineTool':
            workflow_graph = _process_cmd_step(workflow_graph, step)
        else:
            raise Exception(f'{step_class} is not supported by this frontend')

    workflow_graph = _combine_io(workflow_graph)

    # graph_draw(workflow_graph, vertex_text=workflow_graph.vp.type, output="workflow.pdf", output_size=(800, 800))
    return workflow_graph
