import os
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from frontend.functions import custom_render
from django.contrib import messages
from plugins.downloader import download_plugin
from server.settings import PLUGINS_DIR, plugin_change_state, plugin_changed
from .manager import update_downloaded_metadata
from .functions import load_metadata, get_plugin

def get_plugin_by_domain(domain):
    return next((p for p in load_metadata() if p["domain"] == domain), None)

@permission_required("database.can_manage_plugins")
def plugin_manager(request):
    plugins = load_metadata()
    context = {
        "core_plugins": [p for p in plugins if p["category"] == "core"],
        "community_plugins": [p for p in plugins if p["category"] == "community"],
        "plugin_changed": plugin_change_state()
    }
    try:
        plugin = get_plugin("core", "mangarr-test-plugin")()
        manga = plugin.get_manga()
        print(manga)
    except:
        print("Can't print manga")
    return custom_render(request, "plugins/manager.html", context)

@permission_required("database.can_manage_plugins")
def download_plugin_view(request, domain):
    plugin = get_plugin_by_domain(domain)
    if not plugin:
        messages.error(request, "Plugin not found.")
        return redirect("plugin_manager")

    try:
        download_plugin(plugin["source"], plugin["category"], plugin["domain"], plugin["version"])
        plugin_changed()
        messages.success(request, f"Plugin '{plugin['name']}' downloaded.")
    except Exception as e:
        messages.error(request, f"Failed: {e}")

    return redirect("plugin_manager")

@permission_required("database.can_manage_plugins")
def delete_plugin_view(request, domain):
    plugin = get_plugin_by_domain(domain)
    if not plugin:
        messages.error(request, "Plugin not found.")
        return redirect("plugin_manager")

    plugin_path = os.path.join(PLUGINS_DIR, plugin["category"], domain)
    try:
        if os.path.isdir(plugin_path):
            import shutil
            shutil.rmtree(plugin_path)
            messages.success(request, f"Plugin '{plugin['name']}' deleted.")
            update_downloaded_metadata(domain)
            plugin_changed()
        else:
            messages.warning(request, "Plugin not downloaded.")
    except Exception as e:
        messages.error(request, f"Error deleting plugin: {e}")

    return redirect("plugin_manager")
