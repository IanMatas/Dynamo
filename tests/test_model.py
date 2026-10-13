import ast
import json
import math
import unittest
from collections import Counter
from pathlib import Path
from wave_geometry import build_model

ROOT=Path(__file__).resolve().parents[1]

class ModelChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meshes=build_model()

    def test_extents_in_metres(self):
        for kwargs, expected in [({},(130,75,40)),
                                 ({'length':100,'width':60,'height':30,'opening_length':40,'opening_width':30,'segments':64},(100,60,30))]:
            vs=[p for m in build_model(**kwargs) for p in m['vertices']]
            for a, size in enumerate(expected):
                self.assertAlmostEqual(max(p[a] for p in vs)-min(p[a] for p in vs),size,places=8)
            self.assertAlmostEqual(min(p[2] for p in vs),0.,places=9)

    def test_faces_finite_nondegenerate(self):
        for m in self.meshes:
            self.assertTrue(m['vertices'],m['name'])
            self.assertTrue(m['faces'],m['name'])
            for p in m['vertices']:
                self.assertTrue(all(math.isfinite(x) for x in p))
            for face in m['faces']:
                self.assertEqual(len(set(face)),3)
                a,b,c=[m['vertices'][i] for i in face]
                u=[b[i]-a[i] for i in range(3)]
                v=[c[i]-a[i] for i in range(3)]
                cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                self.assertGreater(sum(t*t for t in cross),1e-12,m['name'])

    def test_closed_components_manifold_and_oriented(self):
        for m in self.meshes:
            if m['name'] in ('Central skylight','Roof panel joints'):
                continue # Intentionally open surface meshes.
            directed=Counter()
            undirected=Counter()
            for a,b,c in m['faces']:
                for e in ((a,b),(b,c),(c,a)):
                    directed[e]+=1
                    undirected[tuple(sorted(e))]+=1
            self.assertTrue(all(v==2 for v in undirected.values()),m['name'])
            for a,b in directed:
                self.assertEqual(directed[a,b],directed[b,a],m['name'])

    def test_reproducible(self):
        self.assertEqual(self.meshes,build_model())

    def test_invalid_inputs(self):
        for args in ({'height':float('nan')},{'width':0},{'segments':63},
                     {'segments':128.5},{'opening_length':129}, {'opening_width':74}):
            with self.assertRaises(ValueError):
                build_model(**args)

    def test_graph_wiring_and_embedded_code(self):
        g=json.loads((ROOT/'Wave_Hall_Revit2026.dyn').read_text())
        self.assertEqual(g['View']['Dynamo']['RunType'],'Manual')
        self.assertEqual(len(g['Nodes']),8)
        node=g['Nodes'][-1]
        self.assertEqual(node['Engine'],'CPython3')
        ast.parse(node['Code'])
        self.assertEqual(node['Code'],(ROOT/'wave_geometry.py').read_text()+'\n\n'+(ROOT/'revit_node.py').read_text())
        self.assertEqual(len(g['Connectors']),len(node['Inputs']))
        outputs={p['Id'] for n in g['Nodes'] for p in n['Outputs']}
        inputs={p['Id'] for n in g['Nodes'] for p in n['Inputs']}
        for c in g['Connectors']:
            self.assertIn(c['Start'],outputs)
            self.assertIn(c['End'],inputs)
        self.assertEqual({c['End'] for c in g['Connectors']},inputs)
        self.assertFalse(g['NodeLibraryDependencies'])

if __name__=='__main__':
    unittest.main()
