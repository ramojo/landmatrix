from datetime import timedelta
from pprint import pprint
from traceback import print_stack

from django.utils.encoding import force_text

from editor.models import UserRegionalInfo
from grid.views.activity_protocol import ActivityProtocol
from landmatrix.models.activity import Activity, HistoricalActivity
from landmatrix.models.activity_attribute_group import ActivityAttribute
from landmatrix.models.activity_changeset_review import ActivityChangesetReview, ReviewDecision
from landmatrix.models.activity_feedback import ActivityFeedback
from landmatrix.models.activity_changeset import ActivityChangeset

from django.views.generic import View
from django.http.response import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
import json

from landmatrix.models.country import Country
from landmatrix.models.investor import InvestorActivityInvolvement, InvestorVentureInvolvement, \
    Investor
from landmatrix.models.status import Status

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class ChangesetProtocol(View):

    DEFAULT_MAX_NUM_CHANGESETS = 100

    #@method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):

        self.request = request

        if "action" in kwargs:
            action = kwargs["action"]
        else:
            raise IOError("Parameter 'action' missing")

        if request.POST:
            self.data = json.loads(request.POST["data"])
        elif action in ('history', 'list'):
            self.data = {}
        else:
            raise IOError("Parameters missing")

        if action == "dashboard":
            return self.dashboard(request)
        elif action == "list":
            return self.list(request, *args, **kwargs)
        elif action == "approve":
            return self.approve(request, *args, **kwargs)
        elif action == "reject":
            return self.reject(request, *args, **kwargs)
        else:
            raise IOError("Unknown action")

    def dashboard(self, request):
        res = {
            "latest_added": self.get_paged_results(
                self.apply_dashboard_filters(ActivityChangeset.objects.get_by_state("active"))[:self.DEFAULT_MAX_NUM_CHANGESETS],
                request.GET.get('latest_added_page')
            ),
            "latest_modified": self.get_paged_results(
                self.apply_dashboard_filters(ActivityChangeset.objects.get_by_state("overwritten"))[:self.DEFAULT_MAX_NUM_CHANGESETS],
                request.GET.get('latest_modified_page')
            ),
            "latest_deleted": self.get_paged_results(
                self.apply_dashboard_filters(ActivityChangeset.objects.get_by_state("deleted"))[:self.DEFAULT_MAX_NUM_CHANGESETS],
                request.GET.get('latest_deleted_page')
            ),
            "manage": self._changeset_to_json(limit=2),
            "feedbacks": _feedbacks_to_json(request.user, limit=5),
            "rejected": _rejected_to_json(request.user)

        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    def list(self, request, *args, **kwargs):
        """
        POST params:
            "a_changesets": ["updates", "deletes", "inserts"]
            "sh_changesets": ["updates", "deletes", "inserts"]
        """
        user = request.user
        if user.has_perm("editor.change_activity"):
            self.data = {
                "a_changesets": ["updates", "deletes", "inserts"],
                "sh_changesets": ["deletes"],
            }
        else:
            self.data = {
                "a_changesets": ["my_deals"],
            }
        res = self._changeset_to_json(
            user,
            request.GET.get('my_deals_page'), request.GET.get('updates_page'),
            request.GET.get('inserts_page'), request.GET.get('deletions_page')
        )
        res["feedbacks"] = _feedbacks_to_json(user, request.GET.get('feedbacks_page'))
        res["rejected"] = _rejected_to_json(request.user)

        return HttpResponse(json.dumps(res), content_type="application/json")

    @transaction.atomic
    def approve(self, request, *args, **kwargs):
        res = {"errors": []}
        self._approve_a_changesets(request)
        _approve_investor_changes(request)
        return HttpResponse(json.dumps(res), content_type="application/json")

    def _approve_a_changesets(self, request):
        for cs in self.data.get("a_changesets", {}):
            changeset = ActivityChangeset.objects.get(id=cs.get("id"))
            activity = changeset.fk_activity
            if activity.fk_status.name == "pending":
                _approve_activity_change(activity, changeset, cs.get("comment"), request)
            elif activity.fk_status.name == "to_delete":
                _approve_activity_deletion(activity, changeset, cs.get("comment"), request)

            _approve_investor_changes(get_activity_investor(activity), changeset)

    @transaction.atomic
    def reject(self, request, *args, **kwargs):
        res = {"errors": []}
        print('reject:', self.data)
        self._reject_a_changesets(request)
        _reject_investor_changes(request)
        return HttpResponse(json.dumps(res), content_type="application/json")

    def _reject_a_changesets(self, request):
        for cs in self.data.get("a_changesets", {}):
            changeset = ActivityChangeset.objects.get(id=cs.get("id"))
            activity = changeset.fk_activity
            if activity.fk_status.name in ("pending", "to_delete"):
                _reject_activity_change(activity, changeset, cs.get('comment'), request)
            _reject_investor_changes(get_activity_investor(activity))

    def get_paged_results(self, records, page_number, per_page=10):
        paginator = Paginator(records, per_page)
        page = _get_page(page_number, paginator)

        results = {"cs": []}
        for changeset in page.object_list:
            results["cs"].append(self.changeset_template_data(changeset))
        # results["pagination"] = self._pagination_to_json(paginator, page)
        return results

    def changeset_template_data(self, changeset, extra_data=None):
        template_data = {
            'id': 0 if not changeset or not changeset.pk else changeset.pk,
            "deal_id": 0 if not changeset or not changeset.fk_activity else changeset.fk_activity.activity_identifier,
            "user": force_text(_("Public User")) if not changeset or not changeset.fk_user else force_text(changeset.fk_user.username),
            "timestamp": 0 if not changeset else changeset.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "comment": changeset_comment(changeset)
        }
        if extra_data:
            template_data.update(extra_data)

        return template_data

    def _changeset_to_json(self, user=None, my_deals_page=1, updates_page=1, inserts_page=1, deletions_page=1, limit=None):
        res = {}
        if not self.data:
            self.data = {
                "a_changesets": ["updates", "deletes", "inserts"],
                #"sh_changesets": ["deletes"],
            }
        if "a_changesets" in self.data:
            self.handle_a_changesets(deletions_page, inserts_page, limit, my_deals_page, res, updates_page, user)
        # print('_changeset_to_json'); pprint(res)
        return res

    def handle_a_changesets(self, deletions_page, inserts_page, limit, my_deals_page, res, updates_page, user):
        changesets = {}
        if "my_deals" in self.data["a_changesets"]:
            self.handle_my_deals(changesets, ActivityChangeset.objects, limit, my_deals_page, user)
        if "updates" in self.data["a_changesets"]:
            self.handle_updates(changesets, ActivityChangeset.objects, limit, updates_page)
        if "inserts" in self.data["a_changesets"]:
            self.handle_inserts(changesets, ActivityChangeset.objects, inserts_page, limit)
        if "deletes" in self.data["a_changesets"]:
            handle_deletes(changesets, ActivityChangeset.objects, deletions_page, limit)
        if changesets:
            _uniquify_changesets_dict(changesets)
            res["a_changesets"] = changesets

    def handle_my_deals(self, a_changesets, changesets, limit, my_deals_page, user):
        changesets_my_deals = changesets.get_my_deals(user.id)
        changesets_my_deals = self.apply_dashboard_filters(changesets_my_deals)
        changesets_my_deals = limit and changesets_my_deals[:limit] or changesets_my_deals
        paginator = Paginator(changesets_my_deals, 10)
        page = _get_page(my_deals_page, paginator)
        changesets_my_deals = page.object_list
        my_deals = {"cs": []}
        for changeset in changesets_my_deals:
            my_deals["cs"].append(self.changeset_template_data(changeset, {"status": changeset.fk_activity.fk_status.name}))
        if my_deals["cs"]:
            my_deals["pagination"] = _pagination_to_json(paginator, page)
            a_changesets["my_deals"] = my_deals

    def handle_updates(self, a_changesets, changesets, limit, updates_page):
        changesets_update = changesets.filter(fk_activity__fk_status__name="pending")
        changesets_update = self.apply_dashboard_filters(changesets_update)
        changesets_update = limit and changesets_update[:limit] or changesets_update
        paginator = Paginator(changesets_update, 10)
        page = _get_page(updates_page, paginator)
        changesets_update = page.object_list
        updates = {"cs": []}
        for changeset in changesets_update:
            fields_changed = _find_changed_fields(changeset)
            updates["cs"].append(self.changeset_template_data(changeset, {"fields_changed": fields_changed}))
        if updates["cs"]:
            updates["pagination"] = _pagination_to_json(paginator, page)
            a_changesets["updates"] = updates

    def apply_dashboard_filters(self, changesets):
        if self.request.session.get('dashboard_filters', {}).get('country'):
            changesets = _filter_changesets_by_countries(
                changesets, self.request.session['dashboard_filters']['country']
            )
        elif self.request.session.get('dashboard_filters', {}).get('region'):
            country_ids = Country.objects.filter(
                fk_region_id__in=self.request.session.get('dashboard_filters', {}).get('region')
            ).values_list('id', flat=True).distinct()
            changesets = _filter_changesets_by_countries(changesets, [str(c) for c in country_ids])
        elif self.request.session.get('dashboard_filters', {}).get('user'):
            user = self.request.session.get('dashboard_filters', {}).get('user')
            if isinstance(user, list) and len(user):
                user = user[0]
            if UserRegionalInfo.objects.filter(user_id=user).exists():
                country = UserRegionalInfo.objects.get(user_id=user).country.all()
                if len(country):
                    changesets = _filter_changesets_by_countries(changesets, [c.id for c in country])

        return _uniquify_changesets_by_deal(changesets)

    def handle_inserts(self, a_changesets, changesets, inserts_page, limit):
        changesets_insert = changesets.filter(fk_activity__fk_status__name="pending")
        changesets_insert = self.apply_dashboard_filters(changesets_insert)
        changesets_insert = limit and changesets_insert[:limit] or changesets_insert
        paginator = Paginator(changesets_insert, 10)
        page = _get_page(inserts_page, paginator)
        changesets_insert = page.object_list
        inserts = {"cs": []}
        for cs in changesets_insert:
            inserts["cs"].append(self.changeset_template_data(cs))
        if inserts["cs"]:
            inserts["pagination"] = _pagination_to_json(paginator, page)
            a_changesets["inserts"] = inserts


def _approve_investor_changes(investor, changeset):
    _update_investor_status(
        investor,
        Status.objects.get(name="overwritten" if changeset.previous_version else "active")
    )


def _reject_investor_changes(investor):
    _update_investor_status(investor, Status.objects.get(name="rejected"))


def _update_investor_status(investor, status):
    if not investor:
        return
    investor.fk_status = status
    investor.save()


def get_activity_investor(activity):
    iai = InvestorActivityInvolvement.objects.filter(fk_activity=activity).first()
    if iai:
        return Investor.objects.filter(id=iai.fk_investor).first()
    return None


def _uniquify_changesets_dict(changesets):
    unique, deals = [], []
    for cs in changesets.get('inserts', {}).get('cs', []):
        if cs['deal_id'] not in deals:
            unique.append(cs)
            deals.append(cs['deal_id'])
    changesets.get('inserts', {})['cs'] = unique
    unique = []
    for cs in changesets.get('updates', {}).get('cs', []):
        if cs['deal_id'] not in deals:
            unique.append(cs)
            deals.append(cs['deal_id'])
    changesets.get('updates', {})['cs'] = unique


def _uniquify_changesets_by_deal(changesets):
    unique, deals = [], []
    for changeset in changesets:
        if changeset.fk_activity.activity_identifier not in deals:
            unique.append(changeset)
            deals.append(changeset.fk_activity.activity_identifier)
    return unique


def _filter_changesets_by_countries(changesets, countries):
    return changesets.filter(
        fk_activity__attributes__name='target_country',
        fk_activity__attributes__value__in=countries
    )


def changeset_comment(changeset):
    if changeset is None:
        return 'changeset is None'

    review = ActivityChangesetReview.objects.filter(fk_activity_changeset_id=changeset.id)
    if len(review) > 0:
        return review[0].comment
    else:
        return changeset.comment and len(changeset.comment) > 0 and changeset.comment or "-"


def _find_changed_fields(changeset):
    """
    This code never worked in the original Landmatrix. It is disabled until it is needed.
    """
    fields_changed = []
    return fields_changed

    activity = changeset.fk_activity
    prev_activity = activity.history.as_of(changeset.timestamp)
    prev_tags = dict(a.ActivityAttribute.history.filter(fk_activity=prev_activity). \
        filter(history_date__lte=changeset.timestamp).values_list('name', 'value'))
    tags = dict(ActivityAttribute.objects.filter(fk_activity=changeset.fk_activity) \
        .values_list('name', 'value'))

    prev_keys = []
    for key, value in tags.items():
        if key in prev_tags and value != prev_tags[key]:
            # field has been changed
            fields_changed.append(key)
            break
    for key in set(tags.keys()).difference(prev_tags.keys()):
        # field has been added or deleted
        fields_changed.append(key)
    return fields_changed


def handle_deletes(a_changesets, changesets, deletions_page, limit):
    changesets_delete = changesets.filter(fk_activity__fk_status__name="to_delete")
    changesets_delete = limit and changesets_delete[:limit] or changesets_delete
    paginator = Paginator(changesets_delete, 10)
    page = _get_page(deletions_page, paginator)
    changesets_delete = page.object_list
    deletes = {"cs": []}
    for cs in changesets_delete:
        comment = cs.comment and len(cs.comment) > 0 and cs.comment or "-"
        deletes["cs"].append({
            "id": cs.id,
            "deal_id": cs.fk_activity.activity_identifier,
            "user": cs.fk_user.username,
            "comment": comment
        })
    if deletes["cs"]:
        deletes["pagination"] = _pagination_to_json(paginator, page)
        a_changesets["deletes"] = deletes


def _feedbacks_to_json(user, feedbacks_page=1, limit=None):
    feedbacks = []
    feed = ActivityFeedback.objects.get_current_feedbacks(user.id)
    feed = limit and feed[:limit] or feed
    paginator = Paginator(feed, 10)
    page = _get_page(feedbacks_page, paginator)
    feed = page.object_list
    for feedback in feed:
        feedbacks.append({
            "deal_id": feedback.fk_activity.activity_identifier,
            "from_user": feedback.fk_user_created.username,
            "comment": feedback.comment,
            "timestamp": feedback.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {
        "feeds": feedbacks,
        "pagination": _pagination_to_json(paginator, page),
    }


def _rejected_to_json(user, limit=None):
    rejected = HistoricalActivity.objects.filter(fk_status__name='rejected', history_user_id=user.id)
    feed = limit and rejected[:limit] or rejected
    paginator = Paginator(feed, 10)
    page = _get_page(1, paginator)
    feed = page.object_list
    rejected = [
        {
            "deal_id": activity.activity_identifier,
            "user": user.username,
            "comment": _get_comment(activity),
            "timestamp": activity.history_date.strftime("%Y-%m-%d %H:%M:%S")
         } for activity in feed
    ]
    return {
        "cs": rejected,
        "pagination": _pagination_to_json(paginator, page),
    }


def _get_comment(historical_activity):
    changeset = ActivityChangesetReview.objects.filter(
        timestamp__gt=historical_activity.history_date - timedelta(seconds=1)
    ).filter(
        timestamp__lt=historical_activity.history_date + timedelta(seconds=1)
    ).filter(
        fk_activity_changeset__fk_activity_id=historical_activity.id
    ).first()
    return changeset.comment if changeset else None


def _get_page(page_number, paginator):
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)
    return page


def _pagination_to_json(paginator, page):
    pagination = {}
    if page.has_previous():
        pagination["previous"] = page.previous_page_number()
    if page.has_next():
        pagination["next"] = page.next_page_number()
    pagination["current"] = page.number
    pagination["last"] = paginator.num_pages
    pagination["total"] = paginator.count
    return pagination


def _approve_activity_change(activity, changeset, comment, request):
    _change_status_with_review(
        activity, Status.objects.get(name="overwritten" if changeset.previous_version else "active"),
        changeset, request.user,
        ReviewDecision.objects.get(name="approved"), comment
    )
    involvements = InvestorActivityInvolvement.objects.get_involvements_for_activity(activity)
    ap = ActivityProtocol()
    if len(involvements) > 0:
        _conditionally_update_stakeholders(activity, ap, involvements, request)
    # FIXME
    # Problem here: Involvements are not historical yet, but activity and investors are.
    # As an intermediate solution another involvement is created for each historical activity
    # which links to the public activity. Let's confirm the new and remove the old involvement.
    ap.prepare_deal_for_public_interface(activity.activity_identifier)


def _reject_activity_change(activity, changeset, comment, request):
    _change_status_with_review(
        activity, Status.objects.get(name="rejected"),
        changeset, request.user,
        ReviewDecision.objects.get(name="rejected"), comment
    )
    # FIXME
    # Problem here: Involvements are not historical yet, but activity and investors are.
    # As an intermediate solution another involvement is created for each historical activity
    # which links to the public activity. Let's remove the new involvement.


def _change_status_with_review(activity, status, changeset, user, review_decision, comment):
    activity.fk_status = status
    activity.save()
    ActivityChangesetReview.objects.create(
        fk_activity_changeset=changeset,
        fk_user=user,
        fk_review_decision=review_decision,
        comment=comment
    )


def _conditionally_update_stakeholders(activity, ap, involvements, request):
    operational_stakeholder = involvements[0].fk_investor
    if _any_investor_has_changed(operational_stakeholder, involvements):
        # TODO make sure this is correct: secondary investors changed
        involvement_stakeholders = [
            {"stakeholder": ivi.fk_stakeholder, "investment_ratio": ivi.investment_ratio}
            for iai in involvements
            for ivi in InvestorVentureInvolvement.objects.filter(fk_investor=iai.fk_investor)
        ]

        ap.update_secondary_investors(
            activity, operational_stakeholder, involvement_stakeholders, request
        )


def _approve_activity_deletion(activity, changeset, cs_comment, request):
    activity.fk_status = Status.objects.get(name="deleted")
    activity.save()
    review_decision = ReviewDecision.objects.get(name="deleted")
    ActivityChangesetReview.objects.create(
        fk_a_changeset=changeset,
        fk_user=request.user,
        fk_review_decision=review_decision,
        comment=cs_comment
    )
    ActivityProtocol().remove_from_lookup_table(activity.activity_identifier)


def _any_investor_has_changed(operational_stakeholder, involvements):
    op_subinvestor_ids = set(s.investor_identifier for s in operational_stakeholder.subinvestors.all())
    involvement_investor_ids = (i.fk_investor.investor_identifier for i in involvements)
    return any(op_subinvestor_ids.symmetric_difference(involvement_investor_ids))

