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
        group_by_obj = self.env[data['group_by_data']['model']]
        for record in data['group_by_data']['ids']:
            group_by_ids.append(group_by_obj.browse(record))
        docargs = {
            #'group_by_top': self._group_by_top,
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
