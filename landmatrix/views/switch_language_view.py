from django.utils.translation import ugettext_lazy as _, LANGUAGE_SESSION_KEY
from django.views.generic.base import RedirectView 
from django.conf import settings

class SwitchLanguageView(RedirectView):
    
    permanent = False
    
    def get(self, request, *args, **kwargs):
        language = kwargs.pop('language', None)
        
        if not language or language not in dict(settings.LANGUAGES).keys():
            messages.error(request, _('The language "%s" is not supported' % language))
        else:
            request.session[LANGUAGE_SESSION_KEY] = language
            request.session['django_language'] = language
            request.LANGUAGE_CODE = language
        #messages.success(request, _('Language was switched successfully.'))
        
        return super(SwitchLanguageView, self).get(request, *args, **kwargs)
        
    def get_redirect_url(self, **kwargs):
        return self.request.GET.get('next', self.request.META.get('HTTP_REFERER', '/'))
        
switch_language = SwitchLanguageView.as_view()