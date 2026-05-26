#!/usr/bin/env python3

import csv
import datetime
import hashlib
import json as jsonpy
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback

from functools import wraps
from pprint import pprint
from string import Template
from typing import Any, Union

import mailbox
import smtplib
from smtplib import SMTPException, SMTPAuthenticationError
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

import uno
from com.sun.star.awt import Key, KeyEvent, KeyModifier, Rectangle
from com.sun.star.awt import MessageBoxButtons
from com.sun.star.awt.MessageBoxResults import YES
from com.sun.star.beans import PropertyValue
from com.sun.star.beans.PropertyConcept import ALL
from com.sun.star.container import NoSuchElementException
from com.sun.star.ui.dialogs import TemplateDescription
from com.sun.star.ui import ImageType
from com.sun.star.ui import UIElementType

from .easyuno import Locale, MessageBoxType
from .easydocs import LODocuments
from .easyplus import mureq
from .easymain import (
    _,
    _DATE_OFFSET as DATE_OFFSET,
    IS_MAC,
    IS_WIN,
    LANG,
    LANGUAGE,
    TITLE,
    Macro,
    Paths,
    log,
    classproperty,
    create_instance,
    data_to_dict,
    dict_to_property
)

__all__ = [
    'Config',
    'Dates',
    'Email',
    'Hash',
    'LOInspect',
    'LOMenus',
    'LOShortCuts',
    'LOToolBars',
    'Shell',
    'Timer',
    'URL',
    'catch_exception',
    'debug',
    'error',
    'errorbox',
    'info',
    'msgbox',
    'mri',
    'number_to_text',
    'pos_size',
    'question',
    'render',
    'save_log',
    'set_app_config',
    'sleep',
    'warning',
]

TIMEOUT = 10

PYTHON = 'python'
if IS_WIN:
    PYTHON = 'python.exe'

FILES = {
    'CONFIG': 'zaz-{}.json',
}

_EVENTS = {}


def debug(*messages) -> None:
    """Show messages debug

    :param messages: List of messages to debug
    :type messages: list[Any]
    """

    data = [str(m) for m in messages]
    log.debug('\t'.join(data))
    return


def error(message: Any) -> None:
    """Show message error

    :param message: The message error
    :type message: Any
    """

    log.error(message)
    return


def info(*messages) -> None:
    """Show messages info

    :param messages: List of messages to debug
    :type messages: list[Any]
    """

    data = [str(m) for m in messages]
    log.info('\t'.join(data))
    return


def save_log(path: str, data: Any) -> bool:
    """Save data in file, data append to end and automatic add current time.

    :param path: Path to save log
    :type path: str
    :param data: Data to save in file log
    :type data: Any
    """
    result = True

    try:
        with open(path, 'a') as f:
            f.write(f'{str(Dates.now)} - ')
            pprint(data, stream=f)
    except Exception as e:
        error(e)
        result = False

    return result


def mri(obj: Any) -> None:
    """Inspect object with MRI Extension

    :param obj: Any pyUno object
    :type obj: Any

    `See MRI <https://github.com/hanya/MRI/releases>`_
    """

    m = create_instance('mytools.Mri')
    if m is None:
        msg = 'Extension MRI not found'
        error(msg)
        return

    if hasattr(obj, 'obj'):
        obj = obj.obj
    m.inspect(obj)
    return


def catch_exception(f: Any):
    """Catch exception for any function

    :param f: Any Python function
    :type f: Function instance
    """

    @wraps(f)
    def func(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            name = f.__name__
            if IS_WIN:
                msgbox(traceback.format_exc())
            log.error(name, exc_info=True)
    return func


def set_app_config(node_name: str, key: str, new_value: Any) -> Any:
    """Update value for key in node name.

    :param node_name: Name of node
    :type name: str
    :param key: Name of key
    :type key: str
    :return: True if update sucesfully
    :rtype: bool

    `See Api ConfigurationUpdateAccess <https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1configuration_1_1ConfigurationUpdateAccess.html>`_
    """
    result = True
    current_value = ''
    name = 'com.sun.star.configuration.ConfigurationProvider'
    service = 'com.sun.star.configuration.ConfigurationUpdateAccess'
    cp = create_instance(name, True)
    node = PropertyValue(Name='nodepath', Value=node_name)
    update = cp.createInstanceWithArguments(service, (node,))

    try:
        current_value = update.getPropertyValue(key)
        update.setPropertyValue(key, new_value)
        update.commitChanges()
    except Exception as e:
        error(e)
        if update.hasByName(key) and current_value:
            update.setPropertyValue(key, current_value)
            update.commitChanges()
        result = False

    return result


def msgbox(message: Any, title: str=TITLE, \
    buttons=MessageBoxButtons.BUTTONS_OK, \
    type_message_box=MessageBoxType.INFOBOX) -> int:
    """Create message box

    :param message: Any type message, all is converted to string.
    :type message: Any
    :param title: The title for message box
    :type title: str
    :param buttons: A combination of `com::sun::star::awt::MessageBoxButtons <https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1awt_1_1MessageBoxButtons.html>`_
    :type buttons: long
    :param type_message_box: The `message box type <https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1awt.html#ad249d76933bdf54c35f4eaf51a5b7965>`_
    :type type_message_box: enum
    :return: `MessageBoxResult <https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1awt_1_1MessageBoxResults.html>`_
    :rtype: int

    `See Api XMessageBoxFactory <http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1XMessageBoxFactory.html>`_
    """

    toolkit = create_instance('com.sun.star.awt.Toolkit')
    parent = toolkit.getDesktopWindow()
    box = toolkit.createMessageBox(parent, type_message_box, buttons, title, str(message))
    return box.execute()


def question(message: str, title: str=TITLE) -> bool:
    """Create message box question, show buttons YES and NO

    :param message: Message question
    :type message: str
    :param title: The title for message box
    :type title: str
    :return: True if user click YES and False if click NO
    :rtype: bool
    """
    buttons = MessageBoxButtons.BUTTONS_YES_NO
    result = msgbox(message, title, buttons, MessageBoxType.QUERYBOX)
    return result == YES


def warning(message: Any, title: str=TITLE) -> int:
    """Create message box with icon warning

    :param message: Any type message, all is converted to string.
    :type message: Any
    :param title: The title for message box
    :type title: str
    :return: MessageBoxResult
    :rtype: int
    """
    return msgbox(message, title, type_message_box=MessageBoxType.WARNINGBOX)


def errorbox(message: Any, title: str=TITLE) -> int:
    """Create message box with icon error

    :param message: Any type message, all is converted to string.
    :type message: Any
    :param title: The title for message box
    :type title: str
    :return: MessageBoxResult
    :rtype: int
    """
    return msgbox(message, title, type_message_box=MessageBoxType.ERRORBOX)


def sleep(seconds: int):
    """Sleep for seconds

    :param seconds: Seconds for sleep.
    :type seconds: int
    """
    time.sleep(seconds)
    return


def render(template, data):
    s = Template(template)
    return s.safe_substitute(**data)


def pos_size(x, y, width, height):
    return Rectangle(x, y, width, height)


def number_to_text(value, language='', variant='', country=''):
    locale = Locale()
    if not language:
        language = LANG
        variant = LANGUAGE.split('-')[1]
    locale.Language = language
    locale.Country = country
    locale.Variant = variant
    nt = create_instance('com.sun.star.linguistic2.NumberText')
    text = nt.getNumberText(str(value), locale)
    return text


class Services():

    @classproperty
    def toolkit(cls):
        instance = create_instance('com.sun.star.awt.Toolkit', True)
        return instance

    @classproperty
    def desktop(cls):
        """Create desktop instance

        :return: Desktop instance
        :rtype: pyUno
        """
        instance = create_instance('com.sun.star.frame.Desktop', True)
        return instance


class LOInspect():
    """Class inspect

    Inspired by `MRI <https://github.com/hanya/MRI/releases>`_
    """
    TYPE_CLASSES = {
        'INTERFACE': '-Interface-',
        'SEQUENCE': '-Sequence-',
        'STRUCT': '-Struct-',
    }

    def __init__(self, obj: Any, to_doc: bool=True):
        """Introspection objects pyUno

        :param obj: Object to inspect
        :type obj: Any pyUno
        :param to_doc: If show info in new doc Calc
        :type to_doc: bool
        """
        self._obj = obj
        if hasattr(obj, 'obj'):
            self._obj = obj.obj
        self._properties = ()
        self._methods = ()
        self._interfaces = ()
        self._services = ()
        self._listeners = ()

        introspection = create_instance('com.sun.star.beans.Introspection')
        result = introspection.inspect(self._obj)
        if result:
            self._properties = self._get_properties(result)
            self._methods = self._get_methods(result)
            self._interfaces = self._get_interfaces(result)
            self._services = self._get_services(self._obj)
            self._listeners = self._get_listeners(result)
            self._to_doc(to_doc)

    def _to_doc(self, to_doc: bool):
        if not to_doc:
            return

        doc = LODocuments().new()
        sheet = doc[0]
        sheet.name = 'Properties'
        sheet['A1'].data = self.properties

        sheet = doc.insert('Methods')
        sheet['A1'].data = self.methods

        sheet = doc.insert('Interfaces')
        sheet['A1'].data = self.interfaces

        sheet = doc.insert('Services')
        if self.services:
            sheet['A1'].data = self.services

        sheet = doc.insert('Listeners')
        sheet['A1'].data = self.listeners

        return

    def _get_value(self, p: Any):
        type_class = p.Type.typeClass.value
        if type_class in self.TYPE_CLASSES:
            return self.TYPE_CLASSES[type_class]

        value = ''
        try:
            value = getattr(self._obj, p.Name)
            if type_class == 'ENUM' and value:
                value = value.value
            elif type_class == 'TYPE':
                value = value.typeName
            elif value is None:
                value = '-void-'
        except:
            value = '-error-'

        return str(value)

    def _get_attributes(self, a: Any):
        PA = {1 : 'Maybe Void', 16 : 'Read Only'}
        attr = ', '.join([PA.get(k, '') for k in PA.keys() if a & k])
        return attr

    def _get_property(self, p: Any):
        name = p.Name
        tipo = p.Type.typeName
        value = self._get_value(p)
        attr = self._get_attributes(p.Attributes)
        return name, tipo, value, attr

    def _get_properties(self, result: Any):
        properties = result.getProperties(ALL)
        data = [('Name', 'Type', 'Value', 'Attributes')]
        data += [self._get_property(p) for p in properties]
        return data

    def _get_arguments(self, m: Any):
        arguments = '( {} )'.format(', '.join(
                [' '.join((
                    f'[{p.aMode.value.lower()}]',
                    p.aName,
                    p.aType.Name)) for p in m.ParameterInfos]
            ))
        return arguments

    def _get_method(self, m: Any):
        name = m.Name
        arguments = self._get_arguments(m)
        return_type = m.ReturnType.Name
        class_name = m.DeclaringClass.Name
        return name, arguments, return_type, class_name

    def _get_methods(self, result: Any):
        methods = result.getMethods(ALL)
        data = [('Name', 'Arguments', 'Return Type', 'Class')]
        data += [self._get_method(m) for m in methods]
        return data

    def _get_interfaces(self, result: Any):
        methods = result.getMethods(ALL)
        interfaces = {m.DeclaringClass.Name for m in methods}
        return tuple(zip(interfaces))

    def _get_services(self, obj: Any):
        try:
            data = [str(s) for s in obj.getSupportedServiceNames()]
            data = tuple(zip(data))
        except:
            data = ()
        return data

    def _get_listeners(self, result: Any):
        data = [l.typeName for l in result.getSupportedListeners()]
        return tuple(zip(data))

    @property
    def properties(self):
        return self._properties

    @property
    def methods(self):
        return self._methods

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def services(self):
        return self._services

    @property
    def listeners(self):
        return self._listeners


class Dates(object):
    """Class for datetimes
    """
    _start = None

    @classproperty
    def now(cls):
        """Current local date and time

        :return: Return the current local date and time, remove microseconds.
        :rtype: datetime
        """
        return datetime.datetime.now().replace(microsecond=0)

    @classproperty
    def now_time(cls):
        """Current local time

        :return: Return the current local time
        :rtype: time
        """
        return cls.now.time()

    @classproperty
    def today(cls):
        """Current local date

        :return: Return the current local date
        :rtype: date
        """
        return datetime.date.today()

    @classproperty
    def epoch(cls):
        """Get unix time

        :return: Return unix time
        :rtype: int

        `See Unix Time <https://en.wikipedia.org/wiki/Unix_time>`_
        """
        n = cls.now
        e = int(time.mktime(n.timetuple()))
        return e

    @classmethod
    def date(cls, year: int, month: int, day: int):
        """Get date from year, month, day

        :param year: Year of date
        :type year: int
        :param month: Month of date
        :type month: int
        :param day: Day of day
        :type day: int
        :return: Return the date
        :rtype: date

        `See Python date <https://docs.python.org/3/library/datetime.html#date-objects>`_
        """
        d = datetime.date(year, month, day)
        return d

    @classmethod
    def time(cls, hours: int, minutes: int, seconds: int):
        """Get time from hour, minutes, seconds

        :param hours: Hours of time
        :type hours: int
        :param minutes: Minutes of time
        :type minutes: int
        :param seconds: Seconds of time
        :type seconds: int
        :return: Return the time
        :rtype: datetime.time
        """
        t = datetime.time(hours, minutes, seconds)
        return t

    @classmethod
    def datetime(cls, year: int, month: int, day: int, hours: int, minutes: int, seconds: int):
        """Get datetime from year, month, day, hours, minutes and seconds

        :param year: Year of date
        :type year: int
        :param month: Month of date
        :type month: int
        :param day: Day of day
        :type day: int
        :param hours: Hours of time
        :type hours: int
        :param minutes: Minutes of time
        :type minutes: int
        :param seconds: Seconds of time
        :type seconds: int
        :return: Return datetime
        :rtype: datetime
        """
        dt = datetime.datetime(year, month, day, hours, minutes, seconds)
        return dt

    @classmethod
    def str_to_date(cls, str_date: str, template: str, to_calc: bool=False):
        """Get date from string

        :param str_date: Date in string
        :type str_date: str
        :param template: Formato of date string
        :type template: str
        :param to_calc: If date is for used in Calc cell
        :type to_calc: bool
        :return: Return date or int if used in Calc
        :rtype: date or int

        `See Python strptime <https://docs.python.org/3/library/datetime.html#datetime.datetime.strptime>`_
        """
        d = datetime.datetime.strptime(str_date, template).date()
        if to_calc:
            d = d.toordinal() - DATE_OFFSET
        return d

    @classmethod
    def calc_to_date(cls, value: float):
        """Get date from calc value

        :param value: Float value from cell
        :type value: float
        :return: Return the current local date
        :rtype: date

        `See Python fromordinal <https://docs.python.org/3/library/datetime.html#datetime.datetime.fromordinal>`_
        """
        d = datetime.date.fromordinal(int(value) + DATE_OFFSET)
        return d

    @classmethod
    def start(cls):
        """Start counter
        """
        cls._start = cls.now
        info('Start: ', cls._start)
        return

    @classmethod
    def end(cls, get_seconds: bool=True):
        """End counter

        :param get_seconds: If return value in total seconds
        :type get_seconds: bool
        :return: Return the timedelta or total seconds
        :rtype: timedelta or int
        """
        e = cls.now
        td = e - cls._start
        result = str(td)
        if get_seconds:
            result = td.total_seconds()
        info('End: ', e)
        return result


class Email():
    """Class for send email
    """
    class SmtpServer(object):

        def __init__(self, config):
            self._server = None
            self._error = ''
            self._sender = ''
            self._is_connect = self._login(config)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.close()

        @property
        def is_connect(self):
            return self._is_connect

        @property
        def error(self):
            return self._error

        def _login(self, config):
            name = config['server']
            port = config['port']
            is_ssl = config.get('ssl', False)
            starttls = config.get('starttls', False)
            self._sender = config['user']
            try:
                if starttls:
                    self._server = smtplib.SMTP(name, port, timeout=TIMEOUT)
                    self._server.ehlo()
                    self._server.starttls()
                    self._server.ehlo()
                elif is_ssl:
                    self._server = smtplib.SMTP_SSL(name, port, timeout=TIMEOUT)
                    self._server.ehlo()
                else:
                    self._server = smtplib.SMTP(name, port, timeout=TIMEOUT)

                self._server.login(self._sender, config['password'])
                msg = 'Connect to: {}'.format(name)
                debug(msg)
                return True
            except smtplib.SMTPAuthenticationError as e:
                if '535' in str(e):
                    self._error = _('Incorrect user or password')
                    return False
                if '534' in str(e) and 'gmail' in name:
                    self._error = _('Allow less secure apps in GMail')
                    return False
            except smtplib.SMTPException as e:
                self._error = str(e)
                return False
            except Exception as e:
                self._error = str(e)
                return False
            return False

        def _body_validate(self, msg):
            body = msg.replace('\n', '<BR>')
            return body

        def send(self, message):
            email = MIMEMultipart()
            email['From'] = self._sender
            email['To'] = message['to']
            email['Cc'] = message.get('cc', '')
            email['Subject'] = message['subject']
            email['Date'] = formatdate(localtime=True)
            if message.get('confirm', False):
                email['Disposition-Notification-To'] = email['From']
            if 'body_text' in message:
                email.attach(MIMEText(message['body_text'], 'plain', 'utf-8'))
            if 'body' in message:
                body = self._body_validate(message['body'])
                email.attach(MIMEText(body, 'html', 'utf-8'))

            paths = message.get('files', ())
            if isinstance(paths, str):
                paths = (paths,)
            for path in paths:
                fn = Paths(path).file_name
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(Paths.read_bin(path))
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition', f'attachment; filename="{fn}"')
                email.attach(part)

            receivers = (
                email['To'].split(',') +
                email['CC'].split(',') +
                message.get('bcc', '').split(','))
            try:
                self._server.sendmail(self._sender, receivers, email.as_string())
                msg = 'Email sent...'
                debug(msg)
                if message.get('path', ''):
                    self.save_message(email, message['path'])
                return True
            except Exception as e:
                self._error = str(e)
                return False
            return False

        def save_message(self, email, path):
            mbox = mailbox.mbox(path, create=True)
            mbox.lock()
            try:
                msg = mailbox.mboxMessage(email)
                mbox.add(msg)
                mbox.flush()
            finally:
                mbox.unlock()
            return

        def close(self):
            try:
                self._server.quit()
                msg = 'Close connection...'
                debug(msg)
            except:
                pass
            return

    @classmethod
    def _send_email(cls, server, messages):
        with cls.SmtpServer(server) as server:
            if server.is_connect:
                for msg in messages:
                    server.send(msg)
            else:
                log.error(server.error)
        return server.error

    @classmethod
    def send(cls, server: dict, messages: Union[dict, tuple, list]):
        """Send email with config server, emails send in thread.

        :param server: Configuration for send emails
        :type server: dict
        :param messages: Dictionary con message or list of messages
        :type messages: dict or iterator
        """
        if isinstance(messages, dict):
            messages = (messages,)
        t = threading.Thread(target=cls._send_email, args=(server, messages))
        t.start()
        return


class Shell(object):
    """Class for subprocess

    `See Subprocess <https://docs.python.org/3.7/library/subprocess.html>`_
    """
    @classmethod
    def run(cls, command: str, capture: bool=False, split: bool=False):
        """Execute commands

        :param command: Command to run
        :type command: str
        :param capture: If capture result of command
        :type capture: bool
        :param split: Some commands need split.
        :type split: bool
        :return: Result of command
        :rtype: Any
        """
        if split:
            cmd = shlex.split(command)
            result = subprocess.run(cmd, capture_output=capture, text=True, shell=IS_WIN)
            if capture:
                result = result.stdout
            else:
                result = result.returncode
        else:
            if capture:
                result = subprocess.check_output(command, shell=True).decode()
            else:
                result = subprocess.Popen(command)
        return result

    @classmethod
    def popen(cls, command: str):
        """Execute commands and return line by line

        :param command: Command to run
        :type command: str
        :return: Result of command
        :rtype: Any
        """
        try:
            proc = subprocess.Popen(shlex.split(command), shell=IS_WIN,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in proc.stdout:
                yield line.decode().rstrip()
        except Exception as e:
            error(e)
            yield str(e)


class Hash(object):
    """Class for hash
    """
    @classmethod
    def digest(cls, method: str, data: str, in_hex: bool=True):
        """Get digest from data with method

        :param method: Digest method: md5, sha1, sha256, sha512, etc...
        :type method: str
        :param data: Data for get digest
        :type data: str
        :param in_hex: If True, get digest in hexadecimal, if False, get bytes
        :type in_hex: bool
        :return: bytes or hex digest
        :rtype: bytes or str
        """

        result = ''
        obj = getattr(hashlib, method)(data.encode())
        if in_hex:
            result = obj.hexdigest()
        else:
            result = obj.digest()
        return result


class Config(object):
    """Class for set and get configurations
    """
    @classmethod
    def set(cls, prefix: str, values: Any, key: str='') -> bool:
        """Save data config in user config like json

        :param prefix: Unique prefix for this data
        :type prefix: str
        :param values: Values for save
        :type values: Any
        :param key: Key for value
        :type key: str
        :return: True if save correctly
        :rtype: bool
        """
        name_file = FILES['CONFIG'].format(prefix)
        path = Paths.join(Paths.user_config, name_file)
        data = values
        if key:
            data = cls.get(prefix)
            data[key] = values
        result = Paths.save_json(path, data)
        return result

    @classmethod
    def get(cls, prefix: str, key: str='') -> Any:
        """Get data config from user config like json

        :param prefix: Unique prefix for this data
        :type prefix: str
        :param key: Key for value
        :type key: str
        :return: data
        :rtype: Any
        """
        data = {}
        name_file = FILES['CONFIG'].format(prefix)
        path = Paths.join(Paths.user_config, name_file)
        if not Paths.exists(path):
            return data

        data = Paths.read_json(path)
        if key and key in data:
            data = data[key]

        return data


class Timer(object):
    """Class for timer thread"""

    class TimerThread(threading.Thread):

        def __init__(self, event, seconds, macro):
            threading.Thread.__init__(self)
            self._event = event
            self._seconds = seconds
            self._macro = macro

        def run(self):
            while not self._event.wait(self._seconds):
                Macro.call(self._macro)
            info('\tTimer stopped... ')
            return

    @classmethod
    def exists(cls, name):
        """Validate in timer **name** exists

        :param name: Timer name, it must be unique
        :type name: str
        :return: True if exists timer name
        :rtype: bool
        """
        global _EVENTS
        return name in _EVENTS

    @classmethod
    def start(cls, name: str, seconds: float, macro: dict):
        """Start timer **name** every **seconds** and execute **macro**

        :param name: Timer name, it must be unique
        :type name: str
        :param seconds: Seconds for wait
        :type seconds: float
        :param macro: Macro for execute
        :type macro: dict
        """
        global _EVENTS

        _EVENTS[name] = threading.Event()
        info(f"Timer '{name}' started, execute macro: '{macro['name']}'")
        thread = cls.TimerThread(_EVENTS[name], seconds, macro)
        thread.start()
        return

    @classmethod
    def stop(cls, name: str):
        """Stop timer **name**

        :param name: Timer name
        :type name: str
        """
        global _EVENTS
        _EVENTS[name].set()
        del _EVENTS[name]
        return

    @classmethod
    def once(cls, name: str, seconds: float, macro: dict):
        """Start timer **name** only once in **seconds** and execute **macro**

        :param name: Timer name, it must be unique
        :type name: str
        :param seconds: Seconds for wait before execute macro
        :type seconds: float
        :param macro: Macro for execute
        :type macro: dict
        """
        global _EVENTS

        _EVENTS[name] = threading.Timer(seconds, Macro.call, (macro,))
        _EVENTS[name].start()
        info(f'Event: "{name}", started... execute in {seconds} seconds')

        return

    @classmethod
    def cancel(cls, name: str):
        """Cancel timer **name** only once events.

        :param name: Timer name, it must be unique
        :type name: str
        """
        global _EVENTS

        if name in _EVENTS:
            try:
                _EVENTS[name].cancel()
                del _EVENTS[name]
                info(f'Cancel event: "{name}", ok...')
            except Exception as e:
                error(e)
        else:
            debug(f'Cancel event: "{name}", not exists...')
        return


class URL(object):
    """Class for simple url open

    `See mureq <https://github.com/slingamn/mureq>`_
    """
    @classmethod
    def get(cls, url: str, **kwargs):
        try:
            result = mureq.get(url, **kwargs)
            err = ''
        except mureq.HTTPException as e:
            result = None
            err = str(e)
        return err, result

    @classmethod
    def post(cls, url: str, body=None, **kwargs):
        try:
            result = mureq.post(url, body, **kwargs)
            err = ''
        except mureq.HTTPException as e:
            result = None
            err = str(e)
        return err, result


class LOShortCuts(object):
    """Classe for manager shortcuts"""
    KEYS = {getattr(Key, k): k for k in dir(Key)}
    MODIFIERS = {
        'shift': KeyModifier.SHIFT,
        'ctrl': KeyModifier.MOD1,
        'alt': KeyModifier.MOD2,
        'ctrlmac': KeyModifier.MOD3,
    }
    COMBINATIONS = {
        0: '',
        1: 'shift',
        2: 'ctrl',
        4: 'alt',
        8: 'ctrlmac',
        3: 'shift+ctrl',
        5: 'shift+alt',
        9: 'shift+ctrlmac',
        6: 'ctrl+alt',
        10: 'ctrl+ctrlmac',
        12: 'alt+ctrlmac',
        7: 'shift+ctrl+alt',
        11: 'shift+ctrl+ctrlmac',
        13: 'shift+alt+ctrlmac',
        14: 'ctrl+alt+ctrlmac',
        15: 'shift+ctrl+alt+ctrlmac',
    }

    def __init__(self, app: str=''):
        self._app = app
        service = 'com.sun.star.ui.GlobalAcceleratorConfiguration'
        if app:
            service = 'com.sun.star.ui.ModuleUIConfigurationManagerSupplier'
            type_app = LODocuments.TYPES[app]
            manager = create_instance(service, True)
            uicm = manager.getUIConfigurationManager(type_app)
            self._config = uicm.ShortCutManager
        else:
            self._config = create_instance(service)

    def __getitem__(self, index):
        return LOShortCuts(index)

    def __contains__(self, item):
        cmd = self.get_by_shortcut(item)
        return bool(cmd)

    def __iter__(self):
        self._i = -1
        return self

    def __next__(self):
        self._i += 1
        try:
            event = self._config.AllKeyEvents[self._i]
            event = self._get_info(event)
        except IndexError:
            raise StopIteration

        return event

    @classmethod
    def to_key_event(cls, shortcut: str):
        """Convert from string shortcut (Shift+Ctrl+Alt+LETTER) to KeyEvent"""
        key_event = KeyEvent()
        keys = shortcut.split('+')
        try:
            for m in keys[:-1]:
                key_event.Modifiers += cls.MODIFIERS[m.lower()]
            key_event.KeyCode = getattr(Key, keys[-1].upper())
        except Exception as e:
            error(e)
            key_event = None
        return key_event

    @classmethod
    def get_url_script(cls, command: Union[str, dict]) -> str:
        """Get uno command or url for macro"""
        url = command
        if isinstance(url, str) and not url.startswith('.uno:'):
            url = f'.uno:{command}'
        elif isinstance(url, dict):
            url = Macro.get_url_script(command)
        return url

    def _get_shortcut(self, k):
        """Get shortcut for key event"""
        # ~ print(k.KeyCode, str(k.KeyChar), k.KeyFunc, k.Modifiers)
        shortcut = f'{self.COMBINATIONS[k.Modifiers]}+{self.KEYS[k.KeyCode]}'
        return shortcut

    def _get_info(self, key):
        """Get shortcut and command"""
        cmd = self._config.getCommandByKeyEvent(key)
        shortcut = self._get_shortcut(key)
        return shortcut, cmd

    def get_all(self):
        """Get all events key"""
        events = [(self._get_info(k)) for k in self._config.AllKeyEvents]
        return events

    def get_by_command(self, command: Union[str, dict]):
        """Get shortcuts by command"""
        url = LOShortCuts.get_url_script(command)
        key_events = self._config.getKeyEventsByCommand(url)
        shortcuts = [self._get_shortcut(k) for k in key_events]
        return shortcuts

    def get_by_shortcut(self, shortcut: str):
        """Get command by shortcut"""
        key_event = LOShortCuts.to_key_event(shortcut)
        try:
            command = self._config.getCommandByKeyEvent(key_event)
        except NoSuchElementException as e:
            error(f'Not exists shortcut: {shortcut}')
            command = ''
        return command

    def set(self, shortcut: str, command: Union[str, dict]) -> bool:
        """Set shortcut to command

        :param shortcut: Shortcut like Shift+Ctrl+Alt+LETTER
        :type shortcut: str
        :param command: Command tu assign, 'UNOCOMMAND' or dict with macro info
        :type command: str or dict
        :return: True if set sucesfully
        :rtype: bool
        """
        result = True
        url = LOShortCuts.get_url_script(command)
        key_event = LOShortCuts.to_key_event(shortcut)
        try:
            self._config.setKeyEvent(key_event, url)
            self._config.store()
        except Exception as e:
            error(e)
            result = False

        return result

    def remove_by_shortcut(self, shortcut: str):
        """Remove by shortcut"""
        key_event = LOShortCuts.to_key_event(shortcut)
        try:
            self._config.removeKeyEvent(key_event)
            result = True
        except NoSuchElementException:
            debug(f'No exists: {shortcut}')
            result = False
        return result

    def remove_by_command(self, command: Union[str, dict]):
        """Remove by shortcut"""
        url = LOShortCuts.get_url_script(command)
        self._config.removeCommandFromAllKeyEvents(url)
        return

    def reset(self):
        """Reset configuration"""
        self._config.reset()
        self._config.store()
        return


class LOMenuDebug():
    """Class for debug info menu"""

    @classmethod
    def _get_info(cls, menu, index):
        """Get every option menu"""
        line = f"({index}) {menu.get('CommandURL', '----------')}"
        submenu = menu.get('ItemDescriptorContainer', None)
        if not submenu is None:
            line += cls._get_submenus(submenu)
        return line

    @classmethod
    def _get_submenus(cls, menu, level=1):
        """Get submenus"""
        line = ''
        for i, v in enumerate(menu):
            data = data_to_dict(v)
            cmd = data.get('CommandURL', '----------')
            line += f'\n{"  " * level}├─ ({i}) {cmd}'
            submenu = data.get('ItemDescriptorContainer', None)
            if not submenu is None:
                line += cls._get_submenus(submenu, level + 1)
        return line

    def __call__(cls, menu):
        for i, m in enumerate(menu):
            data = data_to_dict(m)
            print(cls._get_info(data, i))
        return


class LOMenuBase():
    """Classe base for menus"""
    NODE = 'private:resource/menubar/menubar'
    config = None
    menus = None
    app = ''

    @classmethod
    def _get_index(cls, parent: Any, name: Union[int, str]=''):
        """Get index menu from name

        :param parent: Menu parent
        :type parent: pyUno
        :param name: Menu name for search if is str
        :type name: int or str
        :return: Index of menu
        :rtype: int
        """
        index = None
        if isinstance(name, str) and name:
            for i, m in enumerate(parent):
                menu = data_to_dict(m)
                if menu.get('CommandURL', '') == name:
                    index = i
                    break
        elif isinstance(name, str):
            index = len(parent) - 1
        elif isinstance(name, int):
            index = name
        return index

    @classmethod
    def _get_command_url(cls, menu: dict):
        """Get url from command and set shortcut

        :param menu: Menu data
        :type menu: dict
        :return: URL command
        :rtype: str
        """
        shortcut = menu.pop('ShortCut', '')
        command = menu['CommandURL']
        url = LOShortCuts.get_url_script(command)
        if shortcut:
            LOShortCuts(cls.app).set(shortcut, command)
        return url

    @classmethod
    def _save(cls, parent: Any, menu: dict, index: int):
        """Insert menu

        :param parent: Menu parent
        :type parent: pyUno
        :param menu: New menu data
        :type menu: dict
        :param index: Position to insert
        :type index: int
        """
        # ~ Some day
        # ~ self._menus.insertByIndex(index, new_menu)
        properties = dict_to_property(menu, True)
        uno.invoke(parent, 'insertByIndex', (index, properties))
        cls.config.replaceSettings(cls.NODE, cls.menus)
        return

    @classmethod
    def _insert_submenu(cls, parent: Any, menus: list):
        """Insert submenus recursively

        :param parent: Menu parent
        :type parent: pyUno
        :param menus: List of menus
        :type menus: list
        """
        for i, menu in enumerate(menus):
            submenu = menu.pop('Submenu', False)
            if submenu:
                idc = cls.config.createSettings()
                menu['ItemDescriptorContainer'] = idc
            menu['Type'] = 0
            if menu['Label'][0] == '-':
                menu['Type'] = 1
            else:
                menu['CommandURL'] = cls._get_command_url(menu)
            cls._save(parent, menu, i)
            if submenu:
                cls._insert_submenu(idc, submenu)
        return

    @classmethod
    def _get_first_command(cls, command):
        url = command
        if isinstance(command, dict):
            url = Macro.get_url_script(command)
        return url

    @classmethod
    def insert(cls, parent: Any, menu: dict, after: Union[int, str]=''):
        """Insert new menu

        :param parent: Menu parent
        :type parent: pyUno
        :param menu: New menu data
        :type menu: dict
        :param after: After menu insert
        :type after: int or str
        """
        index = cls._get_index(parent, after) + 1
        submenu = menu.pop('Submenu', False)
        menu['Type'] = 0
        idc = cls.config.createSettings()
        menu['ItemDescriptorContainer'] = idc
        menu['CommandURL'] = cls._get_first_command(menu['CommandURL'])
        cls._save(parent, menu, index)
        if submenu:
            cls._insert_submenu(idc, submenu)
        return

    @classmethod
    def remove(cls, parent: Any, name: Union[str, dict]):
        """Remove name in parent

        :param parent: Menu parent
        :type parent: pyUno
        :param menu: Menu name
        :type menu: str
        """
        if isinstance(name, dict):
            name = Macro.get_url_script(name)
        index = cls._get_index(parent, name)
        if index is None:
            debug(f'Not found: {name}')
            return
        uno.invoke(parent, 'removeByIndex', (index,))
        cls.config.replaceSettings(cls.NODE, cls.menus)
        cls.config.store()
        return


class LOMenu():
    """Classe for individual menu"""

    def __init__(self, config: Any, menus: Any, app: str, menu: Any):
        """
        :param config: Configuration Mananer
        :type config: pyUno
        :param menus: Menu bar main
        :type menus: pyUno
        :param app: Name LibreOffice module
        :type app: str
        :para menu: Particular menu
        :type menu: pyUno
        """
        self._config = config
        self._menus = menus
        self._app = app
        self._parent = menu

    def __contains__(self, name):
        """If exists name in menu"""
        exists = False
        for m in self._parent:
            menu = data_to_dict(m)
            cmd = menu.get('CommandURL', '')
            if name == cmd:
                exists = True
                break
        return exists

    def __getitem__(self, index):
        """Index access"""
        if isinstance(index, int):
            menu = data_to_dict(self._parent[index])
        else:
            for m in self._parent:
                menu = data_to_dict(m)
                cmd = menu.get('CommandURL', '')
                if cmd == index:
                    break

        obj = LOMenu(self._config, self._menus, self._app,
            menu['ItemDescriptorContainer'])
        return obj

    def debug(self):
        """Debug menu"""
        LOMenuDebug()(self._parent)
        return

    def insert(self, menu: dict, after: Union[int, str]='', save: bool=True):
        """Insert new menu

        :param menu: New menu data
        :type menu: dict
        :param after: Insert in after menu
        :type after: int or str
        :param save: For persistente save
        :type save: bool
        """
        LOMenuBase.config = self._config
        LOMenuBase.menus = self._menus
        LOMenuBase.app = self._app
        LOMenuBase.insert(self._parent, menu, after)
        if save:
            self._config.store()
        return

    def remove(self, menu: str):
        """Remove menu

        :param menu: Menu name
        :type menu: str
        """
        LOMenuBase.config = self._config
        LOMenuBase.menus = self._menus
        LOMenuBase.remove(self._parent, menu)
        return


class LOMenuApp():
    """Classe for manager menu by LibreOffice module"""
    NODE = 'private:resource/menubar/menubar'
    MENUS = {
        'file': '.uno:PickList',
        'picklist': '.uno:PickList',
        'tools': '.uno:ToolsMenu',
        'help': '.uno:HelpMenu',
        'window': '.uno:WindowList',
        'edit': '.uno:EditMenu',
        'view': '.uno:ViewMenu',
        'insert': '.uno:InsertMenu',
        'format': '.uno:FormatMenu',
        'styles': '.uno:FormatStylesMenu',
        'formatstyles': '.uno:FormatStylesMenu',
        'sheet': '.uno:SheetMenu',
        'data': '.uno:DataMenu',
        'table': '.uno:TableMenu',
        'formatform': '.uno:FormatFormMenu',
        'page': '.uno:PageMenu',
        'shape': '.uno:ShapeMenu',
        'slide': '.uno:SlideMenu',
        'slideshow': '.uno:SlideShowMenu',
    }

    def __init__(self, app: str):
        """
        :param app: LibreOffice Module: calc, writer, draw, impress, math, main
        :type app: str
        """
        self._app = app
        self._config = self._get_config()
        self._menus = self._config.getSettings(self.NODE, True)

    def _get_config(self):
        """Get config manager"""
        service = 'com.sun.star.ui.ModuleUIConfigurationManagerSupplier'
        type_app = LODocuments.TYPES[self._app]
        manager = create_instance(service, True)
        config = manager.getUIConfigurationManager(type_app)
        return config

    def debug(self):
        """Debug menu"""
        LOMenuDebug()(self._menus)
        return

    def __contains__(self, name):
        """If exists name in menu"""
        exists = False
        for m in self._menus:
            menu = data_to_dict(m)
            cmd = menu.get('CommandURL', '')
            if name == cmd:
                exists = True
                break
        return exists

    def __getitem__(self, index):
        """Index access"""
        if isinstance(index, int):
            menu = data_to_dict(self._menus[index])
        else:
            for m in self._menus:
                menu = data_to_dict(m)
                cmd = menu.get('CommandURL', '')
                if cmd == index or cmd == self.MENUS[index.lower()]:
                    break

        obj = LOMenu(self._config, self._menus, self._app,
            menu['ItemDescriptorContainer'])
        return obj

    def insert(self, menu: dict, after: Union[int, str]='', save: bool=True):
        """Insert new menu

        :param menu: New menu data
        :type menu: dict
        :param after: Insert in after menu
        :type after: int or str
        :param save: For persistente save
        :type save: bool
        """
        LOMenuBase.config = self._config
        LOMenuBase.menus = self._menus
        LOMenuBase.app = self._app
        LOMenuBase.insert(self._menus, menu, after)
        if save:
            self._config.store()
        return

    def remove(self, menu: str):
        """Remove menu

        :param menu: Menu name
        :type menu: str
        """
        LOMenuBase.config = self._config
        LOMenuBase.menus = self._menus
        LOMenuBase.remove(self._menus, menu)
        return


class LOMenus():
    """Classe for manager menus"""

    def __getitem__(self, index):
        """Index access"""
        return LOMenuApp(index)


class LOToolBarApp():
    """Classe for manager toolbars by LibreOffice module"""
    NODE = 'private:resource/toolbar'

    def __init__(self, app: str):
        """
        :param app: LibreOffice Module: calc, writer, draw, impress, math, main
        :type app: str
        """
        self._app = app
        self._config = self._get_config()
        self._images = self._config.getImageManager()

    def __getitem__(self, name):
        """Index access"""
        url = f'{self.NODE}/{name}'
        tb = self._config.getSettings(url, True)
        return tb

    def _get_config(self):
        """Get config manager"""
        service = 'com.sun.star.ui.ModuleUIConfigurationManagerSupplier'
        type_app = LODocuments.TYPES[self._app]
        manager = create_instance(service, True)
        config = manager.getUIConfigurationManager(type_app)
        return config

    def _get_command(self, command):
        url = command
        if isinstance(command, dict):
            url = Macro.get_url_script(command)
        elif url.startswith('service:'):
            pass
        elif not url.startswith('.uno:'):
            url = f'.uno:{command}'
        return url

    def _get_image(self, path):
        service = 'com.sun.star.graphic.GraphicProvider'
        path_url = Paths.to_url(path)
        gp = create_instance(service)
        args = dict_to_property({'URL': path_url})
        image = gp.queryGraphic(args)
        return image

    def _set_images(self, images, save):
        for command, path in images:
            image = self._get_image(path)
            self._images.insertImages(ImageType.SIZE_LARGE, (command,), (image,))

        if save:
            self._images.store()
        return

    def insert(self, name: str, items: Union[tuple, list], save: bool=True):
        """Insert new toolbar

        :param name: Name for new toolbar
        :type menu: str
        :param items: Each item for insert in toolbar
        :type items: tuple or list
        :param save: For persistente save
        :type save: bool
        """
        settings = self._config.createSettings()
        settings.UIName = name

        name = name.lower().replace(' ', '_')
        URL = f'{self.NODE}/{name}'
        images = []

        for item in items:
            image = item.get('Image', '')
            command = self._get_command(item['CommandURL'])
            if image:
                images.append((command, image))
            data = dict_to_property({'CommandURL': command,
                'Label': item['Label'], 'Type': 0, 'Visible': True}, True)
            uno.invoke(settings, 'insertByIndex', (settings.Count, data))

        if self._config.hasSettings(URL):
            self._config.replaceSettings(URL, settings)
        else:
            self._config.insertSettings(URL, settings)

        if images:
            self._set_images(images, save)

        if save:
            self._config.store()
        return

    def remove(self, name: str):
        name = name.lower().replace(' ', '_')
        URL = f'{self.NODE}/{name}'
        if self._config.hasSettings(URL):
            self._config.removeSettings(URL)
            self._config.store()
        return

    @property
    def elements(self):
        names = []
        elements = self._config.getUIElementsInfo(UIElementType.TOOLBAR)
        for element in elements:
            for e in element:
                if e.Name == 'ResourceURL':
                    names.append(e.Value[25:])
        return tuple(names)


class LOToolBars():
    """Classe for manager menus"""

    def __getitem__(self, app):
        """Index access"""
        return LOToolBarApp(app)
