from panda3d.core import *
from quadtree import quadtreefy

def imgToDict(image):
    max_x=image.getReadXSize()
    max_y=image.getReadYSize()
    d={}
    for x in range(max_x):
        for y in range(max_y):
            if image.getRed(x,y)<0.5:
                v=True
            else:
                v=False  
            d[(x+1,max_y-y)]=v
    return d
    
def getHeightmapZ(heightmap, x, y, scale=100.0):    
    max_x=heightmap.getReadXSize()
    max_y=heightmap.getReadYSize()    
    img_x, img_y = int(x), int(y)
    if img_x==max_x:
        img_x=max_x-1
    elif img_x==0:
        img_x=1    
    if img_y==max_y:
        img_y=max_y-1
    elif img_y==0:
        img_y=1    
    return heightmap.getBright(img_x,512-img_y)*scale

def deformTile(tile, heightmap, x, y, extra_vertex=[]):
    z=tile.getZ(render)
    valid_vertex=[
                Point3(0, 32, 0),
                Point3(0, 0, 0),
                Point3(32, 0, 0),
                Point3(32, 32, 0)
                ]
    valid_vertex=valid_vertex+extra_vertex
    
    geomNodeCollection = tile.findAllMatches('**/+GeomNode')
    for nodePath in geomNodeCollection:
        geomNode = nodePath.node()
        geom = geomNode.modifyGeom(0)
        vdata = geom.modifyVertexData()
        vertexReWriter = GeomVertexRewriter(vdata, 'vertex')  
        while not vertexReWriter.isAtEnd():
            v = vertexReWriter.getData3f()
            if v in valid_vertex:
                #.getData3f() moves to row forward, to change the current vertex
                # we need to move the row back 
                vertexReWriter.setRow(vertexReWriter.getReadRow() - 1)
                #get the new z
                new_vert_z=getHeightmapZ(heightmap, (x-1)*32+v[0], (y-1)*32+v[1])-z
                #write it!
                vertexReWriter.setData3f(v[0],v[1], new_vert_z)


def generateNavmesh(tiles, navmap, heightmap, out_file, default_tile):
    print "Baking navmesh:",
    navmesh=NodePath("navmesh_root")
    nav_dict=imgToDict(navmap)
    for x in range(1, 17):
        for y in range(1, 17):            
            if nav_dict[(x,y)]:            
                print ".",
                if (x,y) in tiles:  
                    terrain_geom=tiles[(x,y)].find('**/navmesh_terrain') 
                    if terrain_geom:        
                        t=terrain_geom.copyTo(navmesh)
                        t.show()
                        t.setPos(tiles[(x,y)].getPos(render))
                        deformTile(t, heightmap, x, y)
                    else:    
                        terrain_geom=default_tile.copyTo(navmesh)
                        terrain_geom.setPos((x-1)*32, (y-1)*32, 0.0)
                        deformTile(terrain_geom, heightmap, x, y)
                        
                    tile_geom=tiles[(x,y)].find('**/navmesh_tile')
                    if tile_geom:
                        t=tile_geom.copyTo(navmesh)
                        t.show()
                        t.setPos(tiles[(x,y)].getPos(render))
                else:
                    terrain_geom=default_tile.copyTo(navmesh)
                    terrain_geom.setPos((x-1)*32, (y-1)*32, 0.0)
                    deformTile(terrain_geom, heightmap, x, y, [Point3(16, 16, 0)])
    print '\nFlattening nodes...',
    navmesh.setColorOff()
    navmesh.setColorScaleOff()
    navmesh.setMaterialOff()
    navmesh.setTextureOff()
    navmesh.clearModelNodes()                
    navmesh.flattenStrong()
    print 'writing to disk...',
    navmesh.writeBamFile(out_file)
    print 'done!'
    
def generateCollisionMesh(out_file):
    pass



#testing stuff
if __name__ == "__main__":
    from panda3d.core import loadPrcFileData
    loadPrcFileData("", "window-type none") 
    from direct.showbase import ShowBase
    base = ShowBase.ShowBase()
    tiles=[]
    navmap=PNMImage()
    navmap.read('save/d2/navmesh.png')
    heightmap=PNMImage()
    heightmap.read('save/d2/heightmap.png')
    out_file="test_navmesh.bam"
    default_tile=loader.loadModel('data/navmesh_tile.egg')
    generateNavmesh(tiles, navmap, heightmap, out_file, default_tile)  
