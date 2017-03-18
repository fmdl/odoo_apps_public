# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from odoo import api, models, fields, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountStandardReport(models.AbstractModel):
    _name = 'report.account_standard_report.report_account_standard_report'

    @api.multi
    def render_html(self, docis, data):
        group_by_ids = []
        for record in data['group_by_data']['ids']:
            group_by_ids.append(self.env[data['group_by_data']['model']].browse(record))
        docargs = {
            'group_by_top': self._group_by_top,
            'data': data,
            'docs': group_by_ids,
            'time': time,
            'lines': self._lines,
            'sum_group_by': self._sum_group_by,
            'accounts': self._account,
        }
        return self.env['report'].render('account_standard_report.report_account_standard_report', docargs)

    def _account(self, data):
        return data['line_account'].values()

    def _lines(self, data, group_by):
        return data['lines_group_by'][str(group_by.id)]['new_lines']

    def _sum_group_by(self, data, group_by, field):
        return data['lines_group_by'][str(group_by.id)][field]

    def _group_by_top(self, data, group_by, field):
        type_ledger = data['type_ledger']
        if type_ledger in ('general', 'journal', 'open'):
            code = group_by.code
            name = group_by.name
        elif type_ledger == 'partner':
            if group_by.ref:
                code = group_by.ref
                name = group_by.name
            else:
                code = group_by.name
                name = ''
        if field == 'code':
            return code or ''
        if field == 'name':
            return name or ''
        return
