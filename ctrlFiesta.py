import sys, re, stat, functools, shutil, platform, logging, textwrap
from os import path

from PySide2 import QtCore, QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from maya import mel, OpenMayaUI
from maya.mel import *

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om

import ctrlFiesta_functions as fFiesta
import ctrlFiesta_util as uFiesta

import shot_utils


#Path to a folder where your thumbnails will be saved
MAYA_APP_DIR = os.getenv("MAYA_APP_DIR")
THUMBNAIL_LIBRARY_PATH="{0}/projects/default/images/curveShapes/".format(MAYA_APP_DIR)
if not os.path.exists(THUMBNAIL_LIBRARY_PATH):
    os.makedirs(THUMBNAIL_LIBRARY_PATH)
    

class ctrlFiestaUi(QtWidgets.QDialog):

    WINDOW_TITLE = "Control Fiesta"
    
    @classmethod
    def maya_main_window(cls):
        main_window_ptr = omui.MQtUtil.mainWindow()
        if sys.version_info.major >= 3:
            return wrapInstance(int(main_window_ptr), QtWidgets.QWidget) # pylint: disable=E0602
        else:
            return wrapInstance(long(main_window_ptr), QtWidgets.QWidget) # pylint: disable=E0602

    def __init__(self):
        super(ctrlFiestaUi, self).__init__(self.maya_main_window())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(415, 440)
        self.resize(415, 440)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.fk_wdg = FKControlWidget()
        self.thumbnails_wdg = ThumbnailControlWidget()

    def create_layout(self):
        form_layout = QtWidgets.QFormLayout()
        form_layout.addWidget(self.fk_wdg)
        form_layout.addWidget(self.thumbnails_wdg)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(form_layout)     

    def create_connections(self):
        self.fk_wdg.create_fk_btn.clicked.connect(self.ctrlFromText)
        self.fk_wdg.save_curve_btn.clicked.connect(self.refresh_ui)
        
    def refresh_ui(self, name):
        self.thumbnails_wdg.tumbnailCreator()
        self.thumbnails_wdg.createThumbnailBtns()    
          
    def ctrlFromInput(self, controller=None):
        pre_parent = None
        sel = fFiesta.selected()
        for i in sel:
            cmds.select(cl=1)
            if controller == None or cmds.objExists(controller) == False:
                controller1 = cmds.circle( nr = (1, 0, 0 ), r = (0.8), name = i + "_CTRL")[0]
                cmds.warning("No curve was found, default circle used instead")
            else:
                controller1 = cmds.duplicate(controller, name = i + "_CTRL")[0]
                
            grp = cmds.group(em = 1, name = i + "_offset_grp")
            cmds.parent(controller1, grp)
            pc = cmds.parentConstraint(i, grp, mo=0)
            cmds.delete(pc)
            cmds.pointConstraint(controller1, i, mo=0)
            cmds.orientConstraint(controller1, i, mo=0)
            if pre_parent != None:
                cmds.parent(grp, pre_parent)
            pre_parent = controller1
                             
    def ctrlFromText(self, text_field_in):
        text_field_in = self.fk_wdg.input_dialog.text()
        if text_field_in == "":
            cmds.warning("you need to write in an existing curves name")
        else:
            self.ctrlFromInput(controller=text_field_in)


class FKControlWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(FKControlWidget, self).__init__(parent)

        self.info_label_1 = QtWidgets.QLabel(
                                             "Tool 1: Write an existing curve in your scene,\n" +
                                             "select your joints and create FKchain.\n" +
                                             "\n" +
                                             "Tool 2: Draw a curve, press save to library, \n select joints and press the desired curve."
                                             )
        self.info_label_1.adjustSize()
        self.info_label_1.setAlignment(QtCore.Qt.AlignHCenter)
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.addStretch()
        info_layout.addWidget(self.info_label_1)
        info_layout.addStretch()

        self.input_dialog_text = QtWidgets.QLabel("CTRL curve: ")
        self.input_dialog_text.setStyleSheet("QLabel { background-color: #6a5991; }")
        self.input_dialog = QtWidgets.QLineEdit()
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.setSpacing(2)
        input_layout.addWidget(self.input_dialog_text)
        input_layout.addWidget(self.input_dialog)
      
        self.create_fk_btn = QtWidgets.QPushButton("Create FKchain")
        self.create_fk_btn.setStyleSheet("QPushButton { background-color: #6a5991; }")
        self.save_curve_btn = QtWidgets.QPushButton("Save curve to library")
        self.save_curve_btn.setStyleSheet("QPushButton { background-color: #91729e; }")
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.create_fk_btn)
        btn_layout.addWidget(self.save_curve_btn)
        btn_layout.addStretch()
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.addLayout(info_layout)
        main_layout.setSpacing(20)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(btn_layout)
    

class ClickableIcon(QtWidgets.QPushButton):
    def __init__(self, icon_path, icon_crv, parent=None):
        super().__init__(parent)
        
        self.icon_name = icon_crv
        self.setIcon(QtGui.QIcon(icon_path))
        
        self.setIconSize(QtCore.QSize(70, 70))  # Set the icon size to match the button size
        self.setFixedSize(70, 70)  # Fix the button size
        
        self.clicked.connect(self.callback_fn)

    def print_image_name(self):
        name = self.icon_name
        print(f"Clicked on image: {name}")
        
    def callback_fn(self, *_):  # _ignore swallows the original button argument
        cleaned = re.sub(r"\d+$", "", self.icon_name)
            
        cleaned_rest = re.sub(".*?([0-9]*)$",r"\1",self.icon_name)
        
        my_shape = cleaned + "Shape" + cleaned_rest
             
        load_from_lb=fFiesta.loadFromLib(shape=my_shape)
        for x in load_from_lb:
            for a in x:
                poid = x.get("points")
                points = list(map(tuple, poid))
                break
            for a in x:
                knots = x.get("knots")
                break
            for a in x:
                degree = x.get("degree")
                break
            for a in x:
                form = x.get("form")
                formd = bool(form)
                break
                    
        sel=fFiesta.selected()
        temp_crv = cmds.curve(p=points, k=knots, per=formd, d=degree)
        if sel:
            cmds.rename(temp_crv, "temp_crv")
            cmds.select(sel)
            ctrlFiestaUi.ctrlFromInput(self, controller="temp_crv")
            cmds.delete("temp_crv")
        if not sel:
            temp_crv
            cmds.rename(temp_crv, cleaned)
        cmds.select(deselect=True)
            


class ThumbnailControlWidget(QtWidgets.QWidget):
        
    def __init__(self, parent=None):
        super(ThumbnailControlWidget, self).__init__(parent)
        
        layout = QtWidgets.QVBoxLayout()
        scroll_area = QtWidgets.QScrollArea()
        scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QFormLayout(scroll_content)

        self.createThumbnailBtns(self.scroll_layout)

        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        
        layout.addWidget(scroll_area)
        
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.addLayout(layout)
        
    def tumbnailCreator(self, args=None):
        sel = fFiesta.selected()
        shape_sel = "\n".join(cmds.listRelatives(sel[0], shapes=True))
        
        obj = str(sel[0]).split("|")[-1]    
        
        selection_curve = sel
        
        get_shp = fFiesta.getShape(crv=sel)
        save_crv = fFiesta.saveToLib(crv=sel, shapeName=shape_sel)
        validate_crv = fFiesta.validateCurve(crv=sel)
        
        for obj in selection_curve:
            shortName = obj.split("|")[-1]
            cmds.rename(obj, shortName)
        
        cmds.setAttr("defaultRenderGlobals.imageFormat", 8)
        cmds.playblast(viewer=False,
                             completeFilename=THUMBNAIL_LIBRARY_PATH + obj + ".jpg",
                             startTime=0,
                             endTime=0,
                             forceOverwrite=True,
                             showOrnaments=False,
                             percent=100,
                             width=70,
                             height=70,
                             framePadding=0,
                             format="image")

    def createThumbnailBtns(self, *args):
        # Clear the existing widgets in the scroll_layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.takeAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        icon_names = cmds.getFileList(folder=THUMBNAIL_LIBRARY_PATH, filespec="*.jpg")

        if len(icon_names) % 2 != 0:
            icon_names.append("")
            
        for i in range(0, len(icon_names), 2):
            icon_path1 = f"{THUMBNAIL_LIBRARY_PATH}" + icon_names[i]
            icon_path2 = f"{THUMBNAIL_LIBRARY_PATH}" + icon_names[i+1]
            
            value1 = icon_names[i]
            value2 = icon_names[i+1]

            name_split1 = path.splitext(value1)[0]
            name_split2 = path.splitext(value2)[0]
            
            icon_label1 = QtWidgets.QLabel(name_split1)
            icon_label2 = QtWidgets.QLabel(name_split2)
                                    
            clickable_icon1 = ClickableIcon(icon_path1, name_split1)
            clickable_icon2 = ClickableIcon(icon_path2, name_split2)
            
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(clickable_icon1)
            row_layout.addWidget(icon_label1)
            if icon_names[i+1] != "":
                row_layout.addWidget(clickable_icon2) 
                row_layout.addWidget(icon_label2)
            
            self.scroll_layout.addRow(row_layout)


class CheckOutWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(CheckOutWidget, self).__init__(parent)

        self.shot_select_cmb = QtWidgets.QComboBox()
        shot_select_layout = QtWidgets.QHBoxLayout()
        shot_select_layout.addStretch()
        shot_select_layout.addWidget(QtWidgets.QLabel("Shot: "))
        shot_select_layout.addWidget(self.shot_select_cmb)

        self.force_overwrite_cb = QtWidgets.QCheckBox("Force Overwrite")
        overwrite_layout = QtWidgets.QHBoxLayout()
        overwrite_layout.addStretch()
        overwrite_layout.addWidget(self.force_overwrite_cb)

        self.ref_wdgs = []
        self.ref_layout = QtWidgets.QVBoxLayout()
        ref_grp_box = QtWidgets.QGroupBox("References")
        ref_grp_box.setLayout(self.ref_layout)

        self.check_out_btn = QtWidgets.QPushButton("Check Out")
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.check_out_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.addLayout(shot_select_layout)
        main_layout.addWidget(ref_grp_box)
        main_layout.addLayout(overwrite_layout)
        main_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.shot_select_cmb.currentTextChanged.connect(self.update_selected_shot_meta)
        self.check_out_btn.clicked.connect(self.load_shot)

        self.refresh_shot_list()

    def refresh_shot_list(self):
        current_text = self.shot_select_cmb.currentText()

        self.shot_select_cmb.blockSignals(True)
        self.shot_select_cmb.clear()

        shot_list = shot_utils.get_shot_list()
        for shot in shot_list:
            self.shot_select_cmb.addItem(shot[0], shot[1])

        self.shot_select_cmb.setCurrentText(current_text)
        self.shot_select_cmb.blockSignals(False)

        self.update_selected_shot_meta()

    def update_selected_shot_meta(self):
        file_path = self.shot_select_cmb.currentData()
        if not file_path:
            return

        shot_meta = shot_utils.read_json(file_path)

        ref_data = shot_meta["references"]
        ref_count = len(ref_data)
        ref_wdg_count = len(self.ref_wdgs)

        extra_ref_wdgs_required = ref_count - ref_wdg_count
        if extra_ref_wdgs_required > 0:
            for i in range(extra_ref_wdgs_required):
                self.ref_wdgs.append(ReferenceWidget())
                self.ref_layout.addWidget(self.ref_wdgs[-1])
                
        for i in range(ref_count):
            self.ref_wdgs[i].set_ref_data(ref_data[i]["ref_node"], ref_data[i]["loaded"])
            self.ref_wdgs[i].setVisible(True)
        for i in range(ref_count, ref_wdg_count):
            self.ref_wdgs[i].setVisible(False)

    def load_shot(self):
        file_path = self.shot_select_cmb.currentData()
        force_overwrite = self.force_overwrite_cb.isChecked()

        loaded_ref_nodes = []
        for ref_wdg in self.ref_wdgs:
            if ref_wdg.is_loaded():
                loaded_ref_nodes.append(ref_wdg.ref_node_name())

        shot_utils.load_shot(file_path, loaded_ref_nodes, force_overwrite)


class ReferenceWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(ReferenceWidget, self).__init__(parent)

        self.loaded_cb = QtWidgets.QCheckBox()
        self.ref_node_label = QtWidgets.QLabel()

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.loaded_cb)
        main_layout.addWidget(self.ref_node_label)
        main_layout.addStretch()
        
    def set_ref_data(self, ref_node_name, loaded):
        self.ref_node_label.setText(ref_node_name)
        self.loaded_cb.setChecked(loaded)

    def ref_node_name(self):
        return self.ref_node_label.text()

    def is_loaded(self):
        return self.isVisible() and self.loaded_cb.isChecked()


if __name__ == "__main__":

    try:
        ctrl_fiesta_ui.close() # pylint: disable=E0601
        ctrl_fiesta_ui.deleteLater()
    except:
        pass

    ctrl_fiesta_ui = ctrlFiestaUi()
    ctrl_fiesta_ui.show()

#---------- 