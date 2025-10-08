from django.utils.translation import pgettext_lazy


USE_I18N = True

LANGUAGE_FALLBACK = True

USE_L10N = True

USE_TZ = True


LANGUAGES = [
    ('en', pgettext_lazy('Server localization name English', 'langs.english')),
    ('cs', pgettext_lazy('Server localization name Czech', 'langs.czech')),
]

LANGUAGES_KEYS = list(dict(LANGUAGES).keys())