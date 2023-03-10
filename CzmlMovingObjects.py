# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CzmlMovingObjects
                                 A QGIS plugin
 This plugin creates CZML files for moving objects described as points
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-10-04
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Murat Kendir
        email                : muratkendir@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, Qgis
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .CzmlMovingObjects_dialog import CzmlMovingObjectsDialog
import os.path

# Added
from qgis.core import QgsProject
from pytz import timezone
import pytz
import json
from .Metadata import Metadata

class CzmlMovingObjects:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CzmlMovingObjects_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CZML Moving Objects')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CzmlMovingObjects', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CzmlMovingObjects/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Points to CZML Moving Objects'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&CZML Moving Objects'),
                action)
            self.iface.removeToolBarIcon(action)
    
    #MK Get point based vector layers with names to fill related form elements
    def getPointVectorLayers(self):
        currentLayers = QgsProject.instance().mapLayers()
        pointLayers = []
        pointLayerNames = []
        for layer in currentLayers:
            if currentLayers.get(layer).type().value == 0 and currentLayers.get(layer).geometryType() == 0:
                pointLayers.append(layer)
                pointLayerNames.append(currentLayers.get(layer).name())
        return pointLayerNames

    #MK #Read layer attributes and populate attribute comboxes with them.
    def fill_group_by_combobox(self):
        currentLayers = QgsProject.instance().mapLayers()
        if self.dlg.select_layer_comboBox.currentIndex() != 0:
            for layer in currentLayers:
                if currentLayers.get(layer).name() == self.dlg.select_layer_comboBox.currentText():
                    selectedLayer = currentLayers.get(layer)
                    #print(selectedLayer.attributeAliases())
                    self.dlg.group_by_comboBox.clear()
                    self.dlg.group_by_comboBox.addItem('Not Selected')
                    self.dlg.group_by_comboBox.addItems(selectedLayer.attributeAliases())
        else:
            print('Please select a valid layer.')

    #MK Selecting filename to export czml file
    def browseForFileName(self):
        fileName = QFileDialog.getSaveFileName(self.dlg,"Select output file ","", '*.czml')
        fileURL = fileName[0]
        fileExtension = fileURL[-5:] 
        if fileExtension == '.czml' or fileExtension == '.CZML':
            checkedFileURL = fileURL
        else:
            checkedFileURL = fileURL + '.czml'
        #self.dlg.browse_lineEdit.setText(checkedFileURL)
        self.dlg.lineEditFileName.setText(checkedFileURL)

    def checkClockButton(self):
        if self.dlg.radioButtonClockConf.isChecked():
            self.dlg.dateTimeEditClockCurrent.setEnabled(1)
            self.dlg.dateTimeEditClockBeginning.setEnabled(1)
            self.dlg.dateTimeEditClockEnd.setEnabled(1)
            self.dlg.lineEditClockMultiplier.setEnabled(1)
            self.dlg.comboBoxClockRange.setEnabled(1)
            self.dlg.comboBoxClockStep.setEnabled(1)
        else:
            self.dlg.dateTimeEditClockCurrent.setDisabled(1)
            self.dlg.dateTimeEditClockBeginning.setDisabled(1)
            self.dlg.dateTimeEditClockEnd.setDisabled(1)
            self.dlg.lineEditClockMultiplier.setDisabled(1)
            self.dlg.comboBoxClockRange.setDisabled(1)
            self.dlg.comboBoxClockStep.setDisabled(1)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = CzmlMovingObjectsDialog()
            self.dlg.lineEditFileName.clear()
            self.dlg.browse_pushButton.clicked.connect(self.browseForFileName)
        
        self.dlg.comboBoxTimeZone.clear()
        self.dlg.comboBoxTimeZone.addItems(pytz.all_timezones)
        #print(pytz.all_timezones)
        self.dlg.comboBoxTimeZone.setCurrentText('UTC')

        #If Configure Cesium Clock radio button element selected, then activate clock parameters and get them.
        self.dlg.radioButtonClockConf.clicked.connect(self.checkClockButton)   

        #MK Populate Layers ComboBox with existed poitn based vector layers

        #MK Clear first point based layers combobox, then populate with point layers.
        self.dlg.select_layer_comboBox.clear()
        #MK Set a placeholder text for layer combobox
        self.dlg.select_layer_comboBox.addItem('Select a point layer')
        self.dlg.select_layer_comboBox.addItems(self.getPointVectorLayers())

        #MK Fill Group By Attributes Button
        self.dlg.refresh_attributes_pushButton.clicked.connect(self.fill_group_by_combobox)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Save File after <OK> clicked.
            fileURL = self.dlg.lineEditFileName.text()

            
            #Take CZML Clock time interval options
            if self.dlg.radioButtonClockConf.isChecked():
                selectedTimeZone = self.dlg.comboBoxTimeZone.currentText()
                timeZone = timezone(self.dlg.comboBoxTimeZone.currentText())
                selectedClockCurrent = self.dlg.dateTimeEditClockCurrent.dateTime()
                selectedClockCurrentLocal = timeZone.localize(selectedClockCurrent.toPyDateTime()).isoformat()
                selectedClockBeginning = self.dlg.dateTimeEditClockBeginning.dateTime()
                selectedClockBeginningLocal = timeZone.localize(selectedClockBeginning.toPyDateTime()).isoformat()
                selectedClockEnd = self.dlg.dateTimeEditClockEnd.dateTime()
                selectedClockEndLocal = timeZone.localize(selectedClockEnd.toPyDateTime()).isoformat()
                selectedClockMultiplier = self.dlg.lineEditClockMultiplier.text()
                selectedClockRange = self.dlg.comboBoxClockRange.currentText()
                selectedClockStep = self.dlg.comboBoxClockStep.currentText()
            
            
            #Take Selected layer from current QGIS canvas.
            currentLayers = QgsProject.instance().mapLayers()
            if self.dlg.select_layer_comboBox.currentIndex() != 0:
                for layer in currentLayers:
                    if currentLayers.get(layer).name() == self.dlg.select_layer_comboBox.currentText():
                        selectedLayer = currentLayers.get(layer)
            layerName = selectedLayer.name()
            
            exportedFile = open(fileURL, mode='w', encoding='utf-8')
            
            if self.dlg.radioButtonClockConf.isChecked():
                documentClock = Metadata.Clock(selectedClockCurrentLocal, selectedClockBeginningLocal, selectedClockEndLocal, selectedClockMultiplier, selectedClockRange, selectedClockStep)
                documentMetadata = Metadata("1.0", "document", layerName, documentClock)
            else:
                documentMetadata = Metadata("1.0", "document", layerName)
                print( documentMetadata.getMetaDict() )

            beginningLines ='[\n' +  json.dumps( documentMetadata.getMetaDict(), indent=4 )

            featureLines = ''
            for feature in selectedLayer.getFeatures():
                featureLines += str(round(feature.geometry().asPoint().x(),7)) + '\n'

            wholeDocument = beginningLines + featureLines +'test data 1 2 3\ntest data 5 6 7'
            print(wholeDocument)
            exportedFile.write(wholeDocument)
            exportedFile.close()
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
