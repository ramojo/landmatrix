#!/usr/bin/env python
import os
import sys
import csv
from collections import OrderedDict
from django.core.management import BaseCommand
from django.db import connections

from landmatrix.models import Activity, ActivityAttribute


class Command(BaseCommand):
    help = 'Compares deal lists'

    #def add_arguments(self, parser):
    #    parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        old = self.get_old_activities()
        new = self.get_new_activities()
        #with open(options['file'][0], 'r') as csvfile:
        #    reader = csv.reader(csvfile, delimiter=';')
        #    for i, row in enumerate(reader):
        #        if i == 0:
        #            continue
        #        old.append(row[0])
        #        new.append(row[2])
        missing = list(set(old) - set(new))
        missing.sort()
        deals = OrderedDict()
        deals['domestic'] = []
        deals['contract_farming'] = []
        deals['status'] = []
        deals['investor'] = []
        deals['unknown'] = []

        for deal_id in missing:
            a = Activity.objects.get(activity_identifier=deal_id)
            inv = a.investoractivityinvolvement_set.all()
            if inv.count() > 0:
                investor_name = inv[0].fk_investor.name
            else:
                investor_name = ''
            if a.deal_scope == 'domestic':
                deals['domestic'].append(a)
            elif ActivityAttribute.objects.filter(name='contract_farming', value='Yes', fk_activity_id=a.id).count() > 0:
                deals['contract_farming'].append(a)
            elif a.fk_status.name not in ('active', 'overwritten'):
                deals['status'].append(a)
            elif 'Unknown' in investor_name:
                deals['investor'].append(a)
            else:
                deals['unknown'].append(a)

        for key, value in deals.items():
            self.stdout.write('-- %i %s deals:' % (len(value), key))
            for a in value:
                inv = a.investoractivityinvolvement_set.all()
                if inv.count() > 0:
                    investor_name = inv[0].fk_investor.name
                else:
                    investor_name = ''
                self.stdout.write('%s (%s, %s, %s, %s, %s) --> %s' % (
                    a.activity_identifier,
                    a.is_public and 'public' or 'not public',
                    a.deal_scope,
                    a.negotiation_status,
                    a.fk_status.name,
                    investor_name,
                    a.get_not_public_reason(),
                    )
                )

    def get_old_activities(self):
        sql = """
        SELECT
                sub.negotiation_status,
                a.activity_identifier,
                size.value
             FROM
                activities a
             LEFT JOIN a_key_value_lookup size ON a.activity_identifier = size.activity_identifier AND size.key = 'pi_deal_size',
                (SELECT DISTINCT
                   a.id,
                   negotiation.value as negotiation_status,
                   negotiation.year as negotiation_status_year
                 FROM
                   activities a

        JOIN (
          status
        ) ON (status.id = a.fk_status)
        LEFT JOIN (
            involvements i,
            stakeholders s,
            primary_investors pi,
            status pi_st
        ) ON (i.fk_activity = a.id AND i.fk_stakeholder = s.id AND i.fk_primary_investor = pi.id AND pi.fk_status = pi_st.id)
        LEFT JOIN (
        sh_key_value_lookup skvf1,
          countries investor_country,
          regions investor_region
        ) ON (s.stakeholder_identifier = skvf1.stakeholder_identifier AND skvf1.key = 'country' AND skvf1.value = investor_country.id AND investor_country.fk_region = investor_region.id)
        LEFT JOIN (
            a_key_value_lookup intention
        ) ON (a.activity_identifier = intention.activity_identifier AND intention.key = 'intention')
        LEFT JOIN (
            a_key_value_lookup target_country,
             countries deal_country,
             regions deal_region
        ) ON (a.activity_identifier = target_country.activity_identifier AND target_country.key = 'target_country' AND target_country.value = deal_country.id AND deal_country.fk_region = deal_region.id)
        LEFT JOIN (
            a_key_value_lookup negotiation
        ) ON (a.activity_identifier = negotiation.activity_identifier AND negotiation.key = 'pi_negotiation_status')
        LEFT JOIN (
            a_key_value_lookup implementation
        ) ON (a.activity_identifier = implementation.activity_identifier AND implementation.key = 'pi_implementation_status')
        LEFT JOIN (
            a_key_value_lookup bf
        ) ON (a.activity_identifier = bf.activity_identifier AND bf.key = 'pi_deal')
        LEFT JOIN (
            a_key_value_lookup size
        ) ON (a.activity_identifier = size.activity_identifier AND size.key = 'pi_deal_size')
        LEFT JOIN (
            a_key_value_lookup deal_scope
        ) ON (a.activity_identifier = deal_scope.activity_identifier AND deal_scope.key = 'deal_scope')

                 WHERE

        a.version = (SELECT max(version) FROM activities amax, status st WHERE amax.fk_status = st.id AND amax.activity_identifier = a.activity_identifier AND st.name IN ("active", "overwritten", "deleted"))
        AND status.name in ("active", "overwritten")
        AND bf.value = 'True'
        AND pi.version = (SELECT max(version) FROM primary_investors pimax, status st WHERE pimax.fk_status = st.id AND pimax.primary_investor_identifier = pi.primary_investor_identifier AND st.name IN ("active", "overwritten", "deleted"))
        AND pi_st.name IN ("active", "overwritten")


                    AND lower(negotiation.value) in ('concluded (oral agreement)', 'concluded (contract signed)')  AND deal_scope.value = 'transnational'
              ) AS sub
             WHERE a.id = sub.id
        ORDER BY a.activity_identifier;
        """
        cursor = connections['v1_my'].cursor()
        cursor.execute(sql)
        return [a[1] for a in cursor.fetchall()]

    def get_new_activities(self):
        sql = """

            SELECT DISTINCT
                a.id
        --  subquery columns:
                ,
                a.activity_identifier,
                a.negotiation_status AS negotiation_status
            FROM landmatrix_activity                       AS a
        --  additional joins:
            LEFT JOIN landmatrix_activityattribute         AS target_country   ON a.id = target_country.fk_activity_id AND target_country.name = 'target_country'
        LEFT JOIN landmatrix_country                   AS deal_country     ON CAST(target_country.value AS NUMERIC) = deal_country.id
        LEFT JOIN landmatrix_activityattribute         AS attr_0                ON a.id = attr_0.fk_activity_id AND attr_0.name = 'deal_scope'
        LEFT JOIN landmatrix_activityattribute         AS attr_1                ON a.id = attr_1.fk_activity_id AND attr_1.name = 'negotiation_status'
        LEFT JOIN landmatrix_activityattribute         AS attr_2                ON a.id = attr_2.fk_activity_id AND attr_2.name = 'implementation_status'
        LEFT JOIN landmatrix_activityattribute         AS attr_3                ON a.id = attr_3.fk_activity_id AND attr_3.name = 'negotiation_status'
        LEFT JOIN landmatrix_activityattribute         AS attr_4                ON a.id = attr_4.fk_activity_id AND attr_4.name = 'implementation_status'
        LEFT JOIN landmatrix_activityattribute         AS attr_5                ON a.id = attr_5.fk_activity_id AND attr_5.name = 'intention'
        LEFT JOIN landmatrix_activityattribute         AS attr_6                ON a.id = attr_6.fk_activity_id AND attr_6.name = 'intended_size'
        LEFT JOIN landmatrix_activityattribute         AS attr_7                ON a.id = attr_7.fk_activity_id AND attr_7.name = 'contract_size'
        LEFT JOIN landmatrix_activityattribute         AS attr_8                ON a.id = attr_8.fk_activity_id AND attr_8.name = 'production_size'
        LEFT JOIN landmatrix_activityattribute         AS attr_9                ON a.id = attr_9.fk_activity_id AND attr_9.name = 'contract_farming'
        LEFT JOIN landmatrix_activityattribute         AS attr_10               ON a.id = attr_10.fk_activity_id AND attr_10.name = 'contract_farming'

                            LEFT JOIN landmatrix_activityattribute AS attr_11
                            ON (a.id = attr_11.fk_activity_id AND attr_11.name = 'target_country')


                            LEFT JOIN landmatrix_country AS ac11
                            ON CAST(NULLIF(attr_11.value, '0') AS NUMERIC) = ac11.id

        LEFT JOIN landmatrix_activityattribute         AS attr_12               ON a.id = attr_12.fk_activity_id AND attr_12.name = 'intention'

            WHERE
                a.fk_status_id IN (2, 3)
        AND a.is_public = 't'
        --  additional where conditions:

        --  filter sql:
                AND (a.deal_scope = 'transnational' AND

                        a.id NOT IN (
                            SELECT fk_activity_id
                            FROM landmatrix_activityattribute
                            WHERE landmatrix_activityattribute.name = 'deal_scope'
                            AND landmatrix_activityattribute.value NOT IN ('transnational')
                        )
                         AND
        ((attr_1.date >= '2000-01-01') OR
        (attr_2.date >= '2000-01-01') OR
        (attr_3.date IS NULL) OR
        (attr_4.date IS NULL)) AND
        (((attr_5.value NOT IN ('Logging') OR attr_5.value IS NULL))) AND
        ((CAST(NULLIF(attr_6.value, '0') AS DECIMAL) >= 200) OR
        (CAST(NULLIF(attr_7.value, '0') AS DECIMAL) >= 200) OR
        (CAST(NULLIF(attr_8.value, '0') AS DECIMAL) >= 200)) AND
        ((attr_9.value = 'No') OR

                        a.id NOT IN (
                            SELECT fk_activity_id
                            FROM landmatrix_activityattribute
                            WHERE landmatrix_activityattribute.name = 'contract_farming'
                            AND landmatrix_activityattribute.value NOT IN ('No')
                        )
                         OR
        (attr_10.value IS NULL)) AND
        ac11.high_income = 'f' AND
        (((attr_12.value NOT IN ('Mining', 'Oil / Gas extraction') OR attr_12.value IS NULL))))
        -- additional subquery options:

        AND a.negotiation_status IN ('Contract signed', 'Oral agreement')
          ORDER BY a.activity_identifier
        """
        cursor = connections['default'].cursor()
        cursor.execute(sql)
        return [a[1] for a in cursor.fetchall()]