from core.settings import LANGUAGES_KEYS, LANGUAGE_CODE
from django.http import HttpResponseRedirect
import re

LANGUAGE_PREFIX_RE = re.compile(r'^/(%s)/' % '|'.join(LANGUAGES_KEYS))

class EnforceLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_language = LANGUAGE_CODE

    def __call__(self, request):
        path = request.path_info
        match = LANGUAGE_PREFIX_RE.match(path)

        if match:
            current_lang = match.group(1)
            if current_lang != self.default_language:
                new_path = LANGUAGE_PREFIX_RE.sub(f'/{self.default_language}/', path, count=1)
                return HttpResponseRedirect(new_path)

        return self.get_response(request)
