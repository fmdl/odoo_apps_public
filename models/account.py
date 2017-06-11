# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    compacted = fields.Boolean('Compacte reconciled entries.', help='If flagged, no details will be displayed in the Standard report, only compacted amounts per period.')
