"""Definition of the MiPagoAdapter content type
"""

from zope.interface import implements

from Products.Archetypes import atapi
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata

# -*- Message Factory Imported Here -*-

from cs.pfg.mipago.interfaces import IMiPagoAdapter
from cs.pfg.mipago.config import PROJECTNAME

MiPagoAdapterSchema = schemata.ATContentTypeSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-

))

# Set storage on fields copied from ATContentTypeSchema, making sure
# they work well with the python bridge properties.

MiPagoAdapterSchema['title'].storage = atapi.AnnotationStorage()
MiPagoAdapterSchema['description'].storage = atapi.AnnotationStorage()

schemata.finalizeATCTSchema(MiPagoAdapterSchema, moveDiscussion=False)


class MiPagoAdapter(base.ATCTContent):
    """Adapter for payments with MiPago"""
    implements(IMiPagoAdapter)

    meta_type = "MiPagoAdapter"
    schema = MiPagoAdapterSchema

    title = atapi.ATFieldProperty('title')
    description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-

atapi.registerType(MiPagoAdapter, PROJECTNAME)
