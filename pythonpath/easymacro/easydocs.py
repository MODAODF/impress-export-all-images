#!/usr/bin/env python3

from .easymain import log, Paths, create_instance, dict_to_property
from .easystart import LOStart
from .easycalc import LOCalc
from .easywriter import LOWriter
from .easydraw import LODraw
from .easyimpress import LOImpress
from .easymath import LOMath
from .easybase import LOBase, LOBaseSource
from .easyide import LOBasicIDE


DESKTOP = create_instance('com.sun.star.frame.Desktop', True)


class LODocuments():
    """Class for documents
    """
    TYPES = {
        'calc': 'com.sun.star.sheet.SpreadsheetDocument',
        'writer': 'com.sun.star.text.TextDocument',
        'draw': 'com.sun.star.drawing.DrawingDocument',
        'impress': 'com.sun.star.presentation.PresentationDocument',
        'math': 'com.sun.star.formula.FormulaProperties',
        'ide': 'com.sun.star.script.BasicIDE',
        'base': 'com.sun.star.sdb.OfficeDatabaseDocument',
        'main': 'com.sun.star.frame.StartModule',
    }
    _classes = {
        'com.sun.star.frame.StartModule': LOStart,
        'com.sun.star.sheet.SpreadsheetDocument': LOCalc,
        'com.sun.star.text.TextDocument': LOWriter,
        'com.sun.star.drawing.DrawingDocument': LODraw,
        'com.sun.star.presentation.PresentationDocument': LOImpress,
        'com.sun.star.formula.FormulaProperties': LOMath,
        'com.sun.star.sdb.OfficeDatabaseDocument': LOBase,
        'com.sun.star.script.BasicIDE': LOBasicIDE,
    }
    # ~ BASE: 'com.sun.star.sdb.DocumentDataSource',

    def __init__(self):
        self._desktop = DESKTOP

    def __len__(self):
        #  len(self._desktop.Components)
        for i, _ in enumerate(self._desktop.Components):
            pass
        return i + 1

    def __getitem__(self, index):
        # ~ self._desktop.Components[index]
        obj = None

        for i, doc in enumerate(self._desktop.Components):
            if isinstance(index, int) and i == index:
                obj = self._get_class_doc(doc)
                break
            elif isinstance(index, str) and doc.Title == index:
                obj = self._get_class_doc(doc)
                break

        return obj

    def __contains__(self, item):
        doc = self[item]
        return not doc is None

    def __iter__(self):
        self._i = -1
        return self

    def __next__(self):
        self._i += 1
        doc = self[self._i]
        if doc is None:
            raise StopIteration
        else:
            return doc

    def _get_class_doc(self, doc):
        """Identify type doc"""
        main = 'com.sun.star.frame.StartModule'
        if doc.supportsService(main):
            return self._classes[main](doc)

        mm = create_instance('com.sun.star.frame.ModuleManager')
        type_module = mm.identify(doc)
        return self._classes[type_module](doc)

    @property
    def active(self):
        """Get active doc"""
        active = self._desktop.getCurrentComponent()
        obj = self._get_class_doc(active)
        return obj

    def is_registered(self, name):
        dbc = create_instance('com.sun.star.sdb.DatabaseContext')
        return dbc.hasRegisteredDatabase(name)

    def _new_db(self, args: dict):
        FIREBIRD = 'sdbc:embedded:firebird'

        path = Paths(args.pop('Path'))
        register = args.pop('Register', True)
        name = args.pop('Name', '')
        open_db = args.pop('Open', False)
        if register and not name:
            name = path.name

        dbc = create_instance('com.sun.star.sdb.DatabaseContext')
        db = dbc.createInstance()
        db.URL = FIREBIRD
        db.DatabaseDocument.storeAsURL(path.url, ())
        if register:
            dbc.registerDatabaseLocation(name, path.url)

        if open_db:
            return self.open(path.url, args)

        return LOBaseSource(db)

    def new(self, type_doc: str='calc', args: dict={}):
        """Create new document

        :param type_doc: The type doc to create, default is Calc
        :type  type_doc: str
        :param args: Extra argument
        :type args: dict
        :return: New document
        :rtype: Custom class
        """
        if type_doc == 'base':
            return self._new_db(args)

        url = f'private:factory/s{type_doc}'
        opt = dict_to_property(args)
        doc = self._desktop.loadComponentFromURL(url, '_default', 0, opt)
        obj = self._get_class_doc(doc)
        return obj

    def open(self, path: str, args: dict={}):
        """ Open document from path

        :param path: Path to document
        :type  path: str
        :param args: Extra argument
            Usually options:
                Hidden: True or False
                AsTemplate: True or False
                ReadOnly: True or False
                Password: super_secret
                MacroExecutionMode: 4 = Activate macros
                Preview: True or False
        :type args: dict

        `See API XComponentLoader <http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1frame_1_1XComponentLoader.html>`_
        `See API MediaDescriptor <http://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1document_1_1MediaDescriptor.html>`_
        """
        url = Paths.to_url(path)
        opt = dict_to_property(args)
        doc = self._desktop.loadComponentFromURL(url, '_default', 0, opt)
        if doc is None:
            return

        obj = self._get_class_doc(doc)
        return obj
