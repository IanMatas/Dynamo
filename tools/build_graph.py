"""Generate the portable Dynamo graph; standard library only."""
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

ROOT = Path(__file__).resolve().parents[1]
def uid(name):
    return uuid5(NAMESPACE_URL, 'IanMatas/Dynamo/WaveHall/' + name).hex

def port(name, desc=''):
    return {'Id': uid(name), 'Name': desc, 'Description': desc,
            'UsingDefaultValue': False, 'Level': 2,
            'UseLevels': False, 'KeepListStructure': False}

parameters = [
    ('Length (m)', '130.0;'), ('Width (m)', '75.0;'), ('Height (m)', '40.0;'),
    ('Opening length (m)', '48.0;'), ('Opening width (m)', '40.0;'),
    ('Segments (64 to 256, multiple of 4)', '128;'),
    ('Model key (reuse to update)', '"WaveHall_01";')]
nodes, views, connectors = [], [], []
for i, (name, code) in enumerate(parameters):
    key = 'input' + str(i)
    nodes.append({'ConcreteType': 'Dynamo.Graph.Nodes.CodeBlockNodeModel, DynamoCore',
                  'NodeType': 'CodeBlockNode', 'Code': code, 'Id': uid(key),
                  'Inputs': [], 'Outputs': [port(key+'out', '')],
                  'Replication': 'Disabled', 'Description': name})
    views.append({'ShowGeometry': False, 'Name': name, 'Id': uid(key),
                  'IsSetAsInput': False, 'IsSetAsOutput': False, 'Excluded': False,
                  'X': 40, 'Y': 60+i*115})
    connectors.append({'Start': uid(key+'out'), 'End': uid('pythonin'+str(i)),
                       'Id': uid('connector'+str(i)), 'IsHidden': 'False'})
code = (ROOT/'wave_geometry.py').read_text() + '\n\n' + (ROOT/'revit_node.py').read_text()
nodes.append({'ConcreteType': 'PythonNodeModels.PythonNode, PythonNodeModels',
              'NodeType': 'PythonScriptNode', 'Code': code, 'Engine': 'CPython3',
              'VariableInputPorts': True, 'Id': uid('python'),
              'Inputs': [port('pythonin'+str(i),'IN['+str(i)+']') for i in range(7)],
              'Outputs': [port('pythonout','OUT')], 'Replication': 'Disabled',
              'Description': 'Build or update the wave hall in the active Revit project.'})
views.append({'ShowGeometry': False, 'Name': 'Create / update Wave Hall in Revit',
              'Id': uid('python'), 'IsSetAsInput': False, 'IsSetAsOutput': True,
              'Excluded': False, 'X': 540, 'Y': 230})
graph = {
    'Uuid': uid('graph'), 'IsCustomNode': False,
    'Description': 'Reference-inspired wave hall, 130 x 75 x 40 metres. Open a Revit 2026 project; run manually. Creates Generic Model DirectShapes. No external packages.',
    'Name': 'Wave Hall - Revit 2026', 'ElementResolver': {'ResolutionMap': {}},
    'Inputs': [], 'Outputs': [], 'Nodes': nodes, 'Connectors': connectors,
    'Dependencies': [], 'NodeLibraryDependencies': [], 'Bindings': [],
    'View': {'Dynamo': {'ScaleFactor': 1.0, 'HasRunWithoutCrash': False,
                        'IsVisibleInDynamoLibrary': True, 'Version': '3.4.0.0',
                        'RunType': 'Manual', 'RunPeriod': '1000'},
             'NodeViews': views, 'Annotations': [], 'X': 30, 'Y': 30, 'Zoom': 0.85}}
path = ROOT/'Wave_Hall_Revit2026.dyn'
path.write_text(json.dumps(graph, indent=2)+'\n')
print(path)
