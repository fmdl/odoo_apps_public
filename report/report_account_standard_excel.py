# -*- coding: utf-8 -*-

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class AccountStandardExcel(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, report):

        bold = workbook.add_format({'bold': True})
        currency_format = workbook.add_format({'num_format': '_ * #,##0.00_) ;_ * - #,##0.00 ;_ * "-"??_) ;_ @_ '})
        report_format = workbook.add_format({'font_size': 24})

        data = report.pre_print_report()

        sheet = workbook.add_worksheet(data['name_report'])
        sheet.write(0, 4, data['name_report'], report_format)
        sheet.write(2, 0, 'Company:', bold)
        sheet.write(3, 0, data['res_company'],)
        sheet.write(4, 0, 'Print on %s' % data['time'])

        sheet.write(2, 2, 'Start Date : %s ' % data['date_from'] if data['date_from'] else '')
        sheet.write(3, 2, 'End Date : %s ' % data['date_to'] if data['date_to'] else '')

        sheet.write(2, 4, 'Target Moves:', bold)
        sheet.write(3, 4, 'All Entries' if data['target_move'] == 'all' else 'All Posted Entries')

        sheet.write(2, 6, 'Only UnReconciled Entries' if data['reconciled'] == False else 'With Reconciled Entries', bold)
        sheet.write(3, 6, 'With entries matched with other entries dated after End Date.' if data['rem_futur_reconciled'] else '')

        if report.summary:
            all_lines = []
            for group_by in data['group_by_data']['ids']:
                all_lines.append({'code': data['lines_group_by'][group_by]['code'],
                                    'name': data['lines_group_by'][group_by]['name'],
                                    'debit': data['lines_group_by'][group_by]['debit'],
                                    'credit': data['lines_group_by'][group_by]['credit'],
                                    'debit - credit': data['lines_group_by'][group_by]['debit - credit'],
                })
            # Head
            head = [
                {'name': 'Code',
                 'larg': 10,
                 'col': {}},
                {'name': 'Name',
                 'larg': 30,
                 'col': {}},
                {'name': 'Debit',
                 'larg': 15,
                 'col': {'total_function': 'sum', 'format': currency_format}},
                {'name': 'Credit',
                 'larg': 15,
                 'col': {'total_function': 'sum', 'format': currency_format}},
                {'name': 'Balance',
                 'larg': 15,
                 'col': {'total_function': 'sum', 'format': currency_format}},
            ]

            row = 6
            row += 1
            start_row = row
            for i, line in enumerate(all_lines):
                i += row
                sheet.write(i, 0, line.get('code', ''))
                sheet.write(i, 1, line.get('name', ''))
                sheet.write(i, 2, line.get('debit', ''), currency_format)
                sheet.write(i, 3, line.get('credit', ''), currency_format)
                sheet.write(i, 4, line.get('debit - credit', ''), currency_format)
            row = i

            for j, h in enumerate(head):
                sheet.set_column(j, j, h['larg'])

            table = []
            for h in head:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)

            sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                            {'total_row': 1,
                             'columns': table,
                             'style': 'Table Style Light 9',
                             })



        else:
            all_lines = []
            for group_by in data['group_by_data']['ids']:
                for line in data['lines_group_by'][group_by]['new_lines']:
                    if line['type_line'] != 'total':
                        all_lines.append(line)
            # Head
            head = [
                {'name': 'Date',
                 'larg': 10,
                 'col': {}},
                {'name': 'JRNL',
                 'larg': 10,
                 'col': {}},
                {'name': 'Account',
                 'larg': 10,
                 'col': {}},
                {'name': 'Journal entries',
                 'larg': 20,
                 'col': {}},
                {'name': 'Ref',
                 'larg': 40,
                 'col': {}},
                {'name': 'Partner',
                 'larg': 20,
                 'col': {}},
                {'name': 'Due Date',
                 'larg': 10,
                 'col': {}},
                {'name': 'Debit',
                 'larg': 15,
                 'col': {'total_function': 'sum', 'format': currency_format}},
                {'name': 'Credit',
                 'larg': 15,
                 'col': {'total_function': 'sum', 'format': currency_format}},
                {'name': 'Balance',
                 'larg': 15,
                 'col': {'format': currency_format}},
                {'name': 'Currency',
                 'larg': 15,
                 'col': {'format': currency_format}},
                {'name': 'Match.',
                 'larg': 10,
                 'col': {}},
            ]

            row = 6
            row += 1
            start_row = row
            for i, line in enumerate(all_lines):
                i += row
                sheet.write(i, 0, line.get('date', ''))
                sheet.write(i, 1, line.get('code', ''))
                sheet.write(i, 2, line.get('a_code', ''))
                sheet.write(i, 3, line.get('move_name', ''))
                sheet.write(i, 4, line.get('displayed_name', ''))
                sheet.write(i, 5, line.get('partner_name', ''))
                sheet.write(i, 6, line.get('date_maturity', ''))
                sheet.write(i, 7, line.get('debit', ''), currency_format)
                sheet.write(i, 8, line.get('credit', ''), currency_format)
                sheet.write(i, 9, line.get('progress', ''), currency_format)
                sheet.write(i, 10, line.get('amount_currency', ''), currency_format)
                sheet.write(i, 11, line.get('matching_number', ''))
            row = i

            for j, h in enumerate(head):
                sheet.set_column(j, j, h['larg'])

            table = []
            for h in head:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)

            sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                            {'total_row': 1,
                             'columns': table,
                             'style': 'Table Style Light 9',
                             })


AccountStandardExcel('report.account_standard_report.report_account_standard_excel', 'account.report.standard.ledger')
#'account_standard_report.report_account_standard_excel')
