# -*- coding: utf-8 -*-

import os.path

import Autodesk.Revit.Exceptions
import System
import clr

clr.AddReference('dosymep.Revit.dll')
clr.AddReference('dosymep.Bim4Everyone.dll')

clr.AddReference('dosymep.Xpf.Core.dll')
clr.AddReference('dosymep.SimpleServices.dll')

clr.AddReference('Serilog.dll')
clr.AddReference('Serilog.Sinks.File.dll')

from System import Uri, InvalidOperationException, OperationCanceledException
from System.Windows.Media.Imaging import BitmapImage, BitmapCacheOption

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

from os.path import *
from pyrevit import script

from dosymep.SimpleServices import *
from dosymep.Bim4Everyone.SimpleServices import *


def get_ui_theme_service():
    return ServicesProvider.GetPlatformService[IUIThemeService]()


def get_progress_dialog_service():
    return ServicesProvider.GetPlatformService[IProgressDialogService]()


def get_logger_service():
    return ServicesProvider.GetPlatformService[ILoggerService]()


def get_notification_service():
    return ServicesProvider.GetPlatformService[INotificationService]()


def get_platform_command_service():
    return ServicesProvider.GetPlatformService[IPlatformCommandsService]()


def invoke_command(command_id):
    service = get_platform_command_service()
    (command_result, message) = service.InvokeCommand(command_id, None, ElementSet())

    if command_result == Result.Cancelled:
        raise OperationCanceledException()

    if command_result == Result.Failed:
        raise InvalidOperationException(message)


def show_notification_service(title, body, footer="IronPython", author="dosymep", image_source=None):
    notification_service = get_notification_service()
    notification_service.CreateNotification(title, body, footer, author, image_source).ShowAsync()


def show_canceled_script_notification():
    show_script_warning_notification("Выполнение скрипта отменено.")


def show_fatal_script_notification():
    show_script_fatal_notification("Выполнение скрипта завершено с ошибкой.")


def show_executed_script_notification():
    show_script_notification("Выполнение скрипта завершено успешно.")


def get_author():
    if hasattr(script.get_info(), "author"):
        return script.get_info().author


def get_icon_file(file_name):
    if hasattr(script.get_info(), "icon_file"):
        icon_file = script.get_info().icon_file
        if icon_file:
            return join(dirname(icon_file), file_name)


def get_themed_icon_file():
    if get_ui_theme_service().HostTheme == UIThemes.Dark:
        return get_icon_file("icon.dark.png")
    elif get_ui_theme_service().HostTheme == UIThemes.Light:
        return get_icon_file("icon.png")


def get_typed_icon(type_icon):
    if not type_icon:
        return get_themed_icon_file()
    elif type_icon == "fail":
        return get_icon_file("icon.fail.png")
    elif type_icon == "warning":
        return get_icon_file("icon.warning.png")


def get_image_source(type_icon=None):
    icon_file = get_typed_icon(type_icon)
    if not icon_file or not exists(icon_file):
        icon_file = get_themed_icon_file()

    if not icon_file or not exists(icon_file):
        icon_file = get_icon_file("icon.png")

    if icon_file and exists(icon_file):
        image_source = BitmapImage()
        image_source.BeginInit()
        image_source.CacheOption = BitmapCacheOption.OnLoad
        image_source.UriSource = Uri(icon_file)
        image_source.EndInit()
        return image_source


def show_script_notification(body):
    notification_service = get_notification_service()
    notification_service.CreateNotification(script.get_button().ui_title, body, "IronPython",
                                            get_author(), get_image_source()).ShowAsync()


def show_script_fatal_notification(body, exit_script=False):
    notification_service = get_notification_service()
    notification_service.CreateFatalNotification(script.get_button().ui_title, body,
                                                 get_author(), get_image_source("fail")).ShowAsync()

    if exit_script:
        script.exit()


def show_script_warning_notification(body, exit_script=False):
    notification_service = get_notification_service()
    notification_service.CreateWarningNotification(script.get_button().ui_title, body,
                                                   get_author(), get_image_source("warning")).ShowAsync()

    if exit_script:
        script.exit()


def notification():
    def plugin_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                show_executed_script_notification()
            except SystemExit:
                show_canceled_script_notification()
            except System.OperationCanceledException:
                show_canceled_script_notification()
            except Autodesk.Revit.Exceptions.OperationCanceledException:
                show_canceled_script_notification()
            except Exception:
                show_fatal_script_notification()
                raise

        return wrapper

    return plugin_decorator
