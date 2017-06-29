# -*- coding: utf-8 -*-

import logging
from odoo import SUPERUSER_ID
logger = logging.getLogger('MIG compacted')
from odoo import api


def migrate(cr, v):
    with api.Environment.manage():
        uid = SUPERUSER_ID
        ctx = api.Environment(cr, uid, {})['res.users'].context_get()
        env = api.Environment(cr, uid, ctx)

        cr.execute("""UPDATE account_account SET compacted = FALSE WHERE compacted IS NULL;""")
