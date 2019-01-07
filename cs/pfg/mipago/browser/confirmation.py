# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import MIPAGO_HTML_KEY
from cs.pfg.mipago.config import MIPAGO_PAYMENT_CODE
from cs.pfg.mipago.config import PAYMENT_STATUS_ERROR_IN_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_PAYED
from cs.pfg.mipago.config import PAYMENT_STATUS_SENT_TO_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_USER_IN_MIPAGO
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFPlone.utils import safe_hasattr
from Products.Five.browser import BrowserView
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides

import transaction
import xml.etree.ElementTree as ET


class PaymentConfirmation(BrowserView):
    def get_annotation_context(self):
        parent = aq_parent(self.context)
        if (
            safe_hasattr(parent, "isTranslation")
            and parent.isTranslation()
            and not parent.isCanonical()
        ):
            # look in the canonical version to see if there is
            # a matching (by id) save-data adapter.
            # If so, call its onSuccess method
            cf = parent.getCanonical()
            target = cf.get(self.context.getId())
            if target is not None and target.meta_type == "MiPagoAdapter":
                return target

        return self.context

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        annotation_context = self.get_annotation_context()
        adapted = IAnnotations(annotation_context)
        payment_code = self.extract_payment_code()
        payment_error_message = self.extract_error_message()
        payment_status = self.extract_payment_status()
        payments = adapted.get(ANNOTATION_KEY, {})
        payment_data = payments.get(payment_code, {})
        payment_data["status"] = payment_status
        payments[payment_code] = payment_data
        adapted[ANNOTATION_KEY] = payments
        if payment_status == PAYMENT_STATUS_PAYED:
            self.send_form(payment_code)
        if payment_error_message:
            self.send_failure_form(payment_code, payment_error_message)

        return 1

    def extract_payment_code(self):
        # inspect self.request
        from logging import getLogger

        log = getLogger(__name__)
        log.info("####### extract_payment_code ###########")
        log.info(self.request.items())
        log.info("####### /extract_payment_code ###########")

        param = self.request.get("param1", "")
        return self._parse_param(param)

    def extract_error_message(self):
        param = self.request.get("param1", "")
        return self._parse_error(param)

    def _parse_param(self, param):
        value = unicode(param, "latin1").encode("utf-8")
        root = ET.fromstring(value)
        id_item = root.find(".//id")
        if id_item is not None:
            return id_item.text

        return ""

    def _parse_error(self, param):
        value = unicode(param, "latin1").encode("utf-8")
        root = ET.fromstring(value)
        texto = root.find(".//estado/mensajes/mensaje/texto")

        if texto is not None:
            es = texto.find(".//es")
            if es is not None:
                return es.text.strip()

            eu = texto.find(".//eu")
            if eu is not None:
                return eu.text.strip()

            return "There was an error processing the payment"

        return ""

    def extract_payment_status(self):
        # inspect self.request
        function = self.request.get("function", "")
        if function == "onBeginPayment":
            return PAYMENT_STATUS_USER_IN_MIPAGO
        elif function == "onPayONLineOK":
            return PAYMENT_STATUS_PAYED
        elif function == "onPayONLineNOK":
            return PAYMENT_STATUS_ERROR_IN_MIPAGO

        return ""

    def get_payment_data(self, payment_code=None):
        annotation_context = self.get_annotation_context()
        adapted = IAnnotations(annotation_context)

        if payment_code is not None:
            payments = adapted.get(ANNOTATION_KEY, {})
            return payments.get(payment_code, None)

        return None

    def send_form(self, payment_code):
        data = self.get_payment_data(payment_code)
        form = aq_parent(self.context)
        if data is not None:
            field_data = data.get("fields", [])
            fields = []
            form_data = {}
            for field in field_data:
                form_data[field["id"]] = field["value"]
                fields.append(form.get(field["id"]))

            self.request.form = form_data

            # Mail to form owner
            self.context.send_form(
                fields, self.request, to_addr=self.context.getRecipient_email()
            )

            to_field = self.context.getTo_field()
            if to_field != "#NONE#":
                # Mail to form filler
                self.context.send_form(
                    fields, self.request, to_addr=form_data.get(to_field, "")
                )

    def send_failure_form(self, payment_code, payment_error_message):
        data = self.get_payment_data(payment_code)
        form = aq_parent(self.context)
        if data is not None:
            field_data = data.get("fields", [])
            fields = []
            form_data = {}
            for field in field_data:
                form_data[field["id"]] = field["value"]
                fields.append(form.get(field["id"]))

            self.context.setBody_pre(payment_error_message)
            self.context.setBody_post(payment_error_message)

            transaction.savepoint(1)

            self.request.form = form_data

            # Mail to form owner
            self.context.send_form(
                fields, self.request, to_addr=self.context.getRecipient_email()
            )

            to_field = self.context.getTo_field()
            if to_field != "#NONE#":
                # Mail to form filler
                self.context.send_form(
                    fields, self.request, to_addr=form_data.get(to_field, "")
                )

            self.context.setBody_pre("")
            self.context.setBody_post("")

            transaction.savepoint(1)
