# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface
from .mipagoadapter import IMiPagoAdapter

class ICS_PFG_MIPAGOLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


# -*- extra stuff goes here -*-
