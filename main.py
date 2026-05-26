#!/usr/bin/env python

import uno
import unohelper
from com.sun.star.task import XJobExecutor

ID_EXTENSION = "org.ossii.ImpressExportAllImages.do"
SERVICE = ("com.sun.star.task.Job",)


class MainJob(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx

    def trigger(self, args):
        from exportimages import run

        run()


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(MainJob, ID_EXTENSION, SERVICE)
