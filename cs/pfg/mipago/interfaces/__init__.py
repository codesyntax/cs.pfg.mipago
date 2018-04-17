# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface


class ICS_PFG_MIPAGO(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

class IMiPagoAdapter(Interface):
    pass

# -*- extra stuff goes here -*-
