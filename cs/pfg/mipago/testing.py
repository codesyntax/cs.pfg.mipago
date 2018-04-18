# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from plone.app.testing import PloneWithPackageLayer
import cs.pfg.mipago


class CS_PFG_MIPAGO(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import Products.Five
        import Products.PloneFormGen
        import plone.app.layout
        self.loadZCML(package=Products.Five)
        self.loadZCML(package=Products.PloneFormGen)
        self.loadZCML(package=cs.pfg.mipago)
        self.loadZCML(package=plone.app.layout)

        z2.installProduct(app, 'cs.pfg.mipago')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'cs.pfg.mipago:default')


CS_PFG_MIPAGO_FIXTURE = CS_PFG_MIPAGO()


CS_PFG_MIPAGO_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CS_PFG_MIPAGO_FIXTURE,),
    name='CS_PFG_MIPAGO:IntegrationTesting',
)


CS_PFG_MIPAGO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CS_PFG_MIPAGO_FIXTURE,),
    name='CS_PFG_MIPAGO:FunctionalTesting',
)


CS_PFG_MIPAGO_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        CS_PFG_MIPAGO_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='CS_PFG_MIPAGO:AcceptanceTesting',
)
