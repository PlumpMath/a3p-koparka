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
    #print 'height map', x, y   
    max_x=heightmap.getReadXSize()
    max_y=heightmap.getReadYSize()    
    img_x, img_y = int(x), int(y)
    if img_x>=max_x: img_x=max_x-1
    elif img_x<=0:   img_x=1    
    if img_y>=max_y: img_y=max_y-1
    elif img_y<=0:   img_y=1   
    return heightmap.getBright(img_x,512-img_y)*scale
       

def getDeformableVertexList(tile):
    valid_vertex=[]
    geomNodeCollection = tile.findAllMatches('**/+GeomNode')
    for nodePath in geomNodeCollection:
        geomNode = nodePath.node()
        geom = geomNode.modifyGeom(0)
        vdata = geom.modifyVertexData()
        vertexReWriter = GeomVertexRewriter(vdata, 'vertex')  
        while not vertexReWriter.isAtEnd():
            v = vertexReWriter.getData3f()
            valid_vertex.append(v)
    return valid_vertex
            
def deformTile(tile, heightmap,valid_vertex):        
    pos=tile.getPos(render)
    geomNodeCollection = tile.findAllMatches('**/+GeomNode')
    for nodePath in geomNodeCollection:
        geomNode = nodePath.node()
        geomNode.decompose()
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
                new_vert_z=getHeightmapZ(heightmap, pos.x+v.x, pos.y+v.y)-pos.z              
                #write it!
                vertexReWriter.setData3f(v[0],v[1], new_vert_z)


def generateNavmesh(tiles, navmap, heightmap, out_file, default_tile):
    print "Baking navmesh:"
    navmesh=NodePath("navmesh_root")
    nav_dict=imgToDict(navmap)
    valid_vertex=getDeformableVertexList(default_tile)
    
    for x in range(29):
        for y in range(25):            
            hex_y=y-x/2 
            hex_x=x
            #print hex_x, hex_y
            if (x,y) in tiles: 
                print 'custom tile'
                '''terrain_geom=tiles[(x,y)].find('**/navmesh_terrain') 
                if terrain_geom:        
                    t=terrain_geom.copyTo(navmesh)
                    t.show()
                    t.setPos(tiles[(x,y)].getPos(render))
                    deformTile(t, heightmap, x, y, valid_vertex)
                else:    
                    terrain_geom=default_tile.copyTo(navmesh)
                    terrain_geom.setPos((x-1)*32, (y-1)*32, 0.0)
                    deformTile(terrain_geom, heightmap, x, y, valid_vertex)
                    
                tile_geom=tiles[(x,y)].find('**/navmesh_tile')
                if tile_geom:
                    t=tile_geom.copyTo(navmesh)
                    t.show()
                    t.setPos(tiles[(x,y)].getPos(render))'''                    
            else:
                terrain_geom=default_tile.copyTo(navmesh)
                terrain_geom.setPos(hex2Point((hex_x,hex_y)))
                deformTile(terrain_geom, heightmap, valid_vertex)

    print '\nFlattening nodes...',
    navmesh.setColorOff()
    navmesh.setColorScaleOff()
    navmesh.setMaterialOff()
    navmesh.setTextureOff()
    navmesh.clearModelNodes() 
    #a3p likes the map on center so we move it
    navmesh.setPos(-256, -256, 0)
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
    loadPrcFileData("", "egg-mesh f") 
    from direct.showbase import ShowBase
    base = ShowBase.ShowBase()
    tiles=[]
    navmap=PNMImage()
    navmap.read('save/d2/navmesh.png')
    heightmap=PNMImage()
    heightmap.read('save/d2/heightmap.png')
    out_file="hex_test_navmesh.bam"
    default_tile=loader.loadModel('data/hex_tile.egg')
    generateNavmesh(tiles, navmap, heightmap, out_file, default_tile)  
