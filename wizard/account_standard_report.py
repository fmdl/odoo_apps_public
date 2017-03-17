# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountPartnerLedgerPeriode(models.TransientModel):
    _name = 'account.report.partner.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedger(models.TransientModel):
    _inherit = "account.common.partner.report"
    _name = "account.report.standard.ledger"
    _description = "Account Standard Ledger"

    type_ledger = fields.Selection([('general', 'General Ledger'), ('partner', 'Partner Ledger'), ('journal', 'Journal Ledger'), ('open', 'Open Ledger')], string='Type', default='general', required=True)
    summary = fields.Boolean('Summary', dafault=False)
    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('With Reconciled Entries')
    rem_futur_reconciled = fields.Boolean('With entries matched with other entries dated after End Date.', default=False, help="Reconciled Entries matched with futur is considered like unreconciled. Matching number in futur is replace by *.")
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_methode = fields.Selection([('include', 'Include'), ('exclude', 'Exclude')], string="Methode")
    account_in_ex_clude = fields.Many2many(comodel_name='account.account', string='Accounts', help='If empty, get all accounts')
    with_init_balance = fields.Boolean('With Initial Report at Start Date', default=False)
    sum_group_by_top = fields.Boolean('Sum on Top', default=False)
    sum_group_by_bottom = fields.Boolean('Sum on Bottom', default=True)
    init_balance_history = fields.Boolean('Payable/receivable initial balance with history.', default=False)
    detail_unreconcillied_in_init = fields.Boolean('Detail of un-reconcillied payable/receivable move in initiale balance.', default=True)

    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        today_year = fields.datetime.now().year

        last_day = self.env.user.company_id.fiscalyear_last_day or 31
        last_month = self.env.user.company_id.fiscalyear_last_month or 12
        periode_obj = self.env['account.report.partner.ledger.periode']
        periode_obj.search([]).unlink()
        periode_ids = periode_obj
        for year in range(today_year, today_year - 4, -1):
            date_from = datetime(year - 1, last_month, last_day) + timedelta(days=1)
            date_to = datetime(year, last_month, last_day)
            user_periode = "%s - %s" % (date_from.strftime(date_format),
                                        date_to.strftime(date_format),
                                        )
            vals = {
                'name': user_periode,
                'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT), }
            periode_ids += periode_obj.create(vals)
        return False

    periode_date = fields.Many2one('account.report.partner.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")

    @api.onchange('account_in_ex_clude')
    def on_change_summary(self):
        if self.account_in_ex_clude:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('type_ledger')
    def on_change_type_ledger(self):
        if self.type_ledger != 'partner':
            self.reconciled = True
            self.with_init_balance = True
            return {'domain': {'account_in_ex_clude': []}}
        return {'domain': {'account_in_ex_clude': [('internal_type', 'in', ('receivable', 'payable'))]}}

    @api.onchange('periode_date')
    def on_change_periode_date(self):
        if self.periode_date:
            self.date_from = self.periode_date.date_from
            self.date_to = self.periode_date.date_to

    @api.onchange('date_to')
    def onchange_date_to(self):
        if self.date_to == False:
            self.rem_futur_reconciled = False
        else:
            self.rem_futur_reconciled = True

    @api.multi
    def pre_print_report(self, data):
        data['form'].update({})
        return super(AccountStandardLedger, self).pre_print_report(data)

    # FIXME : find an other solution to pass context instead of rewrite this code
    def _print_report(self, data):
        if self.date_from == False:
            self.with_init_balance = False
        if self.type_ledger != 'partner':
            self.reconciled = True
            self.with_init_balance = True
            self.partner_ids = False
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'rem_futur_reconciled': self.rem_futur_reconciled,
                             'with_init_balance': self.with_init_balance,
                             'amount_currency': self.amount_currency,
                             'sum_group_by_top': self.summary or self.sum_group_by_top,
                             'sum_group_by_bottom': self.sum_group_by_bottom,
                             'type_ledger': self.type_ledger,
                             'summary': self.summary,
                             'partner_ids': self.partner_ids.ids,
                             'account_methode': self.account_methode,
                             'account_in_ex_clude': self.account_in_ex_clude.ids,
                             'init_balance_history': self.init_balance_history,
                             'detail_unreconcillied_in_init': self.detail_unreconcillied_in_init,
                             })
        return self.env['report'].with_context(landscape=True).get_action(self, 'account_standard_report.report_account_standard_report', data=data)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
