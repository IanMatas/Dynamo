# Appended to wave_geometry.py and embedded in the .dyn file; no external paths.
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from Autodesk.Revit.DB import (
    BuiltInCategory, Color, DirectShape, ElementId, FilteredElementCollector,
    GeometryObject, Material, SubTransaction, TessellatedFace,
    TessellatedShapeBuilder, TessellatedShapeBuilderFallback,
    TessellatedShapeBuilderTarget, TransactionStatus, UnitTypeId, UnitUtils, XYZ)
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import List


def create_revit_model(inputs):
    doc = DocumentManager.Instance.CurrentDBDocument
    if doc is None or doc.IsFamilyDocument:
        raise ValueError('Open a Revit project (.rvt), not the family editor, then run again.')
    length, width, height, opening_length, opening_width = [float(v) for v in inputs[:5]]
    segments = float(inputs[5])
    instance = str(inputs[6]).strip()
    if not instance or len(instance) > 80:
        raise ValueError('Model key must contain 1 to 80 characters.')
    meshes = build_model(length, width, height, opening_length, opening_width, segments)
    app_id = 'IanMatas.Dynamo.WaveHall.v1'
    prefix = instance + '::'
    existing = {}
    for element in FilteredElementCollector(doc).OfClass(DirectShape):
        if element.ApplicationId == app_id and element.ApplicationDataId.startswith(prefix):
            key = element.ApplicationDataId[len(prefix):]
            if key in existing:
                raise ValueError('Duplicate model key found in Revit. Use a new Model key.')
            existing[key] = element
    palette = {
        'Porcelain': ((235, 235, 229), 0),
        'Glass': ((130, 165, 177), 65),
        'Aluminium': ((100, 110, 114), 0),
        'Joint': ((130, 132, 129), 0),
        'Concrete': ((191, 189, 181), 0),
    }
    ft = UnitUtils.ConvertToInternalUnits(1.0, UnitTypeId.Meters)
    TransactionManager.Instance.EnsureInTransaction(doc)
    sub = SubTransaction(doc)
    sub.Start()
    result = []
    try:
        available = {m.Name: m for m in FilteredElementCollector(doc).OfClass(Material)}
        material_ids = {}
        for key, (rgb, transparency) in palette.items():
            name = 'WaveHall - ' + key
            if name in available:
                mat = available[name]
            else:
                mat = doc.GetElement(Material.Create(doc, name))
                mat.Color = Color(*rgb)
                mat.Transparency = transparency
                mat.Shininess = 65 if key == 'Glass' else 15
            material_ids[key] = mat.Id
        for mesh in meshes:
            if not mesh['faces']:
                continue
            builder = TessellatedShapeBuilder()
            builder.OpenConnectedFaceSet(False)
            xyz = [XYZ(p[0]*ft, p[1]*ft, p[2]*ft) for p in mesh['vertices']]
            for indices in mesh['faces']:
                vertices = List[XYZ]()
                for index in indices:
                    vertices.Add(xyz[index])
                face = TessellatedFace(vertices, material_ids[mesh['material']])
                if not builder.DoesFaceHaveEnoughLoopsAndVertices(face):
                    raise ValueError('Invalid face in ' + mesh['name'])
                builder.AddFace(face)
            builder.CloseConnectedFaceSet()
            builder.Target = TessellatedShapeBuilderTarget.Mesh
            builder.Fallback = TessellatedShapeBuilderFallback.Salvage
            builder.Build()
            built = builder.GetBuildResult()
            # Revit's TessellatedShapeBuilderResult API does not expose
            # AreThereInvalidData; Build() throws on fatal tessellation errors.
            objects = built.GetGeometricalObjects()
            if objects.Count == 0:
                raise ValueError('Revit produced no geometry for ' + mesh['name'])
            element = existing.pop(mesh['name'], None)
            if element is None:
                element = DirectShape.CreateElement(doc, ElementId(BuiltInCategory.OST_GenericModel))
                element.ApplicationId = app_id
                element.ApplicationDataId = prefix + mesh['name']
            element.SetShape(List[GeometryObject](objects))
            element.Name = instance + ' - ' + mesh['name']
            result.append(element)
        # Only previously generated components with this exact application/model key.
        for stale in existing.values():
            doc.Delete(stale.Id)
        doc.Regenerate()
        if sub.Commit() != TransactionStatus.Committed:
            raise RuntimeError('Revit did not commit the model transaction.')
    except:
        if sub.GetStatus() == TransactionStatus.Started:
            sub.RollBack()
        raise
    finally:
        sub.Dispose()
        TransactionManager.Instance.TransactionTaskDone()
    return {
        'Status': 'Created or updated concept geometry',
        'Model key': instance,
        'Overall metres (L, W, H)': [length, width, height],
        'Elements': result,
        'Triangles': sum(len(m['faces']) for m in meshes),
        'Note': 'Generic Model meshes; not native roof/wall/curtain-system or structural design.'
    }

OUT = create_revit_model(IN)
