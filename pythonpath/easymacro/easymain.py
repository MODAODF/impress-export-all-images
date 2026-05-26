#!/usr/bin/env python3

import csv
import datetime
import getpass
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile

from pathlib import Path
from typing import Any, Union

import uno
import unohelper
from com.sun.star.beans import PropertyValue, NamedValue, StringPair
from com.sun.star.datatransfer import XTransferable, DataFlavor
from com.sun.star.ui.dialogs import TemplateDescription

from .messages import MESSAGES


__all__ = [
    'DESKTOP',
    'INFO_DEBUG',
    'IS_APPIMAGE',
    'IS_FLATPAK',
    'IS_MAC',
    'IS_WIN',
    'LANG',
    'LANGUAGE',
    'NAME',
    'OS',
    'PC',
    'USER',
    'VERSION',
    'ClipBoard',
    'Color',
    'LOMain',
    'Macro',
    'Paths',
    'RecentDocuments',
    'Setting',
    'create_instance',
    'data_to_dict',
    'dict_to_property',
    'get_app_config',
    'run_in_thread',
]


_CTX = uno.getComponentContext()
_SM = _CTX.getServiceManager()


# Global variables
OS = platform.system()
DESKTOP = os.environ.get('DESKTOP_SESSION', '')
PC = platform.node()
USER = getpass.getuser()
IS_WIN = OS == 'Windows'
IS_MAC = OS == 'Darwin'
IS_FLATPAK = bool(os.getenv('FLATPAK_ID', ''))
IS_APPIMAGE = bool(os.getenv('APPIMAGE', ''))


_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
_LOG_DATE = '%Y/%m/%d %H:%M:%S'
if IS_WIN:
    logging.addLevelName(logging.ERROR, 'ERROR')
    logging.addLevelName(logging.DEBUG, 'DEBUG')
    logging.addLevelName(logging.INFO, 'INFO')
else:
    logging.addLevelName(logging.ERROR, '\033[1;41mERROR\033[1;0m')
    logging.addLevelName(logging.DEBUG, '\x1b[33mDEBUG\033[1;0m')
    logging.addLevelName(logging.INFO, '\x1b[32mINFO\033[1;0m')
logging.basicConfig(level=logging.DEBUG, format=_LOG_FORMAT, datefmt=_LOG_DATE)
log = logging.getLogger(__name__)


def create_instance(name: str, with_context: bool=False, arguments: Any=None) -> Any:
    """Create a service instance

    :param name: Name of service
    :type name: str
    :param with_context: If used context
    :type with_context: bool
    :param argument: If needed some argument
    :type argument: Any
    :return: PyUno instance
    :rtype: PyUno Object
    """

    if with_context:
        instance = _SM.createInstanceWithContext(name, _CTX)
    elif arguments:
        instance = _SM.createInstanceWithArguments(name, (arguments,))
    else:
        instance = _SM.createInstance(name)

    return instance


def get_app_config(node_name: str, key: str='') -> Any:
    """Get any key from any node from LibreOffice configuration.

    :param node_name: Name of node
    :type name: str
    :param key: Name of key
    :type key: str
    :return: Any value
    :rtype: Any

    `See Api ConfigurationProvider <https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1configuration_1_1ConfigurationProvider.html>`_
    """

    name = 'com.sun.star.configuration.ConfigurationProvider'
    service = 'com.sun.star.configuration.ConfigurationAccess'
    cp = create_instance(name, True)
    node = PropertyValue(Name='nodepath', Value=node_name)
    value = ''

    try:
        value = cp.createInstanceWithArguments(service, (node,))
        if value and value.hasByName(key):
            value = value.getPropertyValue(key)
    except Exception as e:
        log.error(e)
        value = ''

    return value


def set_app_config(node_name: str, key: str, value: Any) -> None:
    """Set any key from any node from LibreOffice configuration.

    :param node_name: Name of node
    :type name: str
    :param key: Name of key
    :type key: str
    :param key: Value
    :type key: Any

    `See Api ConfigurationProvider <https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1configuration_1_1ConfigurationProvider.html>`_
    """

    name = 'com.sun.star.configuration.ConfigurationProvider'
    service = 'com.sun.star.configuration.ConfigurationUpdateAccess'
    cp = create_instance(name, True)
    node = PropertyValue(Name='nodepath', Value=node_name)

    root = cp.createInstanceWithArguments(service, (node,))
    if root.hasByHierarchicalName(key):
        root.setHierarchicalPropertyValue(key, value)
        root.commitChanges()

    return root


def get_config_node(node_name: str) -> Any:
    """Get any node from LibreOffice configuration.

    :param node_name: Name of node
    :type name: str
    """

    name = 'com.sun.star.configuration.ConfigurationProvider'
    service = 'com.sun.star.configuration.ConfigurationUpdateAccess'
    cp = create_instance(name, True)
    node = PropertyValue(Name='nodepath', Value=node_name)
    root = cp.createInstanceWithArguments(service, (node,))

    return root


# Get info LibO
NAME = TITLE = get_app_config('/org.openoffice.Setup/Product', 'ooName')
VERSION = get_app_config('/org.openoffice.Setup/Product','ooSetupVersion')
LANGUAGE = get_app_config('/org.openoffice.Setup/L10N/', 'ooLocale')
LANG = LANGUAGE.split('-')[0]

# Get start date from Calc configuration
node = '/org.openoffice.Office.Calc/Calculate/Other/Date'
year = get_app_config(node, 'YY')
month = get_app_config(node, 'MM')
day = get_app_config(node, 'DD')
_DATE_OFFSET = datetime.date(year, month, day).toordinal()

_info_debug = f"Python: {sys.version}\n\n{platform.platform()}\n\n" + '\n'.join(sys.path)
INFO_DEBUG = f"{NAME} v{VERSION} {LANGUAGE}\n\n{_info_debug}"


def _(msg):
    if LANG == 'en':
        return msg

    if not LANG in MESSAGES:
        return msg

    return MESSAGES[LANG][msg]


def dict_to_property(values: dict, uno_any: bool=False):
    """Convert dictionary to array of PropertyValue

    :param values: Dictionary of values
    :type values: dict
    :param uno_any: If return like array uno.Any
    :type uno_any: bool
    :return: Tuple of PropertyValue or array uno.Any
    :rtype: tuples or uno.Any
    """
    ps = tuple([PropertyValue(Name=n, Value=v) for n, v in values.items()])
    if uno_any:
        ps = uno.Any('[]com.sun.star.beans.PropertyValue', ps)
    return ps


def data_to_dict(data: Union[tuple, list]) -> dict:
    """Convert tuples, list, PropertyValue, NamedValue to dictionary

    :param data: Iterator of values
    :type data: array of tuples, list, PropertyValue or NamedValue
    :return: Dictionary
    :rtype: dict
    """
    d = {}

    if isinstance(data[0], (tuple, list)):
        d = {r[0]: r[1] for r in data}
    elif isinstance(data[0], (PropertyValue, NamedValue)):
        d = {r.Name: r.Value for r in data}

    return d


def run_in_thread(fn: Any) -> Any:
    """Run any function in thread

    :param fn: Any Python function (macro)
    :type fn: Function instance
    """
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


def set_properties(model, properties):
    if 'X' in properties:
        properties['PositionX'] = properties.pop('X')
    if 'Y' in properties:
        properties['PositionY'] = properties.pop('Y')
    keys = tuple(properties.keys())
    values = tuple(properties.values())
    model.setPropertyValues(keys, values)
    return


def get_properties(obj):
    # ~ properties = obj.PropertySetInfo.Properties
    # ~ values = {p.Name: getattr(obj, p.Name) for p in properties}
    data = obj.PropertySetInfo.Properties
    keys = [p.Name for p in data]
    values = obj.getPropertyValues(keys)
    properties = dict(zip(keys, values))
    return properties




# ~ https://github.com/django/django/blob/main/django/utils/functional.py#L61
class classproperty:

    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self


class Macro():
    """Class for call macro

    `See Scripting Framework <https://wiki.documentfoundation.org/Documentation/DevGuide/Scripting_Framework#Scripting_Framework_URI_Specification>`_
    """
    @classmethod
    def call(cls, args: dict, in_thread: bool=False):
        """Call any macro

        :param args: Dictionary with macro location
        :type args: dict
        :param in_thread: If execute in thread
        :type in_thread: bool
        :return: Return None or result of call macro
        :rtype: Any
        """

        result = None
        if in_thread:
            t = threading.Thread(target=cls._call, args=(args,))
            t.start()
        else:
            result = cls._call(args)
        return result

    @classmethod
    def get_url_script(cls, args: dict):
        library = args['library']
        name = args['name']
        language = args.get('language', 'Python')
        location = args.get('location', 'user')
        module = args.get('module', '.')

        if language == 'Python':
            module = '.py$'
        elif language == 'Basic':
            module = f".{module}."
            if location == 'user':
                location = 'application'

        url = 'vnd.sun.star.script'
        url = f'{url}:{library}{module}{name}?language={language}&location={location}'
        return url

    @classmethod
    def _call(cls, args: dict):
        url = cls.get_url_script(args)
        args = args.get('args', ())

        service = 'com.sun.star.script.provider.MasterScriptProviderFactory'
        factory = create_instance(service)
        script = factory.createScriptProvider('').getScript(url)
        result = script.invoke(args, None, None)[0]

        return result


class Color():
    """Class for colors

    `See Web Colors <https://en.wikipedia.org/wiki/Web_colors>`_
    """
    COLORS = {
        'aliceblue': 15792383,
        'antiquewhite': 16444375,
        'aqua': 65535,
        'aquamarine': 8388564,
        'azure': 15794175,
        'beige': 16119260,
        'bisque': 16770244,
        'black': 0,
        'blanchedalmond': 16772045,
        'blue': 255,
        'blueviolet': 9055202,
        'brown': 10824234,
        'burlywood': 14596231,
        'cadetblue': 6266528,
        'chartreuse': 8388352,
        'chocolate': 13789470,
        'coral': 16744272,
        'cornflowerblue': 6591981,
        'cornsilk': 16775388,
        'crimson': 14423100,
        'cyan': 65535,
        'darkblue': 139,
        'darkcyan': 35723,
        'darkgoldenrod': 12092939,
        'darkgray': 11119017,
        'darkgreen': 25600,
        'darkgrey': 11119017,
        'darkkhaki': 12433259,
        'darkmagenta': 9109643,
        'darkolivegreen': 5597999,
        'darkorange': 16747520,
        'darkorchid': 10040012,
        'darkred': 9109504,
        'darksalmon': 15308410,
        'darkseagreen': 9419919,
        'darkslateblue': 4734347,
        'darkslategray': 3100495,
        'darkslategrey': 3100495,
        'darkturquoise': 52945,
        'darkviolet': 9699539,
        'deeppink': 16716947,
        'deepskyblue': 49151,
        'dimgray': 6908265,
        'dimgrey': 6908265,
        'dodgerblue': 2003199,
        'firebrick': 11674146,
        'floralwhite': 16775920,
        'forestgreen': 2263842,
        'fuchsia': 16711935,
        'gainsboro': 14474460,
        'ghostwhite': 16316671,
        'gold': 16766720,
        'goldenrod': 14329120,
        'gray': 8421504,
        'grey': 8421504,
        'green': 32768,
        'greenyellow': 11403055,
        'honeydew': 15794160,
        'hotpink': 16738740,
        'indianred': 13458524,
        'indigo': 4915330,
        'ivory': 16777200,
        'khaki': 15787660,
        'lavender': 15132410,
        'lavenderblush': 16773365,
        'lawngreen': 8190976,
        'lemonchiffon': 16775885,
        'lightblue': 11393254,
        'lightcoral': 15761536,
        'lightcyan': 14745599,
        'lightgoldenrodyellow': 16448210,
        'lightgray': 13882323,
        'lightgreen': 9498256,
        'lightgrey': 13882323,
        'lightpink': 16758465,
        'lightsalmon': 16752762,
        'lightseagreen': 2142890,
        'lightskyblue': 8900346,
        'lightslategray': 7833753,
        'lightslategrey': 7833753,
        'lightsteelblue': 11584734,
        'lightyellow': 16777184,
        'lime': 65280,
        'limegreen': 3329330,
        'linen': 16445670,
        'magenta': 16711935,
        'maroon': 8388608,
        'mediumaquamarine': 6737322,
        'mediumblue': 205,
        'mediumorchid': 12211667,
        'mediumpurple': 9662683,
        'mediumseagreen': 3978097,
        'mediumslateblue': 8087790,
        'mediumspringgreen': 64154,
        'mediumturquoise': 4772300,
        'mediumvioletred': 13047173,
        'midnightblue': 1644912,
        'mintcream': 16121850,
        'mistyrose': 16770273,
        'moccasin': 16770229,
        'navajowhite': 16768685,
        'navy': 128,
        'oldlace': 16643558,
        'olive': 8421376,
        'olivedrab': 7048739,
        'orange': 16753920,
        'orangered': 16729344,
        'orchid': 14315734,
        'palegoldenrod': 15657130,
        'palegreen': 10025880,
        'paleturquoise': 11529966,
        'palevioletred': 14381203,
        'papayawhip': 16773077,
        'peachpuff': 16767673,
        'peru': 13468991,
        'pink': 16761035,
        'plum': 14524637,
        'powderblue': 11591910,
        'purple': 8388736,
        'red': 16711680,
        'rosybrown': 12357519,
        'royalblue': 4286945,
        'saddlebrown': 9127187,
        'salmon': 16416882,
        'sandybrown': 16032864,
        'seagreen': 3050327,
        'seashell': 16774638,
        'sienna': 10506797,
        'silver': 12632256,
        'skyblue': 8900331,
        'slateblue': 6970061,
        'slategray': 7372944,
        'slategrey': 7372944,
        'snow': 16775930,
        'springgreen': 65407,
        'steelblue': 4620980,
        'tan': 13808780,
        'teal': 32896,
        'thistle': 14204888,
        'tomato': 16737095,
        'turquoise': 4251856,
        'violet': 15631086,
        'wheat': 16113331,
        'white': 16777215,
        'whitesmoke': 16119285,
        'yellow': 16776960,
        'yellowgreen': 10145074,
    }

    def _get_color(self, index):
        if isinstance(index, tuple):
            color = (index[0] << 16) + (index[1] << 8) + index[2]
        else:
            if index[0] == '#':
                r, g, b = bytes.fromhex(index[1:])
                color = (r << 16) + (g << 8) + b
            else:
                color = self.COLORS.get(index.lower(), -1)
        return color

    def __call__(self, index):
        return self._get_color(index)

    def __getitem__(self, index):
        return self._get_color(index)


class BaseObject():

    def __init__(self, obj):
        self._obj = obj

    def __enter__(self):
        return self

    @property
    def obj(self):
        """Return original pyUno object"""
        return self._obj


class LOMain():
    """Classe for LibreOffice"""

    class commands():
        """Class for disable and enable commands

        `See DispatchCommands <https://wiki.documentfoundation.org/Development/DispatchCommands>`_
        https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1configuration_1_1ConfigurationProvider.html
        """
        @classmethod
        def _set_app_command(cls, command: str, disable: bool) -> bool:
            """Disable or enabled UNO command

            :param command: UNO command to disable or enabled
            :type command: str
            :param disable: True if disable, False if active
            :type disable: bool
            :return: True if correctly update, False if not.
            :rtype: bool
            """
            NEW_NODE_NAME = f'zaz_disable_command_{command.lower()}'
            name = 'com.sun.star.configuration.ConfigurationProvider'
            # ~ name = 'com.sun.star.configuration.theDefaultProvider'
            service = 'com.sun.star.configuration.ConfigurationUpdateAccess'
            node_name = '/org.openoffice.Office.Commands/Execute/Disabled'

            cp = create_instance(name, True)
            node = PropertyValue(Name='nodepath', Value=node_name)
            update = cp.createInstanceWithArguments(service, (node,))

            result = True
            try:
                if disable:
                    new_node = update.createInstanceWithArguments(())
                    new_node.setPropertyValue('Command', command)
                    if not update.hasByName(NEW_NODE_NAME):
                        update.insertByName(NEW_NODE_NAME, new_node)
                else:
                    update.removeByName(NEW_NODE_NAME)
                update.commitChanges()
            except Exception as e:
                print(e)
                result = False

            return result

        @classmethod
        def disable(cls, command: str) -> bool:
            """Disable UNO command

            :param command: UNO command to disable
            :type command: str
            :return: True if correctly disable, False if not.
            :rtype: bool
            """
            return cls._set_app_command(command, True)

        @classmethod
        def enabled(cls, command: str) -> bool:
            """Enabled UNO command

            :param command: UNO command to enabled
            :type command: str
            :return: True if correctly disable, False if not.
            :rtype: bool
            """
            return cls._set_app_command(command, False)

    @classmethod
    def fonts(cls):
        """Get all font visibles in LibreOffice

        :return: tuple of FontDescriptors
        :rtype: tuple

        `See API FontDescriptor <https://api.libreoffice.org/docs/idl/ref/structcom_1_1sun_1_1star_1_1awt_1_1FontDescriptor.html>`_
        """
        toolkit = create_instance('com.sun.star.awt.Toolkit')
        device = toolkit.createScreenCompatibleDevice(0, 0)
        return device.FontDescriptors

    @classmethod
    def filters(cls):
        """Get all support filters

        `See Help ConvertFilters <https://help.libreoffice.org/latest/en-US/text/shared/guide/convertfilters.html>`_
        `See API FilterFactory <https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1document_1_1FilterFactory.html>`_
        """
        factory = create_instance('com.sun.star.document.FilterFactory')
        rows = [data_to_dict(factory[name]) for name in factory]
        for row in rows:
            row['UINames'] = data_to_dict(row['UINames'])
        return rows

    @classmethod
    def dispatch(cls, frame: Any, command: str, args: dict={}) -> None:
        """Call dispatch, used only if not exists directly in API

        :param frame: doc or frame instance
        :type frame: pyUno
        :param command: Command to execute
        :type command: str
        :param args: Extra argument for command
        :type args: dict

        `See DispatchCommands <`See DispatchCommands <https://wiki.documentfoundation.org/Development/DispatchCommands>`_>`_
        """
        dispatch = create_instance('com.sun.star.frame.DispatchHelper')
        if hasattr(frame, 'frame'):
            frame = frame.frame
        url = command
        if not command.startswith('.uno:'):
            url = f'.uno:{command}'
        opt = dict_to_property(args)
        dispatch.executeDispatch(frame, url, '', 0, opt)
        return


class ClipBoard(object):
    SERVICE = 'com.sun.star.datatransfer.clipboard.SystemClipboard'
    TEXT = 'text/plain;charset=utf-16'
    IMAGE = 'application/x-openoffice-bitmap;windows_formatname="Bitmap"'

    class TextTransferable(unohelper.Base, XTransferable):

        def __init__(self, text):
            df = DataFlavor()
            df.MimeType = ClipBoard.TEXT
            df.HumanPresentableName = 'encoded text utf-16'
            self.flavors = (df,)
            self._data = text

        def getTransferData(self, flavor):
            return self._data

        def getTransferDataFlavors(self):
            return self.flavors

    @classmethod
    def set(cls, value):
        ts = cls.TextTransferable(value)
        sc = create_instance(cls.SERVICE)
        sc.setContents(ts, None)
        return

    @classproperty
    def contents(cls):
        df = None
        text = ''
        sc = create_instance(cls.SERVICE)
        transferable = sc.getContents()
        data = transferable.getTransferDataFlavors()
        for df in data:
            if df.MimeType == cls.TEXT:
                break
        if df:
            text = transferable.getTransferData(df)
        return text

    @classmethod
    def get(cls):
        return cls.contents


class Paths(object):
    """Class for paths
    """
    FILE_PICKER = 'com.sun.star.ui.dialogs.FilePicker'
    FOLDER_PICKER = 'com.sun.star.ui.dialogs.FolderPicker'
    REMOTE_FILE_PICKER = 'com.sun.star.ui.dialogs.RemoteFilePicker'
    OFFICE_FILE_PICKER = 'com.sun.star.ui.dialogs.OfficeFilePicker'

    def __init__(self, path=''):
        if path.startswith('file://'):
            path = str(Path(uno.fileUrlToSystemPath(path)).resolve())
        self._path = Path(path)

    @property
    def path(self):
        """Get base path"""
        return str(self._path.parent)

    @property
    def file_name(self):
        """Get file name"""
        return self._path.name

    @property
    def name(self):
        """Get name"""
        return self._path.stem

    @property
    def ext(self):
        """Get extension"""
        return self._path.suffix
    @property
    def suffix(self):
        return self.ext

    @property
    def suffixes(self):
        """Get extensions"""
        return self._path.suffixes
    @property
    def exts(self):
        return self.suffixes

    @property
    def size(self):
        """Get size"""
        return self._path.stat().st_size

    @property
    def url(self):
        """Get like URL"""
        return self._path.as_uri()

    @property
    def info(self):
        """Get all info like tuple"""
        i = (self.path, self.file_name, self.name, self.ext, self.size, self.url)
        return i

    @property
    def dict(self):
        """Get all info like dict"""
        data = {
            'path': self.path,
            'file_name': self.file_name,
            'name': self.name,
            'ext': self.ext,
            'size': self.size,
            'url': self.url,
        }
        return data

    @property
    def absolute(self):
        return self._path.absolute()

    @classproperty
    def home(self):
        """Get user home"""
        return str(Path.home())

    @classproperty
    def documents(self):
        """Get user save documents"""
        return self.config()

    @classproperty
    def user_profile(self):
        """Get path user profile"""
        path = self.config('UserConfig')
        path = str(Path(path).parent)
        return path

    @classproperty
    def user_config(self):
        """Get path config in user profile"""
        path = self.config('UserConfig')
        return path

    @classproperty
    def python(self):
        """Get path executable python"""
        if IS_WIN:
            path = self.join(self.config('Module'), PYTHON)
        elif IS_MAC:
            path = self.join(self.config('Module'), '..', 'Resources', PYTHON)
        else:
            path = sys.executable
        return path

    @classmethod
    def to_url(cls, path: str) -> str:
        """Convert paths in format system to URL

        :param path: Path to convert
        :type path: str
        :return: Path in URL
        :rtype: str
        """
        if not path.startswith('file://'):
            path = Path(path).as_uri()
        return path

    @classmethod
    def to_system(cls, path:str) -> str:
        """Convert paths in URL to system

        :param path: Path to convert
        :type path: str
        :return: Path system format
        :rtype: str
        """
        if path.startswith('file://'):
            path = str(Path(uno.fileUrlToSystemPath(path)).resolve())
        return path

    @classmethod
    def config(cls, name: str='Work') -> Union[str, list]:
        """Return path from config

        :param name: Name in service PathSettings, default get path documents
        :type name: str
        :return: Path in config, if exists.
        :rtype: str or list

        `See Api XPathSettings <http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1util_1_1XPathSettings.html>`_
        `See Api thePathSettings <https://api.libreoffice.org/docs/idl/ref/singletoncom_1_1sun_1_1star_1_1util_1_1thePathSettings.html>`_
        """

        #  ToDo
        #  ps = _CTX.getValueByName('/singletons/com.sun.star.util.thePathSettings')

        path = create_instance('com.sun.star.util.PathSettings')
        path = cls.to_system(getattr(path, name)).split(';')

        if len(path) == 1:
            path = path[0]
        return path

    @classmethod
    def join(cls, *paths: str) -> str:
        """Join paths

        :param paths: Paths to join
        :type paths: list
        :return: New path with joins
        :rtype: str
        """
        path = str(Path(paths[0]).joinpath(*paths[1:]))
        return path

    @classmethod
    def exists(cls, path: str) -> bool:
        """If exists path

        :param path: Path for validate
        :type path: str
        :return: True if path exists, False if not.
        :rtype: bool
        """
        path = cls.to_system(path)
        result = Path(path).exists()
        return result

    @classmethod
    def exists_app(cls, name_app: str) -> bool:
        """If exists app in system

        :param name_app: Name of application
        :type name_app: str
        :return: True if app exists, False if not.
        :rtype: bool
        """
        result = bool(shutil.which(name_app))
        return result

    @classmethod
    def is_dir(cls, path: str):
        """Validate if path is directory

        :param path: Path for validate
        :type path: str
        :return: True if path is directory, False if not.
        :rtype: bool
        """
        return Path(path).is_dir()

    @classmethod
    def is_file(cls, path: str):
        """Validate if path is a file

        :param path: Path for validate
        :type path: str
        :return: True if path is a file, False if not.
        :rtype: bool
        """
        return Path(path).is_file()

    @classmethod
    def is_symlink(cls, path: str):
        return Path(path).is_symlink()

    @classmethod
    def temp_file(self):
        """Make temporary file"""
        return tempfile.NamedTemporaryFile(mode='w')

    @classmethod
    def temp_dir(self):
        """Make temporary directory"""
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    @classmethod
    def get(cls, init_dir: str='', filters: Union[str, tuple]='', multiple: bool=False) -> Union[str, list]:
        """Get path for open

        :param init_dir: Initial default path
        :type init_dir: str
        :param filters: Filter for show type files: 'xml' or 'txt,xml'
        :type filters: str
        :param multiple: If user can selected multiple files
        :type multiple: bool
        :return: Selected path or paths
        :rtype: str or list

        `See API <https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1ui_1_1dialogs_1_1TemplateDescription.html>`_
        """
        paths = ''

        if init_dir:
            if init_dir.startswith('~'):
                init_dir = str(Path(init_dir).expanduser().resolve())
            else:
                init_dir = str(Path(init_dir).resolve())
        else:
            init_dir = cls.documents
        init_dir = cls.to_url(init_dir)
        file_picker = create_instance(cls.FILE_PICKER)
        file_picker.setTitle(_('Select path'))
        file_picker.setDisplayDirectory(init_dir)
        file_picker.initialize((TemplateDescription.FILEOPEN_SIMPLE,))
        file_picker.setMultiSelectionMode(multiple)
        if filters:
            if isinstance(filters, str):
                for f in filters.split(','):
                    file_picker.appendFilter(f.upper(), f'*.{f.lower()}')
            else:
                for f in filters:
                    file_picker.appendFilter(f[0].upper(), f'*.{f[1].lower()}')

        if file_picker.execute():
            paths = [cls.to_system(p) for p in file_picker.getSelectedFiles()]
            if not multiple:
                paths = paths[0]

        return paths

    @classmethod
    def get_dir(cls, init_dir: str='') -> str:
        """Get path dir

        :param init_dir: Initial default path
        :type init_dir: str
        :return: Selected path
        :rtype: str
        """
        folder_picker = create_instance(cls.FOLDER_PICKER)
        if not init_dir:
            init_dir = cls.documents
        init_dir = cls.to_url(init_dir)
        folder_picker.setTitle(_('Select directory'))
        folder_picker.setDisplayDirectory(init_dir)

        path = ''
        if folder_picker.execute():
            path = cls.to_system(folder_picker.getDirectory())
        return path

    @classmethod
    def get_for_save(cls, init_dir: str='', filters: str=''):
        """Get path for save

        :param init_dir: Initial default path
        :type init_dir: str
        :param filters: Filter for show type files: 'xml' or 'txt,xml'
        :type filters: str
        :return: Selected path
        :rtype: str
        """
        if not init_dir:
            init_dir = cls.documents
        init_dir = cls.to_url(init_dir)

        file_picker = create_instance(cls.FILE_PICKER)
        file_picker.setTitle(_('Select file'))
        file_picker.setDisplayDirectory(init_dir)
        file_picker.initialize((TemplateDescription.FILESAVE_SIMPLE,))

        if filters:
            for f in filters.split(','):
                file_picker.appendFilter(f.upper(), f'*.{f.lower()}')

        path = ''
        if file_picker.execute():
            files = file_picker.getSelectedFiles()
            path = [cls.to_system(f) for f in files][0]
        return path

    @classmethod
    def files(cls, path: str, pattern: str='**') -> list:
        """Get all files in path

        :param path: Path with files
        :type path: str
        :param pattern: For filter files, default get all.
        :type pattern: str
        :return: Files in path
        :rtype: list
        """

        files = [
            str(p) for p in Path(path).glob(pattern, case_sensitive=False) if p.is_file()
            ]

        return files

    @classmethod
    def dirs(cls, path: str, recursive: bool=False) -> list:
        """Get directories in path

        :param path: Path to scan
        :type path: str
        :param recursive: If recursive
        :type recursive: bool
        :return: Directories in path
        :rtype: list
        """
        if recursive:
            dirs = [str(p) for p in Path(path).glob('**')]
        else:
            dirs = [str(p) for p in Path(path).iterdir() if p.is_dir()]
        return dirs

    @classmethod
    def dirs_tree(cls, path: str) -> list:
        """Get directories recursively like tree

        :param path: Path to scan
        :type path: str
        :return: Directories in path, get info in a tuple (ID_FOLDER, ID_PARENT, NAME)
        :rtype: list
        """
        folders = []
        i = 0
        parents = {path: 0}
        for root, dirs, _ in os.walk(path):
            for name in dirs:
                i += 1
                rn = cls.join(root, name)
                if not rn in parents:
                    parents[rn] = i
                folders.append((i, parents[root], name))
        return folders

    @classmethod
    def extension(cls, id_ext: str) -> str:
        """Get path extension install from id

        :param id_ext: ID extension
        :type id_ext: str
        :return: Path extension
        :rtype: str
        """
        pip = _CTX.getValueByName('/singletons/com.sun.star.deployment.PackageInformationProvider')
        path = Paths.to_system(pip.getPackageLocation(id_ext))
        return path

    @classmethod
    def replace_ext(cls, path: str, new_ext: str):
        """Replace extension in file path

        :param path: Path to file
        :type path: str
        :param new_ext: New extension
        :type new_ext: str
        :return: Path with new extension
        :rtype: str
        """
        if not new_ext.startswith('.'):
            new_ext = f'.{new_ext}'
        return Path(path).with_suffix(new_ext)

    @classmethod
    def with_suffix(cls, path: str, new_ext: str):
        return cls.replace_ext(path, new_ext)

    @classmethod
    def with_name(cls, path: str, new_name: str):
        return Path(path).with_name(new_name)

    @classmethod
    def open(cls, path: str):
        """Open any file with default program in system

        :param path: Path to file
        :type path: str
        :return: PID file, only Linux
        :rtype: int
        """
        pid = 0
        if IS_WIN:
            os.startfile(path)
        else:
            pid = subprocess.Popen(['xdg-open', path]).pid
        return pid

    # ~ Save/read data

    @classmethod
    def save(cls, path: str, data: str, encoding: str='utf-8') -> bool:
        """Save data in path with encoding

        :param path: Path to file save
        :type path: str
        :param data: Data to save
        :type data: str
        :param encoding: Encoding for save data, default utf-8
        :type encoding: str
        :return: True, if save corrrectly
        :rtype: bool
        """
        result = bool(Path(path).write_text(data, encoding=encoding))
        return result

    @classmethod
    def save_bin(cls, path: str, data: bytes) -> bool:
        """Save binary data in path

        :param path: Path to file save
        :type path: str
        :param data: Data to save
        :type data: bytes
        :return: True, if save corrrectly
        :rtype: bool
        """
        result = bool(Path(path).write_bytes(data))
        return result

    @classmethod
    def read(cls, path: str, get_lines: bool=False, encoding: str='utf-8') -> Union[str, list]:
        """Read data in path

        :param path: Path to file read
        :type path: str
        :param get_lines: If read file line by line
        :type get_lines: bool
        :return: File content
        :rtype: str or list
        """
        if get_lines:
            with Path(path).open(encoding=encoding) as f:
                data = f.readlines()
        else:
            data = Path(path).read_text(encoding=encoding)
        return data

    @classmethod
    def read_bin(cls, path: str) -> bytes:
        """Read binary data in path

        :param path: Path to file read
        :type path: str
        :return: File content
        :rtype: bytes
        """
        data = Path(path).read_bytes()
        return data

    @classmethod
    def save_json(cls, path: str, data: str):
        """Save data in path file like json

        :param path: Path to file
        :type path: str
        :return: True if save correctly
        :rtype: bool
        """
        data = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True)
        return cls.save(path, data)

    @classmethod
    def read_json(cls, path: str) -> Any:
        """Read path file and load json data

        :param path: Path to file
        :type path: str
        :return: Any data
        :rtype: Any
        """
        data = json.loads(cls.read(path))
        return data

    @classmethod
    def save_csv(cls, path: str, data: Any, args: dict={}):
        """Write CSV

        :param path: Path to file write csv
        :type path: str
        :param data: Data to write
        :type data: Iterable
        :param args: Any argument support for Python library
        :type args: dict

        `See CSV Writer <https://docs.python.org/3.12/library/csv.html#csv.writer>`_
        """
        with open(path, 'w') as f:
            writer = csv.writer(f, **args)
            writer.writerows(data)
        return

    @classmethod
    def read_csv(cls, path: str, args: dict={}) -> list:
        """Read CSV

        :param path: Path to file csv
        :type path: str
        :param args: Any argument support for Python library
        :type args: dict
        :return: Data csv like tuple
        :rtype: tuple

        `See CSV Reader <https://docs.python.org/3.12/library/csv.html#csv.reader>`_
        """
        with open(path) as f:
            rows = list(csv.reader(f, **args))
        return rows

    @classmethod
    def kill(cls, path: str) -> bool:
        """Delete path

        :param path: Path to file or directory
        :type path: str
        :return: True if delete correctly
        :rtype: bool
        """
        result = False

        p = Path(path)
        try:
            if p.is_file():
                p.unlink()
                result = True
            elif p.is_dir():
                shutil.rmtree(path)
                result = True
        except OSError as e:
            log.error(e)

        return result

    @classmethod
    def copy(cls, source: str, target: str='', name: str='') -> str:
        """Copy files ✓

        :param source: Path source
        :type source: str
        :param target: Path target
        :type target: str
        :param name: New name in target
        :type name: str
        :return: Path target
        :rtype: str
        """
        p, f, n, e, _, _ = Paths(source).info
        if target:
            p = target
        e = f'.{e}'
        if name:
            e = ''
            n = name
        path_new = cls.join(p, f'{n}{e}')
        shutil.copy(source, path_new)
        return path_new

    @classmethod
    def zip(cls, source: Union[str, tuple, list], target: str='') -> str:
        """Zip files or directories

        :param source: Path source file or directory or list of files.
        :type source: str or tuple or list
        :param target: Path target
        :type target: str
        :return: Path target
        :rtype: str
        """
        path_zip = target
        if not isinstance(source, (tuple, list)):
            path = Paths(source)
            start = len(path.path) + 1
            if not target:
                path_zip = f'{path.path}/{path.name}.zip'

        if isinstance(source, (tuple, list)):
            files = [(f, f[len(Paths(f).path)+1:]) for f in source]
        elif Paths.is_file(source):
            files = ((source, source[start:]),)
        else:
            files = [(f, f[start:]) for f in Paths.files(source)]

        compression = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(path_zip, 'w', compression=compression) as z:
            for f in files:
                z.write(f[0], f[1])
        return path_zip

    @classmethod
    def unzip(cls, source: str, target: str='', members=None, pwd=None):
        """Unzip files

        :param source: Path source file zip.
        :type source: str
        :param target: Path target folder for extrac content zip.
        :type target: str
        :param members: Tuple of files in zip for extract.
        :type members: tuple
        :param pwd: Password of zip.
        :type pwd: str
        """
        path = target
        if not target:
            path = Paths(source).path
        with zipfile.ZipFile(source) as z:
            if not pwd is None:
                pwd = pwd.encode()
            if isinstance(members, str):
                members = (members,)
            z.extractall(path, members=members, pwd=pwd)
        return

    @classmethod
    def zip_content(cls, path: str) -> list:
        """Get files in zip

        :param path: Path source file zip.
        :type path: str
        :return: Content files
        :rtype: list
        """
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        return names

    @classmethod
    def merge_zip(cls, target, zips):
        try:
            with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as t:
                for path in zips:
                    with zipfile.ZipFile(path, compression=zipfile.ZIP_DEFLATED) as s:
                        for name in s.namelist():
                            t.writestr(name, s.open(name).read())
        except Exception as e:
            error(e)
            return False

        return True

    @classmethod
    def get_path(cls, path: str, with_name: str='', absolute: bool=True, as_uri: bool=True):
        p = Path(path)
        if absolute:
            p = p.absolute()
        if with_name:
            p = p.with_name(with_name)
        if as_uri:
            p = p.as_uri()
        return p


class Setting():
    FILE_NAME_SETTING = 'zaz-{}.json'

    @classmethod
    def save(cls, key: str='', value: Any={}, prefix: str='conf'):
        file_name = cls.FILE_NAME_SETTING.format(prefix)
        path_config = Paths.join(Paths.user_config, file_name)
        values = cls.read(prefix=prefix)
        if key:
            values[key] = value
        else:
            values = value
        result = Paths.save_json(path_config, values)
        return result

    @classmethod
    def read(cls, key: str='', prefix: str='conf'):
        file_name = cls.FILE_NAME_SETTING.format(prefix)
        path_config = Paths.join(Paths.user_config, file_name)
        values = {}
        if not Paths.exists(path_config):
            return values

        values = Paths.read_json(path_config)
        if key:
            values = values.get(key, '')

        return values


class RecentDocuments():

    @classproperty
    def list(cls):
        node = "/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"
        data = get_app_config(node)
        files = [Paths.to_system(p) for p in data.ElementNames]
        return tuple(files)

    @classmethod
    def clear(cls):
        node1 = "/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/ItemList"
        node2 = "/org.openoffice.Office.Histories/Histories/org.openoffice.Office.Histories:HistoryInfo['PickList']/OrderList"

        root = get_config_node(node1)
        for e in root.ElementNames:
            root.removeByName(e)
        root.commitChanges()

        root = get_config_node(node2)
        for e in root.ElementNames:
            root.removeByName(e)
        root.commitChanges()

        return

    @property
    def size(self):
        node = "org.openoffice.Office.Common/History"
        size = get_app_config(node, 'PickListSize')
        return size
    @size.setter
    def size(self, value):
        node = "org.openoffice.Office.Common/History"
        set_app_config(node, 'PickListSize', value)
