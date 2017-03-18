# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from odoo import api, models, fields, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from cStringIO import StringIO
try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')

D_LEDGER = {'general': {'name': 'General Ledger',
                        'group_by': 'account_id',
                        'model': 'account.account',
                        'short': 'code',
                        },
            'partner': {'name': 'Partner Ledger',
                        'group_by': 'partner_id',
                        'model': 'res.partner',
                        'short': 'name',
                        },
            'journal': {'name': 'Journal Ledger',
                        'group_by': 'journal_id',
                        'model': 'account.journal',
                        'short': 'code',
                        },
            'open': {'name': 'Open Ledger',
                     'group_by': 'account_id',
                     'model': 'account.account',
                     'short': 'code',
                     },
            }


class AccountPartnerLedgerPeriode(models.TransientModel):
    _name = 'account.report.partner.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedger(models.TransientModel):
    #_inherit = "account.common.partner.report"
    _name = 'account.report.standard.ledger'
    _description = 'Account Standard Ledger'

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
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')
    periode_date = fields.Many2one('account.report.partner.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')

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

    def print_pdf_report(self):
        data = self.pre_print_report()
        return self.env['report'].with_context(landscape=True).get_action(self, 'account_standard_report.report_account_standard_report', data=data)

    def print_excel_report(self):
        return self.env['report'].get_action(self, 'account_standard_report.report_account_standard_excel') #

    def pre_compute_form(self):
        if self.date_from == False:
            self.with_init_balance = False
        if self.type_ledger != 'partner':
            self.reconciled = True
            self.with_init_balance = True
            self.partner_ids = False

    def pre_print_report(self):
        self.pre_compute_form()
        data = {}
        data.update({
            'reconciled': self.reconciled,
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
            'journal_ids': self.journal_ids.ids,
            'result_selection': self.result_selection,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'target_move': self.target_move,
            'used_context': {},
        })
        lang_code = self.env.context.get('lang') or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format
        data['lines_group_by'], data['line_account'], data['group_by_data'], data['open_data'] = self._generate_data(data, date_format)

        data['name_report'] = self._get_name_report()
        data['date_from'] = datetime.strptime(data['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['date_from'] else False
        data['date_to'] = datetime.strptime(data['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['date_to'] else False
        data['res_company'] = self.env.user.company_id.name
        data['time'] = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.now()).strftime(('%s %s') %(date_format, time_format))

        return data

    def _generate_data(self, data, date_format):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        with_init_balance = self.with_init_balance
        init_balance_history = self.init_balance_history
        summary = self.summary
        date_from = self.date_from
        date_to = self.date_to
        type_ledger = self.type_ledger
        detail_unreconcillied_in_init = self.detail_unreconcillied_in_init
        date_from_dt = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) if date_from else False
        date_to_dt = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT) if date_to else False
        date_init_dt = self._generate_date_init(date_from_dt)
        date_init = date_init_dt.strftime(DEFAULT_SERVER_DATE_FORMAT) if date_init_dt else False
        accounts = self._search_account()

        reconcile_clause, matching_in_futur, list_match_after_init = self._compute_reconcile_clause(date_init_dt)

        res = self._generate_sql(data, accounts, reconcile_clause, date_to, date_from)

        lines_group_by = {}
        group_by_ids = []
        group_by_field = D_LEDGER[type_ledger]['group_by']
        line_account = self._generate_account_dict(accounts)

        init_lines_to_compact = []
        new_list = []
        for r in res:
            date_move_dt = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT)

            # Cas 1 : avant la date d'ouverture et, 401 non lettré avant la date d'ouverture
            #       si compte avec balance initiale
            #       -> pour calcul d'init
            #       sinon
            #       -> perdu
            # Cas 2 : entre la date d'ouverture et date_from, et 401 non lettré avant dat_to
            #       -> pour calcul d'init
            # Cas 3 : après la date_from
            #       -> pour affichage

            add_in = 'view'
            if with_init_balance:
                if r['a_type'] in ('payable', 'receivable') and detail_unreconcillied_in_init:
                    if not r['matching_number_id']:
                        matched_in_future = False
                        matched_after_init = False
                    else:
                        matched_after_init = True
                        matched_in_future = True
                        if r['matching_number_id'] in matching_in_futur:
                            matched_in_future = False
                        if r['matching_number_id'] in list_match_after_init:
                            matched_after_init = False
                else:
                    matched_after_init = True
                    matched_in_future = True

                if date_move_dt < date_init_dt and matched_after_init:
                    if r['include_initial_balance']:
                        add_in = 'init'
                    else:
                        add_in = 'not add'
                elif date_move_dt >= date_init_dt and date_from_dt and date_move_dt < date_from_dt and matched_in_future:
                    add_in = 'init'
                else:
                    add_in = 'view'

            r['reduce_balance'] = False
            if add_in == 'init':
                init_lines_to_compact.append(r)
                if r['a_type'] in ('payable', 'receivable') and date_move_dt < date_init_dt:
                    r['reduce_balance'] = True
            elif add_in == 'view':
                date_move = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT)
                r['date'] = date_move.strftime(date_format)
                r['date_maturity'] = datetime.strptime(r['date_maturity'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
                r['displayed_name'] = '-'.join(
                    r[field_name] for field_name in ('ref', 'name')
                    if r[field_name] not in (None, '', '/')
                )
                # if move is matching with the future then replace matching number par *
                if r['matching_number_id'] in matching_in_futur:
                    r['matching_number'] = '*'

                r['type_line'] = 'normal'
                append_r = True if not type_ledger == 'open' else False
                if date_from_dt and date_move_dt < date_from_dt:
                    r['type_line'] = 'init'
                    r['code'] = 'INIT'
                    append_r = True

                if append_r:
                    new_list.append(r)

        init_balance_lines = self._generate_init_balance_lines(type_ledger, init_lines_to_compact, init_balance_history)

        if type_ledger == 'journal':
            all_lines = new_list
        else:
            all_lines = init_balance_lines + new_list

        for r in all_lines:
            if r[group_by_field] in lines_group_by.keys():
                lines_group_by[r[group_by_field]]['new_lines'].append(r)
            else:
                lines_group_by[r[group_by_field]] = {'new_lines': [r], }

        # remove unused group_by
        for group_by, value in lines_group_by.items():
            if not value['new_lines']:
                del lines_group_by[group_by]

        open_debit = 0
        open_credit = 0
        # compute sum by group_by
        # compute sum by account
        for group_by, value in lines_group_by.items():
            balance = 0.0
            sum_debit = 0.0
            sum_credit = 0.0
            for r in value['new_lines']:
                balance += r['debit'] - r['credit']
                r['progress'] = balance
                if float_is_zero(balance, rounding):
                    r['progress'] = 0.0

                sum_debit += r['debit']
                sum_credit += r['credit']
                open_debit += r['debit']
                open_credit += r['credit']

                r['s_debit'] = False if float_is_zero(r['debit'], rounding) else True
                r['s_credit'] = False if float_is_zero(r['credit'], rounding) else True

                line_account[r['account_id']]['debit'] += r['debit']
                line_account[r['account_id']]['credit'] += r['credit']
                line_account[r['account_id']]['active'] = True
                line_account[r['account_id']]['balance'] += r['debit'] - r['credit']

            balance = sum_debit - sum_credit
            if float_is_zero(balance, rounding):
                balance = 0.0

            if data['sum_group_by_bottom']:
                lines_group_by[group_by]['new_lines'].append(self._generate_total(sum_debit, sum_credit, balance))

            lines_group_by[group_by]['s_debit'] = False if float_is_zero(sum_debit, rounding) else True
            lines_group_by[group_by]['s_credit'] = False if float_is_zero(sum_credit, rounding) else True
            lines_group_by[group_by]['debit - credit'] = balance
            lines_group_by[group_by]['debit'] = sum_debit
            lines_group_by[group_by]['credit'] = sum_credit

            group_by_ids.append(group_by)

        # remove unused account
        for key, value in line_account.items():
            if value['active'] == False:
                del line_account[key]

        open_balance = open_debit - open_credit
        if float_is_zero(open_balance, rounding):
            open_balance = 0.0

        open_data = {'debit': open_debit,
                     'credit': open_credit,
                     'balance': open_balance, }

        group_by_ids = self.env[D_LEDGER[type_ledger]['model']].browse(group_by_ids)
        group_by_ids = sorted(group_by_ids, key=lambda x: x[D_LEDGER[type_ledger]['short']])
        group_by_ids = {'model': D_LEDGER[type_ledger]['model'],
                        'ids': [x.id for x in group_by_ids]}

        return lines_group_by, line_account, group_by_ids, open_data


    def _generate_sql(self, data, accounts, reconcile_clause, date_to, date_from):
        date_clause = ''
        if date_to:
            date_clause += ' AND account_move_line.date <= ' + "'" + str(date_to) + "'" + ' '
        if date_from and self.type_ledger == 'journal':
            date_clause += ' AND account_move_line.date >= ' + "'" + str(date_from) + "'" + ' '

        context = {'journal_ids': self.journal_ids.ids,
                   'state': self.target_move, }
        query_get_data = self.env['account.move.line'].with_context(context)._query_get()
        reconcile_clause = reconcile_clause
        move_state = ['posted'] if self.target_move == 'posted' else ['draft', 'posted']
        params = [tuple(['posted']), tuple(accounts.ids)] + query_get_data[2]

        partner_clause = ''
        if self.partner_ids:
            partner_ids = self.partner_ids.ids
            if len(partner_ids) == 1:
                partner_ids = "(%s)" % (partner_ids[0])
            else:
                partner_ids = tuple(partner_ids)
            partner_clause = ' AND account_move_line.partner_id IN ' + str(partner_ids) + ' '
        elif self.type_ledger == 'partner':
            partner_clause = ' AND account_move_line.partner_id IS NOT NULL '

        query = """
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                j.code,
                acc.code AS a_code,
                acc.name AS a_name,
                acc_type.type AS a_type,
                acc_type.include_initial_balance AS include_initial_balance,
                account_move_line.ref,
                m.name AS move_name,
                account_move_line.name,
                account_move_line.debit,
                account_move_line.credit,
                account_move_line.amount_currency,
                account_move_line.currency_id,
                c.symbol AS currency_code,
                afr.name AS matching_number,
                afr.id AS matching_number_id,
                account_move_line.partner_id,
                account_move_line.account_id,
                account_move_line.journal_id,
                prt.name AS partner_name
            FROM """ + query_get_data[0] + """
                LEFT JOIN account_journal j ON (account_move_line.journal_id = j.id)
                LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
                LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
                LEFT JOIN res_currency c ON (account_move_line.currency_id = c.id)
                LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
                LEFT JOIN account_full_reconcile afr ON (account_move_line.full_reconcile_id = afr.id)
                LEFT JOIN res_partner prt ON (account_move_line.partner_id = prt.id)
            WHERE
                m.state IN %s
                AND account_move_line.account_id IN %s AND """ + query_get_data[1] + reconcile_clause + partner_clause + date_clause + """
                ORDER BY account_move_line.date, move_name, a_code, account_move_line.ref"""
        self.env.cr.execute(query, tuple(params))
        return self.env.cr.dictfetchall()

    def _generate_account_dict(self, accounts):
        line_account = {}
        for account in accounts:
            line_account[account.id] = {
                'debit': 0.0,
                'credit': 0.0,
                'balance': 0.0,
                'code': account.code,
                'name': account.name,
                'active': False,
            }
        return line_account

    def _generate_init_balance_lines(self, type_ledger, init_lines_to_compact, init_balance_history):
        group_by_field = D_LEDGER[type_ledger]['group_by']
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        init_lines = {}
        for r in init_lines_to_compact:
            key = (r['account_id'], r[group_by_field])
            reduce_balance = r['reduce_balance'] and not init_balance_history
            if key in init_lines.keys():
                if reduce_balance:
                    init_lines[key]['re_debit'] += r['debit']
                    init_lines[key]['re_credit'] += r['credit']
                else:
                    init_lines[key]['debit'] += r['debit']
                    init_lines[key]['credit'] += r['credit']
            else:
                init_lines[key] = {'debit': r['debit'] if not reduce_balance else 0,
                                   'credit': r['credit'] if not reduce_balance else 0,
                                   're_debit': r['debit'] if reduce_balance else 0,
                                   're_credit': r['credit'] if reduce_balance else 0,
                                   'account_id': r['account_id'],
                                   group_by_field: r[group_by_field],
                                   'a_code': r['a_code'],
                                   'a_type': r['a_type'], }
        init = []
        for key, value in init_lines.items():
            init_debit = value['debit']
            init_credit = value['credit']
            balance = init_debit - init_credit
            re_balance = value['re_debit'] - value['re_credit']
            if float_is_zero(balance, rounding):
                balance = 0.0
            if re_balance > 0:
                init_debit += abs(re_balance)
            elif re_balance < 0:
                init_credit += abs(re_balance)

            if not float_is_zero(init_debit, rounding) or not float_is_zero(init_credit, rounding):
                init.append({'date': 'Initial balance',
                             'date_maturity': '',
                             'debit': init_debit,
                             'credit': init_credit,
                             'code': 'INIT',
                             'a_code': value['a_code'],
                             'move_name': '',
                             'account_id': value['account_id'],
                             group_by_field: value[group_by_field],
                             'displayed_name': '',
                             'partner_name': '',
                             'progress': balance,
                             'amount_currency': 0.0,
                             'matching_number': '',
                             'type_line': 'init'})
        return init

    def _generate_total(self, sum_debit, sum_credit, balance):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        return {'date': 'Total',
                'date_maturity': '',
                'debit': sum_debit,
                'credit': sum_credit,
                's_debit': False if float_is_zero(sum_debit, rounding) else True,
                's_credit': False if float_is_zero(sum_credit, rounding) else True,
                'code': '',
                'move_name': '',
                'a_code': '',
                'account_id': '',
                'displayed_name': '',
                'partner_name': '',
                'progress': balance,
                'amount_currency': 0.0,
                'matching_number': '',
                'type_line': 'total', }

    def _search_account(self):
        type_ledger = self.type_ledger
        domain = [('deprecated', '=', False), ]
        if type_ledger == 'partner':
            result_selection = self.result_selection
            if result_selection == 'supplier':
                acc_type = ['payable']
            elif result_selection == 'customer':
                acc_type = ['receivable']
            else:
                acc_type = ['payable', 'receivable']
            domain.append(('internal_type', 'in', acc_type))

        account_in_ex_clude = self.account_in_ex_clude.ids
        acc_methode = self.account_methode
        if account_in_ex_clude:
            if acc_methode == 'include':
                domain.append(('id', 'in', account_in_ex_clude))
            elif acc_methode == 'exclude':
                domain.append(('id', 'not in', account_in_ex_clude))
        return self.env['account.account'].search(domain)

    def _compute_reconcile_clause(self, date_init):
        reconcile_clause = ""
        list_match_in_futur = []
        list_match_after_init = []

        if not self.reconciled:
            reconcile_clause = ' AND account_move_line.reconciled = false '

        # when an entrie a matching number and this matching number is linked with
        # entries witch the date is gretter than date_to, then
        # the entrie is considered like unreconciled.
        if self.rem_futur_reconciled and self.date_to:
            date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
            acc_ful_obj = self.env['account.full.reconcile']

            def sql_query(params):
                query = """
                SELECT DISTINCT afr.id
                FROM account_full_reconcile afr
                INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
                AND aml.date > %s
                """
                self.env.cr.execute(query, params)
                return self.env.cr.dictfetchall()

            for r in sql_query([date_to]):
                list_match_in_futur.append(r['id'])
            if date_init:
                for r in sql_query([date_init]):
                    list_match_after_init.append(r['id'])

            if list_match_in_futur and not self.reconciled:
                if len(list_match_in_futur) == 1:
                    list_match_in_futur_sql = "(%s)" % (list_match_in_futur[0])
                else:
                    list_match_in_futur_sql = str(tuple(list_match_in_futur))
                reconcile_clause = ' AND (account_move_line.full_reconcile_id IS NULL OR account_move_line.full_reconcile_id IN ' + list_match_in_futur_sql + ')'

        return reconcile_clause, list_match_in_futur, list_match_after_init

    def _get_name_report(self):
        name = D_LEDGER[self.type_ledger]['name']
        if self.summary:
            name += ' Summary'
        return name

    def _generate_date_init(self, date_from_dt):
        if date_from_dt:
            last_day = self.env.user.company_id.fiscalyear_last_day or 31
            last_month = self.env.user.company_id.fiscalyear_last_month or 12
            if date_from_dt.month >= last_month and date_from_dt.day >= last_day:
                year = date_from_dt.year
            else:
                year = date_from_dt.year - 1
            return datetime(year=year, month=last_month, day=last_day) + timedelta(days=1)
        return False
