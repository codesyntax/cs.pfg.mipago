# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from cs.pfg.mipago.testing import CS_PFG_MIPAGO_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that cs.pfg.mipago is properly installed."""

    layer = CS_PFG_MIPAGO_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if cs.pfg.mipago is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'cs.pfg.mipago'))

    def test_browserlayer(self):
        """Test that IICS_PFG_MIPAGO is registered."""
        from cs.pfg.mipago.interfaces import (
            ICS_PFG_MIPAGOLayer)
        from plone.browserlayer import utils
        self.assertIn(
            ICS_PFG_MIPAGOLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = CS_PFG_MIPAGO_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['cs.pfg.mipago'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if cs.pfg.mipago is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'cs.pfg.mipago'))

    def test_browserlayer_removed(self):
        """Test that ICS_PFG_MIPAGO is removed."""
        from cs.pfg.mipago.interfaces import \
            ICS_PFG_MIPAGOLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            ICS_PFG_MIPAGOLayer,
            utils.registered_layers())
