from pprint import pprint
from django.db import models, transaction

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from migrate import V1, V2, load_project, BASE_PATH
from map_model import MapModel
from map_model_implementations import year_to_date

load_project(BASE_PATH+'/land-matrix-2', 'landmatrix')
load_project(BASE_PATH+'/land-matrix', 'editor')

from landmatrix.models import Language, ActivityAttributeGroup, StakeholderAttributeGroup, Country
from editor.models import A_Tag, A_Tag_Group, Comment, SH_Tag_Group, SH_Tag


class MapTagGroups(MapModel):

    language = Language.objects.get(pk=1)

    @classmethod
    @transaction.atomic(using=V2)
    def map_all(cls, save=False):

        cls._check_dependencies()
        cls._start_timer()
        cls._save = save

        cls.migrate_tag_group_set(cls.tag_groups)

        cls._done = True
        cls._print_summary()

    @classmethod
    def migrate_tag_group_set(cls, tag_groups):
        for i, tag_group in enumerate(tag_groups):
            cls.migrate_tag_group(i, tag_group)

    @classmethod
    def migrate_tag_group(cls, i, tag_group):

        for relevant_tags in cls.relevant_tag_sets(tag_group):
            cls.migrate_tags(relevant_tags, tag_group)

        cls._print_status({ key: value for key, value in tag_group.__dict__.items() if not callable(value) and not key.startswith('__') }, i)


class MapActivityTagGroup(MapTagGroups):

    old_class = A_Tag_Group
    tag_groups = A_Tag_Group.objects.using(V1).select_related('fk_activity') # .filter(fk_activity__activity_identifier=147, fk_activity__version=4)

    @classmethod
    def relevant_tag_sets(cls, tag_group):
        return [
            [tag_group.fk_a_tag],
            A_Tag.objects.using(V1).filter(fk_a_tag_group=tag_group).select_related('fk_a_key', 'fk_a_value'),
        ]

    @classmethod
    def migrate_tags(cls, relevant_tags, tag_group):
        attrs = {}
        for tag in relevant_tags:
            key = tag.fk_a_key.key
            value = tag.fk_a_value.value
            year = tag.fk_a_value.year
            if key in attrs:
                cls.write_activity_attribute_group(attrs, tag_group, year)
            attrs[key] = value
        if attrs:
            cls.write_activity_attribute_group(attrs, tag_group, year)

    @classmethod
    def write_activity_attribute_group(cls, attrs, tag_group, year):
        aag = ActivityAttributeGroup(
            fk_activity_id=tag_group.fk_activity.id, fk_language=cls.language,
            date=year_to_date(year), attributes=attrs, name=attrs.get('name')
        )

        comments = cls.get_comments(tag_group)
        if comments:
            aag.attributes.update({
                tag_group.fk_a_tag.fk_a_value.value + '_comment': '\n'.join(comments)
            })
#        print(aag.attributes)
        if cls._save:
            aag.save(using=V2)

    @classmethod
    def get_comments(cls, tag_group):
        queryset = Comment.objects.using(V1).filter(fk_a_tag_group=tag_group)
        return [comment.comment for comment in queryset]


class MapStakeholderTagGroup(MapTagGroups):

    old_class = SH_Tag_Group
    tag_groups = SH_Tag_Group.objects.using(V1).select_related('fk_stakeholder')

    @classmethod
    def relevant_tag_sets(cls, tag_group):
        return [
            [tag_group.fk_sh_tag],
            SH_Tag.objects.using(V1).filter(fk_sh_tag_group=tag_group).select_related('fk_sh_key', 'fk_sh_value'),
        ]

    @classmethod
    def migrate_tags(cls, relevant_tags, tag_group):
        attrs = {}
        for tag in relevant_tags:
            key = tag.fk_sh_key.key
            value = tag.fk_sh_value.value
            if key in attrs:
                cls.write_stakeholder_attribute_group(attrs, tag_group)
            attrs[key] = value
        if attrs:
            cls.write_stakeholder_attribute_group(attrs, tag_group)

    @classmethod
    def write_stakeholder_attribute_group(cls, attrs, tag_group):
        attrs = resolve_country(attrs)
        sag = StakeholderAttributeGroup(
            fk_stakeholder_id=tag_group.fk_stakeholder.id, fk_language=cls.language,
            attributes=attrs, name=attrs.get('name')
        )

        comments = cls.get_comments(tag_group)
        if comments:
            sag.attributes.update({
                tag_group.fk_sh_tag.fk_sh_value.value + '_comment': '\n'.join(comments)
            })

        if cls._save:
            sag.save(using=V2)

    @classmethod
    def get_comments(cls, tag_group):
        queryset = Comment.objects.using(V1).filter(fk_sh_tag_group=tag_group)
        return set([comment.comment.strip() for comment in queryset if comment.comment.strip()])

def resolve_country(attrs):
    if 'country' in attrs:
        attrs['country'] = Country.objects.using(V2).get(name=attrs['country']).id
    return attrs