"""Dependency-free conceptual wave hall geometry. Coordinates are metres."""
import math


def build_model(length=130.0, width=75.0, height=40.0,
                opening_length=48.0, opening_width=40.0, segments=128):
    vals = (length, width, height, opening_length, opening_width)
    if not all(math.isfinite(v) and v > 0 for v in vals):
        raise ValueError('Dimensions must be finite positive metres.')
    if length < 20 or width < 15 or height < 5:
        raise ValueError('Use length >= 20 m, width >= 15 m, height >= 5 m.')
    if not (0.15 * length <= opening_length <= 0.55 * length):
        raise ValueError('Opening length must be 15 to 55 percent of total length.')
    if not (0.15 * width <= opening_width <= 0.65 * width):
        raise ValueError('Opening width must be 15 to 65 percent of total width.')
    if int(segments) != segments or not 64 <= segments <= 256 or segments % 4:
        raise ValueError('Segments must be a multiple of 4 from 64 to 256.')
    n = int(segments)
    meshes = []

    def mesh(name, material):
        m = {'name': name, 'material': material, 'vertices': [], 'faces': []}
        meshes.append(m)
        return m

    def tri(m, a, b, c):
        m['faces'].append((a, b, c))

    def quad(m, a, b, c, d):
        tri(m, a, b, c)
        tri(m, a, c, d)

    def point(m, p):
        m['vertices'].append(tuple(p))
        return len(m['vertices']) - 1

    def outer(t):
        # Broad rounded central hall, tapering into two extended wings.
        c, s = math.cos(t), math.sin(t)
        x = 0.5 * length * c
        y = 0.5 * width * math.copysign(abs(s) ** 0.5, s)
        y *= 0.48 + 0.52 * math.exp(-(x / (0.30 * length)) ** 4)
        y += 0.045 * width * math.sin(2 * math.pi * x / length)
        return (x, y)

    raw_outer = [outer(2 * math.pi * i / n) for i in range(n)]
    ymin, ymax = min(p[1] for p in raw_outer), max(p[1] for p in raw_outer)
    def outline(t):
        x, y = outer(t)
        return (x, (y - (ymin + ymax) / 2) * width / (ymax - ymin))

    def roof_z(x, y):
        # High rear crest, lower front lip, and a lifted right wing.
        u, v = x / length, y / width
        crest = math.exp(-((u + 0.075) / 0.245) ** 2)
        right = math.exp(-((u - 0.43) / 0.20) ** 2)
        return height * (0.18 + 0.76 * crest * (0.58 + 0.84 * v)
                         + 0.36 * right + 0.09 * (u + 0.5))

    thickness = min(0.65, height * 0.02)
    def ring_point(i, f):
        t = 2 * math.pi * i / n
        ax, ay = 0.5 * opening_length * math.cos(t), 0.5 * opening_width * math.sin(t)
        bx, by = outline(t)
        x, y = ax + f * (bx - ax), ay + f * (by - ay)
        return (x, y, roof_z(x, y))

    roof = mesh('Roof shell', 'Porcelain')
    radial = 10
    for underside in (False, True):
        for j in range(radial + 1):
            for i in range(n):
                x, y, z = ring_point(i, j / float(radial))
                point(roof, (x, y, z - (thickness if underside else 0)))
    offset = n * (radial + 1)
    for j in range(radial):
        for i in range(n):
            k = (i + 1) % n
            a, b, c, d = j*n+i, (j+1)*n+i, (j+1)*n+k, j*n+k
            quad(roof, a, b, c, d)
            quad(roof, d+offset, c+offset, b+offset, a+offset)
    for i in range(n):
        k = (i + 1) % n
        quad(roof, i, k, k+offset, i+offset)
        a, b = radial*n+i, radial*n+k
        quad(roof, b, a, a+offset, b+offset)

    # Box section following an arbitrary line, shared by fins and skylight grid.
    def beam(m, a, b, size):
        d = tuple(b[i]-a[i] for i in range(3))
        norm = math.sqrt(sum(v*v for v in d))
        if norm < 1e-7:
            return
        d = tuple(v/norm for v in d)
        ref = (0., 0., 1.) if abs(d[2]) < 0.95 else (0., 1., 0.)
        def cross(p, q):
            return (p[1]*q[2]-p[2]*q[1], p[2]*q[0]-p[0]*q[2], p[0]*q[1]-p[1]*q[0])
        u = cross(d, ref)
        mag = math.sqrt(sum(v*v for v in u))
        u = tuple(v/mag*size/2 for v in u)
        v = cross(d, u)
        ids = []
        for p in (a, b):
            for su, sv in ((-1,-1),(1,-1),(1,1),(-1,1)):
                ids.append(point(m, tuple(p[i]+su*u[i]+sv*v[i] for i in range(3))))
        quad(m, ids[3],ids[2],ids[1],ids[0])
        quad(m, ids[4],ids[5],ids[6],ids[7])
        for j in range(4):
            k=(j+1)%4
            quad(m,ids[j],ids[k],ids[k+4],ids[j+4])

    # Individual panel boxes allow readable facade joints in shaded views.
    facade = mesh('Facade panels', 'Porcelain')
    entrance = mesh('Entrance glazing', 'Glass')
    fins = mesh('Entrance fins', 'Porcelain')
    for i in range(n):
        t0, t1 = 2*math.pi*(i+0.035)/n, 2*math.pi*(i+0.965)/n
        a, b = outline(t0), outline(t1)
        is_entrance = a[0] < -length*0.25 and a[1] < 0
        m = entrance if is_entrance else facade
        # Insets keep panels and fins inside the specified bounding dimensions.
        a, b = tuple(v*0.994 for v in a), tuple(v*0.994 for v in b)
        ids=[]
        for factor in (1., 0.990):
            for p, z in ((a,0.),(b,0.),(b,roof_z(*b)-thickness),(a,roof_z(*a)-thickness)):
                ids.append(point(m,(p[0]*factor,p[1]*factor,z)))
        quad(m,*ids[:4]); quad(m,ids[7],ids[6],ids[5],ids[4])
        for j in range(4):
            k=(j+1)%4
            quad(m,ids[j],ids[j+4],ids[k+4],ids[k])
        if is_entrance and i % 2 == 0:
            x,y=a
            size = min(length,width)*0.008
            beam(fins,(x,y,size/2),(x,y,roof_z(x,y)-thickness-size/2),size)

    # Warped glazed surface sits below the roof's inner edge.
    glass = mesh('Central skylight', 'Glass')
    glass_drop = thickness*0.60
    point(glass,(0.,0.,roof_z(0.,0.)-glass_drop))
    rings=12
    for j in range(1,rings+1):
        for i in range(n):
            t=2*math.pi*i/n
            x=opening_length/2*j/rings*math.cos(t)
            y=opening_width/2*j/rings*math.sin(t)
            point(glass,(x,y,roof_z(x,y)-glass_drop))
    for i in range(n):
        tri(glass,0,1+i,1+(i+1)%n)
    for j in range(rings-1):
        for i in range(n):
            k=(i+1)%n
            quad(glass,1+j*n+i,1+(j+1)*n+i,1+(j+1)*n+k,1+j*n+k)

    grid=mesh('Skylight grid', 'Aluminium')
    spacing=2.5
    for axis, half, other in ((0,opening_length/2,opening_width/2),(1,opening_width/2,opening_length/2)):
        for k in range(-int(half/spacing),int(half/spacing)+1):
            fixed=k*spacing
            if abs(fixed)>=half*0.98:
                continue
            reach=other*math.sqrt(1-(fixed/half)**2)*0.998
            steps=max(4,int(2*reach/1.5))
            path=[]
            for j in range(steps+1):
                free=-reach+2*reach*j/steps
                x,y=(fixed,free) if axis==0 else (free,fixed)
                path.append((x,y,roof_z(x,y)-glass_drop+0.11))
            for a,b in zip(path,path[1:]):
                beam(grid,a,b,0.12)

    # Fine strips follow the shell exactly, forming panel joints.
    seams=mesh('Roof panel joints', 'Joint')
    for i in range(0,n,2):
        for j in range(radial):
            a=ring_point(i,j/float(radial)); b=ring_point(i,(j+1)/float(radial))
            dx,dy=b[0]-a[0],b[1]-a[1]
            norm=math.hypot(dx,dy)
            ux,uy=-dy/norm*0.018,dx/norm*0.018
            ids=[]
            for p,sgn in ((a,-1),(b,-1),(b,1),(a,1)):
                x,y=p[0]+sgn*ux,p[1]+sgn*uy
                point_z=roof_z(x,y)+0.006
                ids.append(point(seams,(x,y,point_z)))
            quad(seams,*ids)

    slab=mesh('Ground floor', 'Concrete')
    for z in (0.,0.25):
        point(slab,(0.,0.,z))
        for i in range(n):
            x,y=outline(2*math.pi*i/n)
            point(slab,(x*0.990,y*0.990,z))
    off=n+1
    for i in range(n):
        a,b=1+i,1+(i+1)%n
        tri(slab,0,b,a); tri(slab,off,off+a,off+b)
        quad(slab,a,b,b+off,a+off)

    # Enforce exact overall bounding dimensions, including joints and fins.
    vertices=[p for m in meshes for p in m['vertices']]
    lo=[min(p[a] for p in vertices) for a in range(3)]
    hi=[max(p[a] for p in vertices) for a in range(3)]
    scales=[length/(hi[0]-lo[0]),width/(hi[1]-lo[1]),height/(hi[2]-lo[2])]
    for m in meshes:
        m['vertices']=[((p[0]-(hi[0]+lo[0])/2)*scales[0],
                        (p[1]-(hi[1]+lo[1])/2)*scales[1],
                        (p[2]-lo[2])*scales[2]) for p in m['vertices']]
    return meshes
