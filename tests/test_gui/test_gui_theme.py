"""
novelWriter – GUI Theme and Icons Classes Tester
================================================

This file is a part of novelWriter
Copyright 2018–2022, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import shutil
import pytest

from configparser import ConfigParser

from mock import causeOSError
from novelwriter.constants import nwLabels
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType
from tools import writeFile

from PyQt5.QtGui import QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import QApplication

from novelwriter.config import Config
from novelwriter.gui.theme import GuiIcons, GuiTheme


@pytest.mark.gui
def testGuiTheme_Main(qtbot, nwGUI, fncDir):
    """Test the theme class init.
    """
    mainTheme: GuiTheme = nwGUI.mainTheme
    mainConf: Config = nwGUI.mainConf

    # Methods
    # =======

    mSize = mainTheme.getTextWidth("m")
    assert mSize > 0
    assert mainTheme.getTextWidth("m", mainTheme.guiFont) == mSize

    # Init Fonts
    # ==========

    # The defaults should be set
    defaultFont = mainConf.guiFont
    defaultSize = mainConf.guiFontSize

    # CHange them to nonsense values
    mainConf.guiFont = "notafont"
    mainConf.guiFontSize = 99

    # Let the theme class set them back to default
    mainTheme._setGuiFont()
    assert mainConf.guiFont == defaultFont
    assert mainConf.guiFontSize == defaultSize

    # A second call should just restore the defaults again
    mainTheme._setGuiFont()
    assert mainConf.guiFont == defaultFont
    assert mainConf.guiFontSize == defaultSize

    # Scan for Themes
    # ===============

    assert mainTheme._listConf({}, "not_a_path") is False

    themeOne = os.path.join(fncDir, "themes", "themeone.conf")
    themeTwo = os.path.join(fncDir, "themes", "themetwo.conf")
    writeFile(themeOne, "# Stuff")
    writeFile(themeTwo, "# Stuff")

    result = {}
    assert mainTheme._listConf(result, os.path.join(fncDir, "themes")) is True
    assert result["themeone"] == themeOne
    assert result["themetwo"] == themeTwo

    # Parse Colours
    # =============

    parser = ConfigParser()
    parser["Palette"] = {
        "colour1": "100, 150, 200",
        "colour2": "100, 150, 200, 250",
        "colour3": "250, 250",
        "colour4": "-10, 127, 300",
    }

    # Test the parser for several valid and invalid values
    assert mainTheme._parseColour(parser, "Palette", "colour1") == [100, 150, 200]
    assert mainTheme._parseColour(parser, "Palette", "colour2") == [100, 150, 200]
    assert mainTheme._parseColour(parser, "Palette", "colour3") == [0, 0, 0]
    assert mainTheme._parseColour(parser, "Palette", "colour4") == [0, 127, 255]
    assert mainTheme._parseColour(parser, "Palette", "colour5") == [0, 0, 0]

    # The palette should load with the parsed values
    mainTheme._setPalette(parser, "Palette", "colour1", QPalette.Window)
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == (100, 150, 200, 255)
    mainTheme._setPalette(parser, "Palette", "colour2", QPalette.Window)
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == (100, 150, 200, 255)
    mainTheme._setPalette(parser, "Palette", "colour3", QPalette.Window)
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == (0, 0, 0, 255)
    mainTheme._setPalette(parser, "Palette", "colour4", QPalette.Window)
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == (0, 127, 255, 255)
    mainTheme._setPalette(parser, "Palette", "colour5", QPalette.Window)
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == (0, 0, 0, 255)

    # qtbot.stop()

# END Test testGuiTheme_Main


@pytest.mark.gui
def testGuiTheme_Theme(qtbot, monkeypatch, nwGUI, fncDir):
    """Test the theme part of the class.
    """
    mainTheme: GuiTheme = nwGUI.mainTheme
    mainConf: Config = nwGUI.mainConf

    # List Themes
    # ===========

    shutil.copy(
        os.path.join(mainConf.assetPath, "themes", "default_dark.conf"),
        os.path.join(fncDir, "themes")
    )
    shutil.copy(
        os.path.join(mainConf.assetPath, "themes", "default.conf"),
        os.path.join(fncDir, "themes")
    )
    writeFile(os.path.join(fncDir, "themes", "default.qss"), "/* Stuff */")

    # Block the reading of the files
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert mainTheme.listThemes() == []

    # Load the theme info
    themesList = mainTheme.listThemes()
    assert themesList[0] == ("default_dark", "Default Dark Theme")
    assert themesList[1] == ("default", "Default Theme")

    # A second call should returned the cached list
    assert mainTheme.listThemes() == mainTheme._themeList

    # Check handling of broken theme settings
    mainConf.guiTheme = "not_a_theme"
    assert mainTheme.loadTheme() is False

    # Check handling of unreadable file
    mainConf.guiTheme = "default"
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert mainTheme.loadTheme() is False

    # Load Default Theme
    # ==================

    # Set a mock colour for the window background
    mainTheme._guiPalette.color(QPalette.Window).setRgb(0, 0, 0, 0)

    # Load the default theme
    mainConf.guiTheme = "default"
    assert mainTheme.loadTheme() is True

    # This should load a standard palette
    wCol = QApplication.style().standardPalette().color(QPalette.Window).getRgb()
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb() == wCol

    # Load Default Dark Theme
    # =======================

    mainConf.guiTheme = "default_dark"
    assert mainTheme.loadTheme() is True

    # Check a few values
    assert mainTheme._guiPalette.color(QPalette.Window).getRgb()        == (54, 54, 54, 255)
    assert mainTheme._guiPalette.color(QPalette.WindowText).getRgb()    == (174, 174, 174, 255)
    assert mainTheme._guiPalette.color(QPalette.Base).getRgb()          == (62, 62, 62, 255)
    assert mainTheme._guiPalette.color(QPalette.AlternateBase).getRgb() == (78, 78, 78, 255)

    # qtbot.stop()

# END Test testGuiTheme_Theme


@pytest.mark.gui
def testGuiTheme_Syntax(qtbot, monkeypatch, nwGUI, fncDir):
    """Test the syntax part of the class.
    """
    mainTheme: GuiTheme = nwGUI.mainTheme
    mainConf: Config = nwGUI.mainConf

    # List Themes
    # ===========

    shutil.copy(
        os.path.join(mainConf.assetPath, "syntax", "default_dark.conf"),
        os.path.join(fncDir, "syntax")
    )
    shutil.copy(
        os.path.join(mainConf.assetPath, "syntax", "default_light.conf"),
        os.path.join(fncDir, "syntax")
    )

    # Block the reading of the files
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert mainTheme.listThemes() == []

    # Load the syntax info
    syntaxList = mainTheme.listSyntax()
    assert syntaxList[0] == ("default_dark", "Default Dark")
    assert syntaxList[1] == ("default_light", "Default Light")

    # A second call should returned the cached list
    assert mainTheme.listSyntax() == mainTheme._syntaxList

    # Check handling of broken theme settings
    mainConf.guiSyntax = "not_a_syntax"
    assert mainTheme.loadSyntax() is False

    # Check handling of unreadable file
    mainConf.guiSyntax = "default_light"
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert mainTheme.loadSyntax() is False

    # Load Default Light Syntax
    # =========================

    # Load the default syntax
    mainConf.guiSyntax = "default_light"
    assert mainTheme.loadSyntax() is True

    # Check some values
    assert mainTheme.syntaxName == "Default Light"
    assert mainTheme.colBack == [255, 255, 255]
    assert mainTheme.colText == [0, 0, 0]
    assert mainTheme.colLink == [0, 0, 200]

    # Load Default Dark Theme
    # =======================

    # Load the default syntax
    mainConf.guiSyntax = "default_dark"
    assert mainTheme.loadSyntax() is True

    # Check some values
    assert mainTheme.syntaxName == "Default Dark"
    assert mainTheme.colBack == [54, 54, 54]
    assert mainTheme.colText == [199, 207, 208]
    assert mainTheme.colLink == [184, 200, 0]

    # qtbot.stop()

# END Test testGuiTheme_Syntax


@pytest.mark.gui
def testGuiTheme_Icons(qtbot, caplog, monkeypatch, nwGUI, fncDir):
    """Test the icon cache class.
    """
    iconCache: GuiIcons = nwGUI.mainTheme.iconCache
    mainConf: Config = nwGUI.mainConf

    # Load Theme
    # ==========

    # Invalid theme name
    assert iconCache.loadTheme("not_a_theme") is False

    # Check handling of unreadable file
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert iconCache.loadTheme("typicons_dark") is False

    # Load a broken theme file
    iconsDir = os.path.join(fncDir, "icons")
    os.mkdir(iconsDir)
    os.mkdir(os.path.join(iconsDir, "testicons"))
    writeFile(os.path.join(iconsDir, "testicons", "icons.conf"), (
        "[Main]\n"
        "name = Test Icons\n"
        "\n"
        "[Map]\n"
        "add = add.svg\n"
        "stuff = stuff.svg\n"
    ))

    assetPath = mainConf.assetPath
    mainConf.assetPath = fncDir

    caplog.clear()
    assert iconCache.loadTheme("testicons") is True
    assert "Unknown icon name 'stuff' in config file" in caplog.text
    assert "Icon file 'add.svg' not in theme folder" in caplog.text

    mainConf.assetPath = assetPath

    # Load working theme file
    assert iconCache.loadTheme("typicons_dark") is True
    assert "add" in iconCache._themeMap

    # Load Decorations
    # ================

    # Invalid name should return empty pixmap
    qPix = iconCache.loadDecoration("stuff")
    assert qPix.isNull() is True

    # Load an image
    qPix = iconCache.loadDecoration("wiz-back")
    assert qPix.isNull() is False

    # Fail finding the file
    with monkeypatch.context() as mp:
        mp.setattr("os.path.isfile", lambda *a: False)
        qPix = iconCache.loadDecoration("wiz-back")
        assert qPix.isNull() is True

    # Test image sizes
    qPix = iconCache.loadDecoration("wiz-back", pxW=100, pxH=None)
    assert qPix.isNull() is False
    assert qPix.width() == 100
    assert qPix.height() > 100

    qPix = iconCache.loadDecoration("wiz-back", pxW=None, pxH=100)
    assert qPix.isNull() is False
    assert qPix.width() < 100
    assert qPix.height() == 100

    qPix = iconCache.loadDecoration("wiz-back", pxW=100, pxH=100)
    assert qPix.isNull() is False
    assert qPix.width() == 100
    assert qPix.height() == 100

    # Load Icons
    # ==========

    # Load an unknown icon
    qIcon = iconCache.getIcon("stuff")
    assert isinstance(qIcon, QIcon)
    assert qIcon.isNull() is True

    # Load an icon, it is likelyu already cached
    qIcon = iconCache.getIcon("add")
    assert isinstance(qIcon, QIcon)
    assert qIcon.isNull() is False

    # Load it as a pixmap with a size
    qPix = iconCache.getPixmap("add", (50, 50))
    assert isinstance(qPix, QPixmap)
    assert qPix.isNull() is False
    assert qPix.width() == 50
    assert qPix.height() == 50

    # Load app icon
    qIcon = iconCache.getIcon("novelwriter")
    assert isinstance(qIcon, QIcon)
    assert qIcon.isNull() is False

    # Load mime icon
    qIcon = iconCache.getIcon("proj_nwx")
    assert isinstance(qIcon, QIcon)
    assert qIcon.isNull() is False

    # Load Item Icons
    # ===============

    # Root -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.ROOT, nwItemClass.NOVEL, nwItemLayout.NO_LAYOUT, hLevel="H0"
    ) == iconCache.getIcon(nwLabels.CLASS_ICON[nwItemClass.NOVEL])

    # Folder -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FOLDER, nwItemClass.NOVEL, nwItemLayout.NO_LAYOUT, hLevel="H0"
    ) == iconCache.getIcon("proj_folder")

    # Document H0 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.NO_LAYOUT, hLevel="H0"
    ) == iconCache.getIcon("proj_document")

    # Document H1 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.DOCUMENT, hLevel="H1"
    ) == iconCache.getIcon("proj_title")

    # Document H2 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.DOCUMENT, hLevel="H2"
    ) == iconCache.getIcon("proj_chapter")

    # Document H3 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.DOCUMENT, hLevel="H3"
    ) == iconCache.getIcon("proj_scene")

    # Document H4 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.DOCUMENT, hLevel="H4"
    ) == iconCache.getIcon("proj_section")

    # Document H5 -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.NO_LAYOUT, hLevel="H4"
    ) == iconCache.getIcon("proj_document")

    # Note -> Not Null
    assert iconCache.getItemIcon(
        nwItemType.FILE, nwItemClass.NOVEL, nwItemLayout.NOTE, hLevel="H5"
    ) == iconCache.getIcon("proj_note")

    # No Type -> Null
    assert iconCache.getItemIcon(
        nwItemType.NO_TYPE, nwItemClass.NOVEL, nwItemLayout.DOCUMENT, hLevel="H0"
    ).isNull() is True

    # Header Decorations
    # ==================

    assert iconCache.getHeaderDecoration(-1) == iconCache._headerDec[0]
    assert iconCache.getHeaderDecoration(0)  == iconCache._headerDec[0]
    assert iconCache.getHeaderDecoration(1)  == iconCache._headerDec[1]
    assert iconCache.getHeaderDecoration(2)  == iconCache._headerDec[2]
    assert iconCache.getHeaderDecoration(3)  == iconCache._headerDec[3]
    assert iconCache.getHeaderDecoration(4)  == iconCache._headerDec[4]
    assert iconCache.getHeaderDecoration(5)  == iconCache._headerDec[4]

    # qtbot.stop()

# END Test testGuiTheme_Icons
