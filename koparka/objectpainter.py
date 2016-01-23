from panda3d.core import *
from direct.actor.Actor import Actor
#from direct.particles.ParticleEffect import ParticleEffect
from sqliteloader import loadModel
from direct.stdpy.file import listdir, exists, open
import json
from vfx_loader import createEffect

class ObjectPainter():
    def __init__(self, lightManager): 
        self.lightManager=lightManager
        #collision detection setup
        self.traverser = CollisionTraverser()   
        #self.traverser.showCollisions(render)
        self.queue     = CollisionHandlerQueue()         
        self.pickerNode = CollisionNode('mouseRay')    
        self.pickerNP = camera.attachNewNode(self.pickerNode) 
        #print "mask:", self.pickerNP.getCollideMask()    
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()               
        self.pickerNode.addSolid(self.pickerRay)      
        self.traverser.addCollider(self.pickerNP, self.queue)
                
        self.currentObject=None
        self.isLocked=True
        self.currentLight=None
        self.selectedObject=None
        self.hitNode=None
        self.currentHPR=[0,0,0]
        self.currentZ=0.0
        self.currentScale=1.0
        self.currentWall=None
        self.hit_pos=(0,0,0)
        self.actors=[]
        self.particles=[]
        
        self.tiles={}
        
        #quadtree structure
        nodeA=render.attachNewNode('quadA')
        nodeA.setPos(render,128,128,0)
        nodeB=render.attachNewNode('quadB')
        nodeB.setPos(render,384,128,0)
        nodeC=render.attachNewNode('quadC')
        nodeC.setPos(render,128,384,0)
        nodeD=render.attachNewNode('quadD')
        nodeD.setPos(render,384,384,0)        
        nodeA1=nodeA.attachNewNode('quadA1')
        nodeA1.setPos(render,64, 64, 0)
        nodeA2=nodeA.attachNewNode('quadA2')
        nodeA2.setPos(render,192, 64, 0)
        nodeA3=nodeA.attachNewNode('quadA3')
        nodeA3.setPos(render,64, 192, 0)
        nodeA4=nodeA.attachNewNode('quadA4')
        nodeA4.setPos(render,192, 192, 0)        
        nodeB1=nodeB.attachNewNode('quadB1')
        nodeB1.setPos(render,320, 64, 0)
        nodeB2=nodeB.attachNewNode('quadB2')
        nodeB2.setPos(render,448, 64, 0)
        nodeB3=nodeB.attachNewNode('quadB3')
        nodeB3.setPos(render,320, 192, 0)
        nodeB4=nodeB.attachNewNode('quadB4')
        nodeB4.setPos(render,448, 192, 0)        
        nodeC1=nodeC.attachNewNode('quadC1')
        nodeC1.setPos(render,64, 320, 0)
        nodeC2=nodeC.attachNewNode('quadC2')
        nodeC2.setPos(render,192, 320, 0)
        nodeC3=nodeC.attachNewNode('quadC3')
        nodeC3.setPos(render,64, 448, 0)
        nodeC4=nodeC.attachNewNode('quadC4')
        nodeC4.setPos(render,192, 448, 0)        
        nodeD1=nodeD.attachNewNode('quadD1')
        nodeD1.setPos(render,320, 320, 0)
        nodeD2=nodeD.attachNewNode('quadD2')
        nodeD2.setPos(render,448, 320, 0)
        nodeD3=nodeD.attachNewNode('quadD3')
        nodeD3.setPos(render,320, 448, 0)
        nodeD4=nodeD.attachNewNode('quadD4')
        nodeD4.setPos(render,448, 448, 0)
        self.quadtree=[nodeA1,nodeA2,nodeA3,nodeA4,
                       nodeB1,nodeB2,nodeB3,nodeB4,
                       nodeC1,nodeC2,nodeC3,nodeC4,
                       nodeD1,nodeD2,nodeD3,nodeD4]

    def normalizeHPR(self):
        newHpr=[]
        for i in range(3):
            temp=self.currentHPR[i]%360.0            
            newHpr.append(temp)    
        self.currentHPR=newHpr
    
    def setHpr(self, axis, slider=None, amount=None):
        if slider:
            amount=int(slider['value'])
        if axis=='H: ':
            i=0
        elif axis=='P: ':
            i=1
        elif axis=='R: ':
            i=2         
        self.currentHPR[i]=amount 
        self.normalizeHPR()
        #if self.currentObject!=None:
        #    self.currentObject.setHpr(self.currentHPR[0],self.currentHPR[1],self.currentHPR[2])        
        return axis+'%.1f'%self.currentHPR[i]    
        
    def adjustHpr(self, amount, axis):
        if axis=='H: ':
            i=0
        elif axis=='P: ':
            i=1
        elif axis=='R: ':
            i=2         
        new=self.currentHPR[i]+amount
        self.currentHPR[i]=new 
        self.normalizeHPR()
        #if self.currentObject!=None:
        #    self.currentObject.setHpr(self.currentHPR[0],self.currentHPR[1],self.currentHPR[2])        
        return axis+'%.1f'%self.currentHPR[i]
    
    def setScale(self, slider=None, amount=None):
        if slider:
            amount=slider['value']
        new=min(10.0, max(0.1, amount)) 
        self.currentScale=new
        if self.currentObject!=None:
            self.currentObject.setScale(self.currentScale)
        if self.currentLight is not None:                               
            self.lightManager.setRadius(self.currentLight, 10.0*self.currentScale)
                
    def adjustScale(self, amount):
        new=min(10.0, max(0.1, self.currentScale+amount)) 
        self.currentScale=new        
        if self.currentLight is not None:                               
            self.lightManager.setRadius(self.currentLight, 10.0*self.currentScale)        
        if self.isLocked == False:
            self.currentObject.setScale(self.currentScale)
                
    def setZ(self, slider=None, amount=None):
        if slider:
            amount=(slider['value']*20.0)-10.0
        new=min(10.0, max(-10.0, amount)) 
        self.currentZ=new
        if self.isLocked == False:
            if self.currentObject!=None:
                self.currentObject.setZ(self.currentZ)
                    
    def adjustZ(self, amount):
        new=min(100.0, max(-100.0, self.currentZ+amount)) 
        self.currentZ=new
        if self.isLocked == False:
            if self.currentObject!=None:
                self.currentObject.setZ(self.currentZ)
            
    def stop(self):
        if self.currentObject!=None:
            if self.currentObject in self.actors:
                self.actors.pop(self.actors.index(self.currentObject)).cleanup() 
            self.currentObject.removeNode()
            self.currentObject=None
        if self.currentWall:
            self.currentWall.removeNode()
            self.currentWall=None

    def loadActor(self, model):      
        actor=loadModel(model,animation=True)            
        self.actors.append(actor)
        self.currentObject=self.actors[-1]
        self.currentObject.reparentTo(render)
        self.currentObject.setPythonTag('props', '')
        self.currentObject.setHpr(self.currentHPR[0],self.currentHPR[1],self.currentHPR[2])
        self.currentObject.setZ(self.currentZ)
        self.currentObject.setScale(self.currentScale)  
        
    def loadModel(self, model):
        self.currentScale=1.0
        self.currentHPR=[0, 0, 0]
        self.currentZ=0.0
        self.isLocked=False
        if self.currentObject!=None:
            self.currentObject.removeNode()
        self.currentObject=loader.loadModel(model)
        self.currentObject.reparentTo(render)
        self.currentObject.setPythonTag('props', '')
        self.currentObject.setHpr(self.currentHPR[0],self.currentHPR[1],self.currentHPR[2])
        self.currentObject.setZ(self.currentZ)
        self.currentObject.setScale(self.currentScale) 
        for geom in self.currentObject.findAllMatches('**/+GeomNode'):
            if geom.hasTag('light'): 
                self.currentLight=self.lightManager.addLight(pos=self.currentObject.getPos(), color=(1.0, 1.0, 1.0), radius=10.0)
                self.currentObject.setPythonTag('hasLight', self.currentLight)
                self.currentHPR=[255.0, 255.0, 255.0]   
            if geom.hasTag('particle'):
                file='particle/'+geom.getTag('particle')
                if exists(file):
                    with open(file) as f:  
                        values=json.load(f)
                    p=createEffect(values)                
                    self.currentObject.setPythonTag('particle', p)    
                    p.start(parent=self.currentObject, renderParent=render)         
        if geom.hasTag('glsl_shader'): 
            glsl_shader=geom.getTag('glsl_shader')  
            self.currentObject.setShader(Shader.load(Shader.SLGLSL, "shaders/{0}_v.glsl".format(glsl_shader),"shaders/{0}_f.glsl".format(glsl_shader)))
        else:            
            self.currentObject.setShader(Shader.load(Shader.SLGLSL, "shaders/default_v.glsl","shaders/default_f.glsl"))
        
        if self.currentObject.find('**/navmesh_terrain'):            
            self.isLocked=True
            self.currentObject.find('**/navmesh_terrain').hide()
        if self.currentObject.find('**/navmesh_tile'):
            self.isLocked=True
            self.currentObject.find('**/navmesh_tile').hide()
        if self.currentObject.find('**/collision'):            
            self.currentObject.find('**/collision').hide()
        
        for tex_stage in self.currentObject.findAllTextureStages():            
            tex=self.currentObject.findTexture(tex_stage)
            if tex:
                file_name=tex.getFilename()
                tex_format=tex.getFormat()   
                #print tex_stage,  file_name, tex_format                
                newTex=loader.loadTexture(str(file_name)[:-3]+'dds')
                if tex_stage.getMode()==TextureStage.M_normal:
                    tex_stage.setMode(TextureStage.M_normal_gloss)
                if tex_stage.getMode()!=TextureStage.M_normal_gloss:
                    if tex_format==Texture.F_rgb:
                        tex_format=Texture.F_srgb
                    elif tex_format==Texture.F_rgba:
                        tex_format=Texture.F_srgb_alpha    
                newTex.setFormat(tex_format)
                self.currentObject.setTexture(tex_stage, newTex, 1)
        
        
        
            
    def loadWall(self, model, change_model=False):
        pos=self.hit_pos   
        if self.currentWall!=None:
            pos=self.currentWall.find('**/next').getPos(render)            
        if change_model:            
            pos=self.currentWall.getPos(render)
            self.currentWall.removeNode()
        self.currentWall=loadModel(model)
        self.currentWall.reparentTo(render)
        #self.currentWall.setCollideMask(BitMask32.allOff())        
        #self.currentWall.setShaderAuto()        
        #self.currentWall.find('**/collision').setCollideMask(BitMask32.bit(2))        
        #self.currentWall.find('**/collision').setPythonTag('object', self.currentWall)
        #self.currentWall.setPythonTag('model_file', model)
        self.currentWall.setPythonTag('props', '')
        self.currentWall.setPos(render,pos)
        self.currentWall.setScale(self.currentScale)
            
    def drop(self, props=''):
        if self.currentWall:
            best_node = min(self.quadtree, key=lambda n: n.getDistance(self.currentWall))
            self.currentWall.wrtReparentTo(best_node)
            self.currentWall.setPythonTag('props', props)
        elif self.currentObject:
            x=int((self.currentObject.getX(render)/32.0)+0.5)
            y=int((self.currentObject.getY(render)/32.0)+0.5)
            print x, y
            best_node = min(self.quadtree, key=lambda n: n.getDistance(self.currentObject))
            self.currentObject.setPythonTag('props', props)
            self.currentObject.wrtReparentTo(best_node) 
            self.tiles[(x,y)]=self.currentObject                    
            next=self.currentObject.find('**/next')  
            if next:
                self.hit_pos = next.getPos(render)
            self.currentObject=None
            self.currentLight=None
            
            
    def pickup(self): 
        if self.selectedObject:
            self.currentObject=self.selectedObject
            self.currentObject.wrtReparentTo(render) 
            #self.currentHPR=[self.currentObject.getH(), self.currentObject.getP(), self.currentObject.getR()]
            self.normalizeHPR()
            #self.currentZ=self.currentObject.getZ(render)
            self.currentScales=self.currentObject.getScale()[0]
            if self.currentObject.hasPythonTag('hasLight'):
                self.currentLight=self.currentObject.getPythonTag('hasLight')
            
            
    def select(self):        
        x=int((self.hit_pos.getX()/32.0)+0.5)
        y=int((self.hit_pos.getY()/32.0)+0.5) 
        print x, y     
        if (x,y) in self.tiles:
            self.selectedObject=self.tiles[(x,y)]
            del self.tiles[(x,y)]
            return True
        return False    
            
    def _stringToFloat(self, string):
        f=0.001
        if string:
            try:
                f=float(string)
            except ValueError:
                pass
        if f==0.0:
            f=0.001
        return f
        
    def update(self, snap, painter=None):
        if snap:
            snap=float(snap)
        else:
            snap=0.0    
        if painter:             
            self.hit_pos=painter.brushes[0].getPos()
            self.hit_pos[0]=snap*round(self.hit_pos[0]/snap)
            self.hit_pos[1]=snap*round(self.hit_pos[1]/snap)
            x = int(self.hit_pos[0])
            y = int(self.hit_pos[1])
            if x==512: x=511
            elif x==0: x=1    
            if y==512: y=511
            elif y==0: y=1
            #painter.images[0] is the last known heightmap
            z=painter.images[0].getBright(x,512-y)*100.0
            if self.currentObject:                
                self.currentObject.setPos(self.hit_pos)
                if self.isLocked == False:
                    self.currentObject.setZ(z+self.currentZ)
                else:
                    self.currentObject.setZ(z)    
                if self.currentWall:
                    self.currentWall.lookAt(self.currentObject)
                if self.currentLight is not None:
                    lpos=self.currentObject.getPos()
                    lpos[2]=lpos[2]+1.0
                    self.lightManager.moveLight(self.currentLight, lpos)
        else:        
            if base.mouseWatcherNode.hasMouse():      
                mpos = base.mouseWatcherNode.getMouse()
                self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY()) 
                try:           
                    self.traverser.traverse(render)
                except:
                    print "error?"    
                if self.queue.getNumEntries() > 0:        
                    self.queue.sortEntries()                
                    self.hit_pos=self.queue.getEntry(0).getSurfacePoint(render)
                    self.hitNode=self.queue.getEntry(0).getIntoNodePath()
                    if self.currentObject: 
                        snap=self._stringToFloat(snap)                    
                        self.hit_pos[0]=snap*round(self.hit_pos[0]/snap)
                        self.hit_pos[1]=snap*round(self.hit_pos[1]/snap)
                        self.currentObject.setPos(self.hit_pos)
                        self.currentObject.setZ(self.hit_pos[2]+self.currentZ)
                        if self.currentWall:
                            self.currentWall.lookAt(self.currentObject)
                        if self.currentLight is not None:
                            lpos=self.currentObject.getPos()
                            lpos[2]=lpos[2]+1.0
                            self.lightManager.moveLight(self.currentLight, lpos)
