from django.utils.translation import gettext_lazy as _


USE_I18N = True

LANGUAGE_FALLBACK = True

USE_L10N = True

USE_TZ = True


LANGUAGES = [
    ('en', _('langs.english')),
    ('cs', _('langs.czech')),
]

LANGUAGES_KEYS = list(dict(LANGUAGES).keys())