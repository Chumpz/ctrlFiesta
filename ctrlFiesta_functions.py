from maya import mel, cmds, OpenMayaUI     
from maya.mel import *
import os, sys, re, stat, functools,shutil, platform, logging
import ctrlFiesta_util

#Path to a folder where your shapes jsom file will be saved
SHAPE_LIBRARY_PATH="C:\\Users\\vincent.brandt\\Documents\\maya\\2018\\scripts\\shapeLibrary"
sel = cmds.ls(sl=1)


def getShape(crv= None):
    crvShapes = validateCurve(crv)
    
    crvShapeList = []
    
    for crvShape in crvShapes:
        crvShapeDict = {
        "points": [],
        "knots": [],
        "form": cmds.getAttr(crvShape + ".form"),
        "degree": cmds.getAttr(crvShape + ".degree"),
        }
        points = []
    
    for i in range(cmds.getAttr(crvShape + ".controlPoints", s=1)):
        points.append(cmds.getAttr(crvShape + ".controlPoints[%i]" % i)[0])

    
    crvShapeDict["points"] = points
    crvShapeDict["knots"] = ctrlFiesta_util.getKnots(crvShape)
    
    
    crvShapeList.append(crvShapeDict)
        
    return crvShapeList
    

def validateCurve(crv=None):
    if cmds.nodeType(crv) == "transform" and cmds.nodeType(cmds.listRelatives(crv, c=1, s=1)[0]) == "nurbsCurve":
        crvShapes = cmds.listRelatives(crv, c=1, s=1)
    elif cmds.nodeType(crv) == "nurbsCurve":
        crvShapes = cmds.listRelatives(cmds.listRelatives(crv, p=1)[0], c=1, s=1)
    else:
        cmds.error("The object " + str(crv) + " passed to validateCurve() is not a curve")
    return crvShapes


def loadFromLib(shape=None):
    path = os.path.join(SHAPE_LIBRARY_PATH, shape + ".json")
    data = ctrlFiesta_util.loadData(path)
    return data


def saveToLib(crv=None,
    shapeName=None):
    crvShape = getShape(crv=crv)
    path = os.path.join(SHAPE_LIBRARY_PATH, re.sub("\s", "", shapeName) + ".json")
    for shapeDict in crvShape:
        shapeDict.pop("colour", None)
        ctrlFiesta_util.saveData(path, crvShape)

  


#----------  



