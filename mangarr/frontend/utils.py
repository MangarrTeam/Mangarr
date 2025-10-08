from django.shortcuts import render, redirect
from datetime import date
from core import settings

def custom_render(request, template_name, context={}):
    default_context = {
        'year': date.today().strftime("%Y"),
        'base_url': f'{request.scheme}://{request.get_host()}',
        'instance_name': settings.INSTANCE_NAME,
        'uuid_placeholder': '00000000-0000-0000-0000-000000000000',
        'FILE_PATH_ROOT': settings.FILE_PATH_ROOT,
    }

    context.update(default_context)
    return render(request, template_name, context)


def model_field_to_dict(model) -> dict:
    return {f.name: getattr(model, f.name) for f in model._meta.fields}