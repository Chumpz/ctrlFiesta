from maya import mel, cmds, OpenMayaUI     
from maya.mel import *
import os, sys, re, stat, functools,shutil, platform, logging
from functools import partial
import ctrlFiesta_functions as fFiesta
import ctrlFiesta_util as uFiesta
import re

#Path to a folder where your thumbnails will be saved
path="C:\\Users\\vincent.brandt\\Documents\\maya\\projects\\default\\images\\curveShapes\\"

def selo():
    selection=cmds.ls(sl=1)
    return selection 
    
def callback_fn(myValue, *_):  # _ignore swallows the original button argument

    cleaned = re.sub(r'\d+$', '', myValue)
    
    cleanedRest = re.sub('.*?([0-9]*)$',r'\1',myValue)
    
    myShape = cleaned + 'Shape' + cleanedRest
     
    loadFromLb=fFiesta.loadFromLib(shape=myShape)
    bit = uFiesta.byteify(loadFromLb)
    for x in loadFromLb:
        for a in x:
            poid = x.get('points')
            points = map(tuple, poid)
            #print points
            break
        for a in x:
            knots = x.get('knots')
            #print knots
            break
        for a in x:
            degree = x.get('degree')
            #print degree
            break
        for a in x:
            form = x.get('form')
            #print form
            break
            
    selected=selo()
    tempCrv = cmds.curve(p=points, k=knots, per=bool(form), d=degree)
    cmds.rename(tempCrv, 'tempCrv')
    cmds.select(selected)
    ctrlFromInput(controller='tempCrv')
    cmds.delete('tempCrv')
            

def createFKWindow():

    windowID = 'window'
       

    if cmds.window(windowID, exists = True):
        cmds.deleteUI('window')        


    window = cmds.window(windowID)
    cmds.rowColumnLayout()
    
    cmds.text('This tool has 2 in one.')
    cmds.text('Write in an existing curve in your scene, select your joints and create FKchain ', align='left')
    cmds.text('Or draw a curve, press save, select joints and press the desired curve. \n', align='left')

    #FK to CTRL creator
    cmds.textFieldGrp( 'textField_A', label = 'CTRL curve: ' )
    
    cmds.button(label = 'Create FKchain', command = ctrlFromText)
        
    #Tumbnail creator
    cmds.button(label = 'Save curve', command = tumbnailCreator)
        
    list = cmds.getFileList( folder=path, filespec='*.jpg' )
    for x in list:
        listm=x.split("|")[-1]
        regularExpr = ".jpg"
        result = re.sub(regularExpr, "", listm)
        button = cmds.iconTextButton( style='iconAndTextHorizontal', label=result, image1=path + listm, command = partial(callback_fn, result))
        
    cmds.showWindow( window )



def tumbnailCreator(args=None):
    sel=selo()
    shapesel = '\n'.join(cmds.listRelatives(sel[0], shapes=True))
    
    obj=str(sel[0]).split("|")[-1]    
    
    selectionCurve = sel
    
    detShp = fFiesta.getShape(crv=sel)
    saveCrv = fFiesta.saveToLib(crv=sel, shapeName=shapesel)
    validateCrv = fFiesta.validateCurve(crv=sel)
    
    for obj in selectionCurve:
        shortName = obj.split("|")[-1]
        cmds.rename(obj, shortName)
    
    cmds.setAttr("defaultRenderGlobals.imageFormat", 8)
    cmds.playblast(viewer=False,
                         completeFilename=path + obj + ".jpg",
                         startTime=0,
                         endTime=0,
                         forceOverwrite=True,
                         showOrnaments=False,
                         percent=100,
                         width=70,
                         height=70,
                         framePadding=0,
                         format="image")
    createFKWindow()


def ctrlFromInput(controller=None):
    preParent = None
    sel = selo()
    for i in sel:
        cmds.select(cl=1)
        if controller == None or cmds.objExists(controller) == False:
            controller1 = cmds.circle( nr = (1, 0, 0 ), r = (0.8), name = i + "_CTRL")[0]
        else:
            controller1 = cmds.duplicate(controller, name = i + "_CTRL")[0]
            
        grp = cmds.group(em = 1, name = i + "_offset_grp")
        cmds.parent(controller1, grp)
        pc = cmds.parentConstraint(i, grp, mo=0)
        cmds.delete(pc)
        cmds.pointConstraint(controller1, i, mo=0)
        cmds.orientConstraint(controller1, i, mo=0)
        if preParent != None:
            cmds.parent(grp, preParent)
        preParent = controller1
                         
def ctrlFromText(args=None):
    textFieldIn = cmds.textFieldGrp( 'textField_A', query = True, text = True)
    if textFieldIn == '':
        cmds.warning('you need to write in an existing curves name')
    else:
        ctrlFromInput(controller=textFieldIn)

createFKWindow()
#------


