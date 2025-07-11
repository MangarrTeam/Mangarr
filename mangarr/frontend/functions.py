from django.shortcuts import render, redirect
from datetime import date
from server import settings

def custom_render(request, template_name, context={}):
    default_context = {
        'year': date.today().strftime("%Y"),
        'base_url': f'{request.scheme}://{request.get_host()}',
        'instance_name': settings.INSTANCE_NAME,
    }

    context.update(default_context)
    return render(request, template_name, context)


def model_field_to_dict(model) -> dict:
    return {f.name: getattr(model, f.name) for f in model._meta.fields}