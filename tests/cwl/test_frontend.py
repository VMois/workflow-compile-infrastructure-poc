from wci.frontend.cwl import parse


def test_parse(cwl_packed_workflow_path):
    parse(cwl_packed_workflow_path)
