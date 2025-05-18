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