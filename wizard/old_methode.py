

class AccountStandardLedgerReportObject(models.TransientModel):
    _name = 'account.report.standard.ledger.report.object'

    name = fields.Char()
    object_id = fields.Integer()
    report_id = fields.Many2one('account.report.standard.ledger.report')
    line_ids = fields.One2many('account.report.standard.ledger.line', 'report_object_id')


    def _sql_report_account_lines(self):
        query = """INSERT INTO  account_report_standard_ledger_report_object
            (report_id, create_uid, create_date, object_id)
        SELECT DISTINCT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            ra.account_id AS object_id
        FROM
            account_report_standard_ledger_line ra
        WHERE
            ra.report_id = %s;

        UPDATE account_report_standard_ledger_line ra
        SET
            report_object_id = ro.id
        FROM
            account_report_standard_ledger_report_object ro
        WHERE
            ro.report_id = %s
            AND ra.report_id = %s
            AND ra.account_id = ro.object_id

            """



        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            # WHERE
            self.report_id.id,

            # SELECT
            self.report_id.id,
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))

    def _sql_report_partner_lines(self):
        query = """INSERT INTO  account_report_standard_ledger_report_object
            (report_id, create_uid, create_date, object_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            obj.id AS object_id
        FROM
            res_partner obj
        WHERE
            obj.id IN %s;

        UPDATE account_report_standard_ledger_line ra
        SET
            report_object_id = ro.id
        FROM
            account_report_standard_ledger_report_object ro
        WHERE
            ro.report_id = %s
            AND ra.report_id = %s
            AND ra.account_id = ro.object_id

            """

        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            # WHERE
            tuple(self.partner_ids.ids) if self.partner_ids else (None,),

            # SELECT
            self.report_id.id,
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))


    def _sql_init_unreconcillied_table(self):
        return
        # init_unreconcillied_table
        query = """INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, journal_id, partner_id, move_id,date, date_maturity, debit, credit, balance, full_reconcile_id, reconciled, report_object_id)

        WITH matching_in_futur_before_init (id) AS
        (
        SELECT DISTINCT
            afr.id
        FROM
            account_full_reconcile afr
        INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
        WHERE
            aml.company_id = %s
            AND aml.date >= %s
        ),

        matching_in_futur_after_date_to (id) AS
        (
        SELECT DISTINCT
            afr.id
        FROM
            account_full_reconcile afr
        INNER JOIN account_move_line aml ON aml.full_reconcile_id = afr.id
        WHERE
            aml.company_id = %s
            AND aml.date > %s
        )

        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            aml.account_id,
            '1_init_line' AS type,
            aml.journal_id,
            aml.partner_id,
            aml.move_id,
            aml.date,
            aml.date_maturity,
            aml.debit,
            aml.credit,
            aml.balance,
            aml.full_reconcile_id,
            CASE WHEN aml.full_reconcile_id is NOT NULL AND NOT mifad.id IS NOT NULL THEN TRUE ELSE FALSE END AS reconciled,
            ro.id AS report_object_id
        FROM
            account_report_standard_ledger_report_object ro
            INNER JOIN account_move_line aml ON (CASE WHEN %s THEN aml.account_id = ro.object_id ELSE aml.partner_id = ro.object_id END)
            LEFT JOIN account_account acc ON (aml.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (aml.move_id = m.id)
            LEFT JOIN matching_in_futur_before_init mif ON (aml.full_reconcile_id = mif.id)
            LEFT JOIN matching_in_futur_after_date_to mifad ON (aml.full_reconcile_id = mifad.id)
        WHERE
            m.state IN %s
            AND ro.report_id = %s
            AND aml.company_id = %s
            AND aml.date < %s
            AND acc_type.include_initial_balance = TRUE
            AND aml.journal_id IN %s
            AND aml.account_id IN %s
            AND (%s OR aml.partner_id IN %s)
            AND NOT (%s AND acc.compacted = TRUE)
            AND (%s OR NOT (aml.full_reconcile_id is NOT NULL AND NOT mifad.id IS NOT NULL))
        	AND acc.type_third_parties IN ('supplier', 'customer')
            AND (aml.full_reconcile_id IS NULL OR mif.id IS NOT NULL)
        ORDER BY
            aml.date
        """

        params = [
            # matching_in_futur init
            self.company_id.id,
            self.date_from,

            # matching_in_futur date_to
            self.company_id.id,
            self.date_to,

            # init_unreconcillied_table
            # SELECT
            self.report_id.id,
            self.env.uid,
            # FROM
            True if self.type_ledger in ('general', 'open', 'journal') else False,
            # WHERE
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            self.report_id.id,
            self.company_id.id,
            self.date_from,
            tuple(self.journal_ids.ids) if self.journal_ids else (None,),
            tuple(self.account_ids.ids) if self.account_ids else (None,),
            True if self.type_ledger in ('general', 'open', 'journal') else False,
            tuple(self.partner_ids.ids) if self.partner_ids else (None,),
            self.compact_account,
            self.reconciled,
        ]

        self.env.cr.execute(query, tuple(params))

    def _sql_cumul(self):
        return
        query = """WITH table_progress AS (
            SELECT
            	aml.id AS id,
            	SUM(aml.balance) OVER (PARTITION BY aml.report_object_id ORDER BY aml.report_object_id, aml.id) AS progress
            FROM
            	account_report_standard_ledger_line aml
            WHERE
            	report_id = %s
                AND type != '4_total')

            UPDATE account_report_standard_ledger_line ra
            SET
            	cumul_balance = table_progress.progress
            FROM
            	table_progress
            WHERE
                ra.report_id = %s
            	AND ra.id = table_progress.id
            """
        params = [
            # WHERE
            self.report_id.id,
            # WHERE
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))

    def _sql_account_total(self):
        return
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, date, debit, credit, balance, cumul_balance, report_object_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            MIN(account_id),
            '4_total' AS type,
            %s AS date,
            COALESCE(SUM(debit), 0) AS debit,
            COALESCE(SUM(credit), 0) AS credit,
            COALESCE(SUM(balance), 0) AS balance,
            COALESCE(SUM(balance), 0) AS cumul_balance,
            MIN(report_object_id) AS report_object_id
        FROM
            account_report_standard_ledger_line
        WHERE
            report_id = %s
            AND account_id IS NOT NULL
        GROUP BY
            account_id
        """
        params = [
            # SELECT
            self.report_id.id,
            self.env.uid,
            self.date_from,
            # WHERE
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))

    def _sql_partner_total(self):
        return
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, partner_id, type, date, debit, credit, balance, cumul_balance, report_object_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            MIN(partner_id),
            '4_total' AS type,
            %s AS date,
            COALESCE(SUM(debit), 0) AS debit,
            COALESCE(SUM(credit), 0) AS credit,
            COALESCE(SUM(balance), 0) AS balance,
            COALESCE(SUM(balance), 0) AS cumul_balance,
            MIN(report_object_id) AS report_object_id
        FROM
            account_report_standard_ledger_line
        WHERE
            report_id = %s
            AND partner_id IS NOT NULL
        GROUP BY
            partner_id
        """
        params = [
            self.report_id.id,
            self.env.uid,
            self.date_from,
            self.report_id.id,
        ]
        self.env.cr.execute(query, tuple(params))
