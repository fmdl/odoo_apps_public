# -*- coding: utf-8 -*-

import time
from odoo import api, models


class AccountStandardReport(models.AbstractModel):
    _name = 'report.account_standard_report.report_account_standard_report'

    @api.multi
    def render_html(self, docis, data):
        report = self.env['account.report.standard.ledger'].browse(data['active_id'])
        data = report.pre_print_report()
        group_by_ids = []
        group_by_obj = self.env[data['group_by_data']['model']]
        for record in data['group_by_data']['ids']:
            group_by_ids.append(group_by_obj.browse(record))
        docargs = {
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
        return data['lines_group_by'][group_by.id]['new_lines']

    def _sum_group_by(self, data, group_by, field):
        return data['lines_group_by'][group_by.id][field]
