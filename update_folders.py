import argparse
import copy
import docker
import json
client = docker.from_env()

def toJSON(input):
    return json.dumps(input, sort_keys=True, indent=4)

if not client:
    print("No Docker config found!")
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("iconstyle", nargs='?' )
args = parser.parse_args()

folder_prefix = "auto-project-"
config_path = "/boot/config/plugins/docker.folder/folders.json"
config = json.load(open(config_path))
existing_config = toJSON(config)
folders = {}

for id, folder in config.get("folders").items():
    if id.startswith(folder_prefix) > 1:
        found_folder = list(folder)

        # Clear children to handle garbage collection of old container names
        found_folder["children"] = []
        found_folder["regex"] = ""
        found_folder["icon"] = ""

        folders[id] = found_folder
        config.get("folders").pop(id)

default_folder = {'name': '', 'icon': '', 'docker_preview': 'none', 'docker_preview_hover_only': False, 'docker_preview_text_update_color': True, 'docker_preview_icon_grayscale': False, 'docker_preview_icon_show_log': True, 'docker_preview_icon_show_webui': True, 'docker_preview_no_icon_row_count': 12, 'docker_preview_no_icon_column_count': 2, 'docker_preview_advanced_context_menu': False, 'docker_preview_advanced_context_menu_activation_mode': 'click', 'docker_preview_advanced_context_menu_graph_mode': 'none', 'docker_icon_style': 'label-tab', 'docker_expanded_style': 'right', 'docker_start_expanded': False, 'dashboard_expanded': False, 'dashboard_expanded_button': False, 'icon_animate_hover': False, 'status_icon_autostart': False, 'regex': '', 'buttons': [], 'children': []}
for container in client.containers.list(all=True, filters={"label": "com.docker.compose.project"}):
    folder_key = folder_prefix + container.labels["com.docker.compose.project"]

    if not folder_key in folders:
        folders[folder_key] = copy.deepcopy(default_folder)
        folders[folder_key]["name"] = container.labels["com.docker.compose.project"]

    folders[folder_key]["children"].append(container.name)

    # Give the folder the first icon found
    if "net.unraid.docker.icon" in container.labels and not folders[folder_key]["icon"]:
        folders[folder_key]["icon"] = container.labels["net.unraid.docker.icon"]

for id, folder in folders.items():
    if len(folder["children"]) > 0:
        if args.iconstyle:
            folder["docker_icon_style"] = args.iconstyle

        config.get("folders")[id] = folder


# Only write to if config has changed. Don't ruin the flash drive
if toJSON(config) != existing_config:
    print("Updating folder config")
    with open(config_path, "w") as file:
        file.write(toJSON(config))
