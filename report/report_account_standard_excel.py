# -*- coding: utf-8 -*-

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import _


class AccountStandardExcel(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, report):

        num_format = _('_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ')
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': _(num_format)})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': _(num_format)})
        report_format = workbook.add_format({'font_size': 24})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2

        def _header_sheet(sheet):
            sheet.write(0, 4, data['name_report'], report_format)
            sheet.write(2, 0, _('Company:'), bold)
            sheet.write(3, 0, data['res_company'],)
            sheet.write(4, 0, _('Print on %s') % data['time'])

            sheet.write(2, 2, _('Start Date : %s ') % data['date_from'] if data['date_from'] else '')
            sheet.write(3, 2, _('End Date : %s ') % data['date_to'] if data['date_to'] else '')

            sheet.write(2, 4, _('Target Moves:'), bold)
            sheet.write(3, 4, _('All Entries') if data['target_move'] == 'all' else _('All Posted Entries'))

            sheet.write(2, 6, _('Only UnReconciled Entries') if data['reconciled'] is False else _('With Reconciled Entries'), bold)
            sheet.write(3, 6, _('With entries matched with other entries dated after End Date.') if data['rem_futur_reconciled'] else '')

        data = report.pre_print_report()

        if report.type_ledger == 'aged':

            if report.summary:
                sheet = workbook.add_worksheet(data['name_report'])
                _header_sheet(sheet)

                head = [
                    {'name': 'Code',
                     'larg': 10,
                     'col': {}},
                    {'name': 'Name',
                     'larg': 30,
                     'col': {}},
                    {'name': _('Not Due'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('0-30'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('30-60'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('60-90'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('90-120'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Older'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Total'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                ]

                all_lines = []
                for group_by in data['group_by_data']['ids']:
                    all_lines.append(data['lines_group_by'][group_by])
                if all_lines:

                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        sheet.write(i, 0, line.get('code', ''))
                        sheet.write(i, 1, line.get('name', ''))
                        sheet.write(i, 2, round(line.get('not_due', ''), rounding), currency_format)
                        sheet.write(i, 3, round(line.get('0-30', ''), rounding), currency_format)
                        sheet.write(i, 4, round(line.get('30-60', ''), rounding), currency_format)
                        sheet.write(i, 5, round(line.get('60-90', ''), rounding), currency_format)
                        sheet.write(i, 6, round(line.get('90-120', ''), rounding), currency_format)
                        sheet.write(i, 7, round(line.get('older', ''), rounding), currency_format)
                        sheet.write(i, 8, round(line.get('total', ''), rounding), currency_format)
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

            else: # aged not summary
                head = [
                    {'name': _('Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('JRNL'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account Name'),
                     'larg': 15,
                     'col': {}},
                    {'name': _('Journal entries'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Ref'),
                     'larg': 40,
                     'col': {}},
                    {'name': _('Partner'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Due Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Not Due'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('0-30'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('30-60'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('60-90'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('90-120'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Older'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Total'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Match.'),
                     'larg': 10,
                     'col': {}},
                ]
                table = []
                for h in head:
                    col = {'header': h['name']}
                    col.update(h['col'])
                    table.append(col)

                def _set_line(line):
                    sheet.write(i, 0, line.get('date', ''))
                    sheet.write(i, 1, line.get('code', ''))
                    sheet.write(i, 2, line.get('a_code', ''))
                    sheet.write(i, 3, line.get('a_name', ''))
                    sheet.write(i, 4, line.get('move_name', ''))
                    sheet.write(i, 5, line.get('displayed_name', ''))
                    sheet.write(i, 6, line.get('partner_name', ''))
                    sheet.write(i, 7, line.get('date_maturity', ''))
                    sheet.write(i, 8, round(line.get('not_due', ''), rounding), currency_format)
                    sheet.write(i, 9, round(line.get('0-30', ''), rounding), currency_format)
                    sheet.write(i, 10, round(line.get('30-60', ''), rounding), currency_format)
                    sheet.write(i, 11, round(line.get('60-90', ''), rounding), currency_format)
                    sheet.write(i, 12, round(line.get('90-120', ''), rounding), currency_format)
                    sheet.write(i, 13, round(line.get('older', ''), rounding), currency_format)
                    sheet.write(i, 14, round(line.get('total', ''), rounding), currency_format)
                    sheet.write(i, 15, line.get('matching_number', ''))

                def _set_table(start_row, row):
                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    #sheet.write(row + 1, 10, "=I%s-J%s" % (row + 2, row + 2), currency_format)

                # With total workbook
                sheet = workbook.add_worksheet(data['name_report'] + _(' Totals'))
                _header_sheet(sheet)

                row = 6
                for group_by in data['group_by_data']['ids']:
                    all_lines = []
                    for line in data['lines_group_by'][group_by]['new_lines']:
                        if line['type_line'] != 'total':
                            all_lines.append(line)

                    # Head
                    if all_lines:
                        row += 1
                        save_top_row = row
                        sheet.write(row, 0, data['lines_group_by'][group_by]['code'], left)
                        sheet.write(row, 1, '', top)
                        sheet.write(row, 2, data['lines_group_by'][group_by]['name'], middle)
                        sheet.write(row, 3, '', top)
                        sheet.write(row, 4, '', top)
                        sheet.write(row, 5, '', top)
                        sheet.write(row, 6, '', c_middle)
                        sheet.write(row, 7, '', c_middle)
                        sheet.write(row, 8, '', c_middle)
                        sheet.write(row, 9, '', c_middle)
                        sheet.write(row, 10, '', c_middle)
                        sheet.write(row, 11, '', c_middle)
                        sheet.write(row, 12, '', c_middle)
                        sheet.write(row, 13, '', c_middle)
                        sheet.write(row, 14, '', c_middle)
                        sheet.write(row, 15, '', right)

                        row += 2
                        start_row = row
                        for i, line in enumerate(all_lines):
                            i += row
                            _set_line(line)

                        row = i

                        for j, h in enumerate(head):
                            sheet.set_column(j, j, h['larg'])

                        _set_table(start_row, row)
                        row += 2

                # Pivot
                sheet = workbook.add_worksheet(data['name_report'])
                _header_sheet(sheet)

                all_lines = []
                for group_by in data['group_by_data']['ids']:
                    for line in data['lines_group_by'][group_by]['new_lines']:
                        if line['type_line'] != 'total':
                            all_lines.append(line)
                # Head
                if all_lines:
                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        _set_line(line)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    _set_table(start_row, row)

        else: #standard report

            if report.summary:
                sheet = workbook.add_worksheet(data['name_report'])
                _header_sheet(sheet)

                all_lines = []
                for group_by in data['group_by_data']['ids']:
                    all_lines.update(data['lines_group_by'][group_by])
                if all_lines:
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

            else:  # not summary

                head = [
                    {'name': _('Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('JRNL'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Account Name'),
                     'larg': 15,
                     'col': {}},
                    {'name': _('Journal entries'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Ref'),
                     'larg': 40,
                     'col': {}},
                    {'name': _('Partner'),
                     'larg': 20,
                     'col': {}},
                    {'name': _('Due Date'),
                     'larg': 10,
                     'col': {}},
                    {'name': _('Debit'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Credit'),
                     'larg': 15,
                     'col': {'total_function': 'sum', 'format': currency_format}},
                    {'name': _('Balance'),
                     'larg': 15,
                     'col': {'format': currency_format}},
                    {'name': _('Match.'),
                     'larg': 10,
                     'col': {}},
                ]
                table = []
                for h in head:
                    col = {'header': h['name']}
                    col.update(h['col'])
                    table.append(col)

                def _set_line(line):
                    sheet.write(i, 0, line.get('date', ''))
                    sheet.write(i, 1, line.get('code', ''))
                    sheet.write(i, 2, line.get('a_code', ''))
                    sheet.write(i, 3, line.get('a_name', ''))
                    sheet.write(i, 4, line.get('move_name', ''))
                    sheet.write(i, 5, line.get('displayed_name', ''))
                    sheet.write(i, 6, line.get('partner_name', ''))
                    sheet.write(i, 7, line.get('date_maturity', ''))
                    sheet.write(i, 8, round(line.get('debit', ''), rounding), currency_format)
                    sheet.write(i, 9, round(line.get('credit', ''), rounding), currency_format)
                    sheet.write(i, 10, round(line.get('progress', ''), rounding), currency_format)
                    sheet.write(i, 11, line.get('matching_number', ''))

                def _set_table(start_row, row):
                    sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    #sheet.write(row + 1, 10, "=I%s-J%s" % (row + 2, row + 2), currency_format)

                # With total workbook
                sheet = workbook.add_worksheet(data['name_report'] + _(' Totals'))
                _header_sheet(sheet)

                row = 6
                for group_by in data['group_by_data']['ids']:
                    all_lines = []
                    for line in data['lines_group_by'][group_by]['new_lines']:
                        if line['type_line'] != 'total':
                            all_lines.append(line)

                    # Head
                    if all_lines:
                        row += 1
                        save_top_row = row
                        sheet.write(row, 0, data['lines_group_by'][group_by]['code'], left)
                        sheet.write(row, 1, '', top)
                        sheet.write(row, 2, data['lines_group_by'][group_by]['name'], middle)
                        sheet.write(row, 3, '', top)
                        sheet.write(row, 4, '', top)
                        sheet.write(row, 5, '', top)
                        sheet.write(row, 6, '', top)
                        sheet.write(row, 7, '', top)
                        sheet.write(row, 8, data['lines_group_by'][group_by]['debit'], c_middle)
                        sheet.write(row, 9, data['lines_group_by'][group_by]['credit'], c_middle)
                        sheet.write(row, 10, data['lines_group_by'][group_by]['debit - credit'], c_middle)
                        sheet.write(row, 11, '', right)

                        row += 2
                        start_row = row
                        for i, line in enumerate(all_lines):
                            i += row
                            _set_line(line)

                        row = i

                        for j, h in enumerate(head):
                            sheet.set_column(j, j, h['larg'])

                        _set_table(start_row, row)
                        # sheet.write(save_top_row, 8, '=I%s' % (row + 2), c_middle)
                        # sheet.write(save_top_row, 9, '=J%s' % (row + 2), c_middle)
                        # sheet.write(save_top_row, 10, '=I%s-J%s' % (save_top_row + 1, save_top_row + 1), c_middle)
                        row += 2

                # Pivot workbook
                sheet = workbook.add_worksheet(data['name_report'])
                _header_sheet(sheet)

                all_lines = []
                for group_by in data['group_by_data']['ids']:
                    for line in data['lines_group_by'][group_by]['new_lines']:
                        if line['type_line'] != 'total':
                            all_lines.append(line)
                # Head
                if all_lines:
                    row = 6
                    row += 1
                    start_row = row
                    for i, line in enumerate(all_lines):
                        i += row
                        _set_line(line)
                    row = i

                    for j, h in enumerate(head):
                        sheet.set_column(j, j, h['larg'])

                    _set_table(start_row, row)


AccountStandardExcel('report.account_standard_report.report_account_standard_excel', 'account.report.standard.ledger')
