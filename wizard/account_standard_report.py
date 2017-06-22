# -*- coding: utf-8 -*-

import calendar

from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


D_LEDGER = {'general': {'name': _('General Ledger'),
                        'group_by': 'account_id',
                        'model': 'account.account',
                        'short': 'code',
                        },
            'partner': {'name': _('Partner Ledger'),
                        'group_by': 'partner_id',
                        'model': 'res.partner',
                        'short': 'name',
                        },
            'journal': {'name': _('Journal Ledger'),
                        'group_by': 'journal_id',
                        'model': 'account.journal',
                        'short': 'code',
                        },
            'open': {'name': _('Open Ledger'),
                     'group_by': 'account_id',
                     'model': 'account.account',
                     'short': 'code',
                     },
            'aged': {'name': _('Aged Balance'),
                     'group_by': 'partner_id',
                     'model': 'res.partner',
                     'short': 'name',
                     },
            }


class AccountStandardLedgerPeriode(models.TransientModel):
    _name = 'account.report.standard.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedger(models.TransientModel):
    _name = 'account.report.standard.ledger'
    _description = 'Account Standard Ledger'

    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        today_year = fields.datetime.now().year

        last_day = self.env.user.company_id.fiscalyear_last_day or 31
        last_month = self.env.user.company_id.fiscalyear_last_month or 12
        periode_obj = self.env['account.report.standard.ledger.periode']
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

    type_ledger = fields.Selection([('general', 'General Ledger'), ('partner', 'Partner Ledger'), ('journal', 'Journal Ledger'), ('open', 'Open Ledger'), ('aged', 'Aged Balance')], string='Type', default='general', required=True,
                                   help=' * General Ledger : Journal entries group by account\n'
                                   ' * Partner Leger : Journal entries group by partner, with only payable/recevable accounts\n'
                                   ' * Journal Ledger : Journal entries group by journal, without initial balance\n'
                                   ' * Open Ledger : Openning journal at Start date\n')
    summary = fields.Boolean('Trial Balance', default=False,
                             help=' * Check : generate a trial balance.\n'
                             ' * Uncheck : detail report.\n')
    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('With Reconciled Entries', default=True,
                                help='Only for entrie with a payable/receivable account.\n'
                                ' * Check this box to see un-reconcillied and reconciled entries with payable.\n'
                                ' * Uncheck to see only un-reconcillied entries. Can be use only with parnter ledger.\n')
    rem_futur_reconciled = fields.Boolean('With entries matched with other entries dated after End Date.', default=False,
                                          help=' * Check : Reconciled Entries matched with futur is considered like unreconciled. Matching number in futur is replace by *.\n'
                                          ' * Uncheck : Reconciled Entries matched with futur is considered like reconciled. Carfull use if "With Reconciled Entries" is uncheck.\n')
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_methode = fields.Selection([('include', 'Include'), ('exclude', 'Exclude')], string="Methode")
    account_in_ex_clude = fields.Many2many(comodel_name='account.account', string='Accounts', help='If empty, get all accounts')
    with_init_balance = fields.Boolean('With Initial Report at Start Date', default=False,
                                       help='The initial balance is compute with the fiscal date of company.\n'
                                            ' * Check this box to generate the summary of initial balance.\n'
                                            ' * Uncheck to see all entries.\n')
    sum_group_by_top = fields.Boolean('Sum on Top', default=False, help='See the sum of element on top.')
    sum_group_by_bottom = fields.Boolean('Sum on Bottom', default=True, help='See the sum of element on top.')
    init_balance_history = fields.Boolean('Initial balance with history.', default=True,
                                          help=' * Check this box if you need to report all the debit and the credit sum before the Start Date.\n'
                                          ' * Uncheck this box to report only the balance before the Start Date\n')
    detail_unreconcillied_in_init = fields.Boolean('Detail of un-reconcillied payable/receivable entries in initiale balance.', default=True,
                                                   help=' * Check : Add the detail of entries un-reconcillied and with payable/receivable account in the report.\n'
                                                   ' * Unckeck : no detail.\n')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]),
                                   help='Select journal, for the Open Ledger you need to set all journals.')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    periode_date = fields.Many2one('account.report.standard.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")
    month_selec = fields.Selection([(1, '01 Junary'), (2, '02 Febuary'), (3, '03 March'), (4, '04 April'), (5, '05 May'), (6, '06 June'),
                                    (7, '07 Jully'), (8, '08 August'), (9, '09 September'), (10, '10 October'), (11, '11 November'), (12, '12 December')],
                                   string='Month')
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')
    report_name = fields.Char('Report Name')
    compact_account = fields.Boolean('Compacte account.', default=False)
    reset_exp_acc_start_date = fields.Boolean('Reset expenses/revenue account at start date', default=True)

    @api.onchange('account_in_ex_clude')
    def on_change_summary(self):
        if self.account_in_ex_clude:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('type_ledger')
    def on_change_type_ledger(self):
        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.type_ledger == 'aged':
            self.date_from = False
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            self.with_init_balance = True
            return {'domain': {'account_in_ex_clude': []}}
        self.account_in_ex_clude = False
        return {'domain': {'account_in_ex_clude': [('internal_type', 'in', ('receivable', 'payable'))]}}

    @api.onchange('periode_date')
    def on_change_periode_date(self):
        if self.periode_date:
            self.date_from = self.periode_date.date_from
            self.date_to = self.periode_date.date_to
            if self.month_selec:
                self.on_change_month_selec()

    @api.onchange('month_selec')
    def on_change_month_selec(self):
        if self.periode_date and self.month_selec:
            date_from = datetime.strptime(self.periode_date.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            date_from = datetime(date_from.year, self.month_selec, 1)
            date_to = datetime(date_from.year, self.month_selec, calendar.monthrange(date_from.year, self.month_selec)[1])
            self.date_from = date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
            self.date_to = date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.periode_date and not self.month_selec:
            self.on_change_periode_date()

    @api.onchange('date_to')
    def onchange_date_to(self):
        if self.date_to is False:
            self.rem_futur_reconciled = False
        else:
            self.rem_futur_reconciled = True

    def print_pdf_report(self):
        self.ensure_one()
        return self.env['report'].with_context(landscape=True).get_action(self, 'account_standard_report.report_account_standard_report', data={'active_id': self.id})

    def print_excel_report(self):
        self.ensure_one()
        return self.env['report'].get_action(self, 'account_standard_report.report_account_standard_excel')

    def pre_compute_form(self):
        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
            self.reset_exp_acc_start_date = False
        if self.type_ledger == 'aged':
            self.date_from = False
        if self.date_from is False:
            self.with_init_balance = False
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            self.with_init_balance = True
            if self.date_from is False:
                self.with_init_balance = False
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
            'compact_account': self.compact_account,
            'reset_exp_acc_start_date': self.reset_exp_acc_start_date,
            'used_context': {},
        })
        lang_code = self.env.context.get('lang') or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format
        data['lines_group_by'], data['line_account'], data['group_by_data'], data['open_data'] = self._generate_data(data, date_format)

        self._get_name_report()
        data['name_report'] = self.report_name
        data['date_from'] = datetime.strptime(data['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['date_from'] else False
        data['date_to'] = datetime.strptime(data['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['date_to'] else False
        data['res_company'] = self.env.user.company_id.name
        data['time'] = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.now()).strftime(('%s %s') % (date_format, time_format))

        return data

    def do_query_unaffected_earnings(self, date_init_dt):
        ''' Compute the sum of ending balances for all accounts that are of a type that does not bring forward the balance in new fiscal years.
            This is needed because we have to display only one line for the initial balance of all expense/revenue accounts in the FEC.
        '''
        if not date_init_dt:
            return []
        unaffected_earnings_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)], limit=1)
        if not unaffected_earnings_account:
            return []
        company = self.env.user.company_id
        sql_query = """
        SELECT
            COALESCE(SUM(account_move_line.debit), 0) AS debit,
            COALESCE(SUM(account_move_line.credit), 0) AS credit,
            COALESCE(SUM(account_move_line.balance), 0) AS balance,
            COALESCE(SUM(account_move_line.amount_currency), 0) AS amount_currency
        FROM
            account_move AS account_move_line__move_id, account_move_line
            LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
        WHERE
            m.state = %s
            AND account_move_line.date < %s
            AND account_move_line.company_id = %s
            AND account_move_line.move_id=account_move_line__move_id.id
            AND acc_type.include_initial_balance = 'f'
        """

        self.env.cr.execute(sql_query, (self.target_move, date_init_dt, company.id))
        res = self.env.cr.dictfetchall()
        unaffected_earnings_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)], limit=1)

        res = res[0]
        res.update({'account_id': unaffected_earnings_account.id,
                    'a_name': unaffected_earnings_account.name,
                    'a_code': unaffected_earnings_account.code,
                    'a_type':unaffected_earnings_account.user_type_id.id,
                    'reduce_balance': True})
        return res

    def _generate_data(self, data, date_format):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        with_init_balance = self.with_init_balance
        date_from = self.date_from
        date_to = self.date_to
        type_ledger = self.type_ledger
        compact_account = self.compact_account
        reset_exp_acc_start_date = self.reset_exp_acc_start_date
        detail_unreconcillied_in_init = self.detail_unreconcillied_in_init
        date_from_dt = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) if date_from else False
        date_init_dt = self._generate_date_init(date_from_dt)
        accounts = self._search_account()

        reconcile_clause, matching_in_futur, list_match_after_init = self._compute_reconcile_clause(date_init_dt)

        res = self._generate_sql(data, accounts, reconcile_clause, date_to, date_from)
        group_by_obj = self.env[D_LEDGER[type_ledger]['model']]

        lines_group_by = {}
        group_by_ids = []
        group_by_field = D_LEDGER[type_ledger]['group_by']
        line_account = self._generate_account_dict(accounts)

        init_lines_to_compact = []
        compacted_line_to_compact = []
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
                if reset_exp_acc_start_date and not r['include_initial_balance'] and date_from_dt and date_move_dt < date_from_dt:
                    add_in = 'not add'

            r['reduce_balance'] = False
            if add_in == 'init':
                if date_move_dt < date_init_dt:  # r['a_type'] in ('payable', 'receivable') and
                    r['reduce_balance'] = True
                init_lines_to_compact.append(r)
            elif add_in == 'view':
                if compact_account and r['compacted'] and type_ledger == 'general':  # and (r['matching_number_id'] and not r['matching_number_id'] in matching_in_futur
                    compacted_line_to_compact.append(r)
                    append_r = False
                else:
                    if type_ledger == 'aged':
                        r.update(self.get_aged_balance(r, rounding))
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

        init_balance_lines = []
        if type_ledger in ('general'):
            init_lines_to_compact.append(self.do_query_unaffected_earnings(date_init_dt))
        init_balance_lines.extend(self._generate_init_balance_lines(type_ledger, init_lines_to_compact, ))
        compacted_line = self._generate_compacted_lines(type_ledger, compacted_line_to_compact)

        if type_ledger == 'journal':
            all_lines = new_list
        else:
            all_lines = init_balance_lines + new_list + compacted_line

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

            data_aged = {}
            if type_ledger == 'aged':
                data_aged = {'not_due': False, '0-30': False, '30-60': False, '60-90': False, '90-120': False, 'older': False, 'total': False}

            for r in value['new_lines']:
                balance += r['debit'] - r['credit']
                if float_is_zero(balance, precision_rounding=rounding):
                    balance = 0.0
                r['progress'] = balance

                if type_ledger == 'aged':
                    data_aged = self.get_data_aged_sum(data_aged, r, rounding)

                sum_debit += r['debit']
                sum_credit += r['credit']
                open_debit += r['debit']
                open_credit += r['credit']

                r['s_debit'] = False if float_is_zero(r['debit'], precision_rounding=rounding) else True
                r['s_credit'] = False if float_is_zero(r['credit'], precision_rounding=rounding) else True

                line_account[r['account_id']]['debit'] += r['debit']
                line_account[r['account_id']]['credit'] += r['credit']
                line_account[r['account_id']]['active'] = True
                line_account[r['account_id']]['balance'] += r['debit'] - r['credit']

            balance = sum_debit - sum_credit
            if float_is_zero(balance, precision_rounding=rounding):
                balance = 0.0
            if data['sum_group_by_bottom']:
                lines_group_by[group_by]['new_lines'].append(self._generate_total(sum_debit, sum_credit, balance, data_aged))

            lines_group_by[group_by]['s_debit'] = False if float_is_zero(sum_debit, precision_rounding=rounding) else True
            lines_group_by[group_by]['s_credit'] = False if float_is_zero(sum_credit, precision_rounding=rounding) else True
            lines_group_by[group_by]['debit - credit'] = balance
            lines_group_by[group_by]['debit'] = sum_debit
            lines_group_by[group_by]['credit'] = sum_credit
            lines_group_by[group_by]['code'], lines_group_by[group_by]['name'], lines_group_by[group_by]['displayed_name'] = self._get_sum_name(group_by_obj.browse(group_by))

            lines_group_by[group_by].update(data_aged)

            group_by_ids.append(group_by)

        # remove unused account
        for key, value in line_account.items():
            if value['active'] is False:
                del line_account[key]

        # compute open balance
        open_balance = open_debit - open_credit
        if float_is_zero(open_balance, precision_rounding=rounding):
            open_balance = 0.0

        open_data = {'debit': open_debit,
                     'credit': open_credit,
                     'balance': open_balance, }

        group_by_ids = group_by_obj.browse(group_by_ids)
        group_by_ids = sorted(group_by_ids, key=lambda x: x[D_LEDGER[type_ledger]['short']])
        group_by_ids = {'model': D_LEDGER[type_ledger]['model'],
                        'ids': [x.id for x in group_by_ids]}

        return lines_group_by, line_account, group_by_ids, open_data

    def get_data_aged_sum(self, data_aged, r, rounding):
        total = 0.0
        for value in ['not_due', '0-30', '30-60', '60-90', '90-120', 'older', 'total']:
            if data_aged[value]:
                data_aged[value] += r[value]
            else:
                data_aged[value] = r[value]
        if float_is_zero(data_aged['total'], precision_rounding=rounding):
            data_aged['total'] = False
        return data_aged

    def get_aged_balance(self, r, rounding):
        date_maturity = datetime.strptime(r['date_maturity'], DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        data_aged = {'not_due': False, '0-30': False, '30-60': False, '60-90': False, '90-120': False, 'older': False, 'total': False}
        balance = r['debit'] - r['credit']
        if float_is_zero(balance, precision_rounding=rounding):
            balance = 0.0
        else:
            data_aged['total'] = balance
        if date_maturity < (date_to - timedelta(days=120)):
            data_aged['older'] = balance
        elif date_maturity < (date_to - timedelta(days=90)):
            data_aged['90-120'] = balance
        elif date_maturity < (date_to - timedelta(days=60)):
            data_aged['60-90'] = balance
        elif date_maturity < (date_to - timedelta(days=30)):
            data_aged['30-60'] = balance
        elif date_maturity < (date_to):
            data_aged['0-30'] = balance
        else:
            data_aged['not_due'] = balance
        return data_aged

    def _get_sum_name(self, group_by):
        name = ''
        code = ''
        display_name = ''
        if self.type_ledger in ('general', 'journal', 'open'):
            display_name = "%s - %s" % (group_by.code, group_by.name)
            code = group_by.code
            name = group_by.name
        elif self.type_ledger in ('partner', 'aged',):
            if group_by.ref:
                display_name = '%s - %s' % (group_by.ref, group_by.name)
                code = group_by.ref
                name = group_by.name
            else:
                display_name = group_by.name
                code = group_by.name
                name = ''
        return code, name, display_name

    def _generate_sql(self, data, accounts, reconcile_clause_data, date_to, date_from):
        params = [self.target_move, self.env.user.company_id.id, tuple(accounts.ids), tuple(self.journal_ids.ids)]

        date_clause = ''
        if date_to:
            date_clause += ' AND account_move_line.date <= %s '
            params.append(date_to)
        if date_from and self.type_ledger == 'journal':
            date_clause += ' AND account_move_line.date >= %s '
            params.append(date_from)

        partner_clause = ''
        if self.partner_ids:
            partner_clause = 'AND account_move_line.partner_id IN %s'
            params.append(tuple(self.partner_ids.ids))
        elif self.type_ledger in ('partner', 'aged',):
            partner_clause = ' AND account_move_line.partner_id IS NOT NULL '

        reconcile_clause = ''
        if reconcile_clause_data:
            reconcile_clause = reconcile_clause_data['query']
            if reconcile_clause_data['params']:
                params.append(reconcile_clause_data['params'])

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
                acc.compacted AS compacted,
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
            FROM
                account_move AS account_move_line__move_id, account_move_line
                LEFT JOIN account_journal j ON (account_move_line.journal_id = j.id)
                LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
                LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
                LEFT JOIN res_currency c ON (account_move_line.currency_id = c.id)
                LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
                LEFT JOIN account_full_reconcile afr ON (account_move_line.full_reconcile_id = afr.id)
                LEFT JOIN res_partner prt ON (account_move_line.partner_id = prt.id)
            WHERE
                m.state = %s
                AND account_move_line.company_id = %s
                AND account_move_line.move_id=account_move_line__move_id.id
                AND account_move_line.account_id IN %s
                AND account_move_line.journal_id IN %s""" + date_clause + partner_clause + reconcile_clause + """
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

    def _generate_init_balance_lines(self, type_ledger, init_lines_to_compact):
        group_by_field = D_LEDGER[type_ledger]['group_by']
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        init_lines = {}

        for r in init_lines_to_compact:
            key = (r['account_id'], r[group_by_field])
            reduce_balance = r['reduce_balance'] and not self.init_balance_history
            if key in init_lines.keys():
                init_lines[key]['debit'] += r['debit']
                init_lines[key]['credit'] += r['credit']
            else:
                init_lines[key] = {'debit': r['debit'],
                                   'credit': r['credit'],
                                   'reduce_balance': reduce_balance,
                                   'account_id': r['account_id'],
                                   group_by_field: r[group_by_field],
                                   'a_code': r['a_code'],
                                   'a_name': r['a_name'],
                                   'a_type': r['a_type'], }
        init = []
        for key, value in init_lines.items():
            init_debit = value['debit']
            init_credit = value['credit']
            balance = init_debit - init_credit
            balance = 0.0 if float_is_zero(balance, precision_rounding=rounding) else balance

            if value['reduce_balance']:
                if balance > 0:
                    init_debit = abs(balance)
                    init_credit = 0
                elif balance < 0:
                    init_credit = abs(balance)
                    init_debit = 0
                elif balance == 0:
                    init_debit = 0
                    init_credit = 0

            if not float_is_zero(init_debit, precision_rounding=rounding) or not float_is_zero(init_credit, precision_rounding=rounding):
                init.append({'date': 'Initial balance',
                             'date_maturity': '',
                             'debit': init_debit,
                             'credit': init_credit,
                             'code': 'INIT',
                             'a_code': value['a_code'],
                             'a_name': value['a_name'],
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

    def _generate_compacted_lines(self, type_ledger, compacted_line_to_compact):
        group_by_field = D_LEDGER[type_ledger]['group_by']
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        compacted_lines = {}
        for r in compacted_line_to_compact:
            key = r['account_id']
            if key in compacted_lines.keys():
                compacted_lines[key]['debit'] += r['debit']
                compacted_lines[key]['credit'] += r['credit']
            else:
                compacted_lines[key] = {'debit': r['debit'],
                                        'credit': r['credit'],
                                        'account_id': r['account_id'],
                                        group_by_field: r[group_by_field],
                                        'a_code': r['a_code'],
                                        'a_name': r['a_name'],
                                        'a_type': r['a_type'], }
        centra = []
        for key, value in compacted_lines.items():
            init_debit = value['debit']
            init_credit = value['credit']
            balance = init_debit - init_credit
            if float_is_zero(balance, precision_rounding=rounding):
                balance = 0.0

            if not float_is_zero(init_debit, precision_rounding=rounding) or not float_is_zero(init_credit, precision_rounding=rounding):
                centra.append({'date': _('Compacted'),
                               'date_maturity': '',
                               'debit': init_debit,
                               'credit': init_credit,
                               'code': _('COMP'),
                               'a_code': value['a_code'],
                               'a_name': value['a_name'],
                               'move_name': '',
                               'account_id': value['account_id'],
                               group_by_field: value[group_by_field],
                               'displayed_name': '',
                               'partner_name': '',
                               'progress': balance,
                               'amount_currency': 0.0,
                               'matching_number': '',
                               'type_line': 'normal'})
        return centra

    def _generate_total(self, sum_debit, sum_credit, balance, data_aged):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        data = {'date': _('Total'),
                'date_maturity': '',
                'debit': sum_debit,
                'credit': sum_credit,
                's_debit': False if float_is_zero(sum_debit, precision_rounding=rounding) else True,
                's_credit': False if float_is_zero(sum_credit, precision_rounding=rounding) else True,
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
        data.update(data_aged)
        return data

    def _search_account(self):
        type_ledger = self.type_ledger
        domain = [('deprecated', '=', False), ]
        if type_ledger in ('partner', 'aged',):
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
        reconcile_clause = {}
        list_match_in_futur = []
        list_match_after_init = []

        if not self.reconciled:
            reconcile_clause = {'query': ' AND account_move_line.reconciled = false ', 'params': False, }

        # when an entrie a matching number and this matching number is linked with
        # entries witch the date is gretter than date_to, then
        # the entrie is considered like unreconciled.
        if self.rem_futur_reconciled and self.date_to:
            date_to = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)

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
                for r in sql_query([date_init - timedelta(days=1)]):
                    list_match_after_init.append(r['id'])

            if list_match_in_futur and not self.reconciled:
                reconcile_clause = {'query': ' AND (account_move_line.full_reconcile_id IS NULL OR account_move_line.full_reconcile_id IN %s ) ',
                                    'params': tuple(list_match_in_futur), }

        return reconcile_clause, list_match_in_futur, list_match_after_init

    def _get_name_report(self):
        report_name = D_LEDGER[self.type_ledger]['name']
        if self.summary:
            report_name += _(' Balance')
        self.report_name = report_name

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
