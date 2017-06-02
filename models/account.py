# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        help="If flagged, no details will be displayed in "
             "the General Ledger report (the webkit one only), "
             "only centralized amounts per period.")
