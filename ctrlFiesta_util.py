import os
import json
from maya import cmds as mc, OpenMaya as om

def validatePath(path=None):
    if os.path.isfile(path):
        confirm = mc.confirmDialog(title='Overwrite file?',
                                message='The file ' + path + ' already exists.Do you want to overwrite it?',
                                button=['Yes', 'No'],
                                defaultButton='Yes',
                                cancelButton='No',
                                dismissString='No')
        if confirm == "No":
            mc.warning("The file " + path + " was not saved")
            return 0
    return 1

def loadData(path=None):
    '''Loads raw JSON data from a file and returns it as a dict'''
    if os.path.isfile(path):
        f = open(path, "r")
        data = json.loads(f.read())
        f.close()
        return data
    else:
        mc.error("The file " + path + " doesn't exist")


def saveData(path=None,
             data=None):
    '''Saves a dictionary as JSON in a file'''
    if validatePath(path):
        f = open(path, "w")
        f.write(json.dumps(data, sort_keys=1, indent=4, separators=(",", ":")))
        f.close()
        return 1
    return 0    
    
def getKnots(crvShape=None):
    mObj = om.MObject()
    sel = om.MSelectionList()
    sel.add(crvShape)
    sel.getDependNode(0, mObj)
    
    fnCurve = om.MFnNurbsCurve(mObj)
    tmpKnots = om.MDoubleArray()
    fnCurve.getKnots(tmpKnots)
    
    return [tmpKnots[i] for i in range(tmpKnots.length())]
    
def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input