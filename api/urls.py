from django.conf.urls import url
from django.views.decorators.cache import cache_page

from api.views import *


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

urlpatterns = [
    url(r'^filter\.json', FilterView.as_view(), {'format': 'json'},
        name='api_filter'),
    url(r'^filter_preset\.json', FilterPresetView.as_view(),
        {'format': 'json'}, name='api_dashboard_filter_preset'),
    url(r'^deal_detail\.json', DealDetailView.as_view(), {'format': 'json'},
        name='api_deal_detail'),
    url(r'^investor_network\.json', InvestorNetworkView.as_view(),
        {'format': 'json'}, name='api_investor_network'),
    url(r'^latest_changes\.json', LatestChangesListView.as_view(),
        {'format': 'json'}, name='latest_changes_api'),
    url(r'^negotiation_status\.json',
        NegotiationStatusListView.as_view(), {'format': 'json'},
        name='negotiation_status_api'),
    url(r'^countries\.json', CountryListView.as_view(),
        {'format': 'json'}, name='countries_api'),
    url(r'^regions\.json', RegionListView.as_view(),
        {'format': 'json'}, name='regions_api'),
    url(r'^investors\.json', InvestorListView.as_view(),
        {'format': 'json'}, name='investors_api'),
    url(r'^implementation_status\.json',
        ImplementationStatusListView.as_view(), {'format': 'json'},
        name='implementation_status_api'),
    url(r'^intention\.json',
        InvestmentIntentionListView.as_view(), {'format': 'json'},
        name='intention'),
    url(r'^transnational_deals\.json',
        TransnationalDealListView.as_view(), {'format': 'json'},
        name='transnational_deals_api'),
    url(r'^top-10-countries\.json', Top10CountriesView.as_view(),
        {'format': 'json'}, name='top_10_countries_api'),
    url(r'^transnational_deals_by_country\.json',
        TransnationalDealsByCountryView.as_view(),
        {'format': 'json'}, name='transnational_deals_by_country_api'),
    url(r'^investor_country_summaries\.json',
        InvestorCountrySummaryListView.as_view(),
        {'format': 'json'}, name='investor_country_summaries_api'),
    url(r'^target_country_summaries\.json',
        TargetCountrySummaryListView.as_view(),
        {'format': 'json'}, name='target_country_summaries_api'),
    url(r'^investor_countries_for_target_country\.json',
        InvestorCountrySummaryListView.as_view(),
        {'format': 'json'}, name='investor_countries_for_target_country_api'),
    url(r'^target_countries_for_investor_country\.json',
        TargetCountrySummaryListView.as_view(),
        {'format': 'json'}, name='target_countries_for_investor_country_api'),
    url(r'^hectares\.json', HectaresView.as_view(),
        {'format': 'json'}, name='hectares_api'),
    url(r'^deals\.json', GlobalDealsView.as_view(), {'format': 'json'},
        name='deals_api'),
    url(r'^activities\.json', ActivityListView.as_view(),
        {'format': 'json'}, name='activities_api'),
    url(r'^statistics\.json', StatisticsListView.as_view(),
        {'format': 'json'}, name='statistics_api'),
    url(r'^users\.json', UserListView.as_view(), {'format': 'json'},
        name='users_api'),
    url(r'^agricultural-produce\.json',
        AgriculturalProduceListView.as_view(), {'format': 'json'},
        name='agricultural_produce_api'),
    url(r'^produce-info\.json', ProduceInfoView.as_view(), {'format': 'json'},
        name='produce_info_api'),
    url(r'^resource-extraction\.json', ResourceExtractionView.as_view(), {'format': 'json'},
        name='resource_extraction_api'),
    url(r'^logging\.json', LoggingView.as_view(), {'format': 'json'},
        name='logging_api'),
    url(r'^contract-farming\.json', ContractFarmingView.as_view(), {'format': 'json'},
        name='contract_farming_api'),
]
