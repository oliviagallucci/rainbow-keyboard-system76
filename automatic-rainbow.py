import sys
import os
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

def create_and_activate_venv():
    try:
        # install virtualenv if not already installed
        subprocess.check_call([sys.executable, "-m", "pip", "install", "virtualenv"])

        # create a new virtual environment
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])

        # activate the virtual environment
        activate_script = "venv\\Scripts\\activate" if sys.platform == "win32" else "source venv/bin/activate"
        subprocess.check_call(activate_script, shell=True)

        # install requests
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])

        print("virtual environment created, activated, and 'requests' installed.")

    except subprocess.CalledProcessError as e:
        print(f"error: {e}")

import requests

def get_downloads_folder():
    system_platform = os.name

    if system_platform == 'posix':  # linux or macOS
        home_dir = str(Path.home())
        return os.path.join(home_dir, 'Downloads')

    elif system_platform == 'nt':  # windows
        return os.path.join(os.path.expanduser('~'), 'Downloads')

    else:
        print("unsupported operating system")
        return None

def download_latest_deb_release(repo_owner, repo_name, output_path="."):
    # get the latest release info from GitHub api
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    response = requests.get(api_url)
    release_info = response.json()

    # find the Debian pkg asset in the release assets
    deb_asset = None
    for asset in release_info['assets']:
        if asset['name'].endswith('.deb'):
            deb_asset = asset
            break

    if deb_asset is None:
        print("no Debian package found in the latest release.")
        return

    # get the download url for the Debian package
    deb_url = deb_asset['browser_download_url']

    # download the Debian package
    response = requests.get(deb_url)
    deb_content = response.content

    # save the Debian package to the specified output path
    output_filename = os.path.join(output_path, f"{repo_name}_latest.deb")
    with open(output_filename, 'wb') as output_file:
        output_file.write(deb_content)

    print(f"latest release of {repo_name} (Debian package) downloaded to {output_filename}")

    return output_filename

def install_deb_file(deb_file_path):
    # check if the file exists
    if not os.path.exists(deb_file_path):
        print(f"error: the specified .deb file '{deb_file_path}' does not exist.")
        return

    # ask the user for confirmation
    user_confirmation = input(f"do you want to install {deb_file_path}? Type 'y' to confirm: ")

    # check if the user typed 'y' before proceeding
    if user_confirmation.lower() != 'y':
        print("installation aborted.")
        return

    # run the dpkg command to install the .deb file
    try:
        subprocess.run(['sudo', 'dpkg', '-i', deb_file_path], check=True)
        print(f"installation of {deb_file_path} successful.")
    except subprocess.CalledProcessError as e:
        print(f"error: failed to install {deb_file_path}.")
        print(f"command returned non-zero exit status {e.returncode}.")
        print(f"output: {e.output.decode('utf-8')}")

def update_mode(filepath, filename):
    try:
        # construct the full path to the file
        full_path = os.path.join(filepath, filename)

        # open the file and load the JSON data
        with open(full_path, 'r') as file:
            data = json.load(file)

        # update the "Mode" value
        if "Mode" in data:
            data["Mode"] = "Rainbow"

        # write the updated data back to the file
        with open(full_path, 'w') as file:
            json.dump(data, file, indent=4)

        print(f'successfully updated "Mode" to "Rainbow" in {full_path}')

    except FileNotFoundError:
        print(f'error: File "{full_path}" not found.')
    except json.JSONDecodeError:
        print(f'error: Unable to parse JSON in "{full_path}"')
    except Exception as e:
        print(f'an error occurred: {e}')

def deactivate_virtual_environment():
    # check if the script is running in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # deactivate the virtual environment
        try:
            if sys.platform == "win32":
                subprocess.check_call([sys.executable, "-m", "venv", "Scripts\\deactivate"])
            else:
                subprocess.check_call(["deactivate"])
            
            print("virtual environment deactivated.")
        except subprocess.CalledProcessError as e:
            print(f"error deactivating virtual environment: {e}")
    else:
        print("not currently in a virtual environment.")

def restart_keyboard_colors():
    command = "sudo systemctl restart keyboard-colors"
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("keyboard colors restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"error restarting keyboard colors: {e}")

if __name__ == "__main__":
    # create a new python environment 
    create_and_activate_venv()

    # find downloads folder 
    downloads_folder = get_downloads_folder()

    if downloads_folder:
        print(f"the downloads folder is: {downloads_folder}")

    # download the latest release 
    repo_owner = "withinboredom"
    repo_name = "system-76-keyboards"
    output_path = downloads_folder

    deb_file_name = download_latest_deb_release(repo_owner, repo_name, output_path)

    deb_file_path = os.path.join(downloads_folder, deb_file_name)

    install_deb_file(deb_file_path)

    # original file: https://github.com/withinboredom/system-76-keyboards/blob/master/csharp/keyboards/settings.json
    # located approx here on machine: /etc/keyboard-colors.json
    filepath = "/etc/"
    filename = "keyboard-colors.json"
    update_mode(filepath, filename)

    # restart keyboard service 
    # sudo systemctl restart keyboard-colors 
    restart_keyboard_colors()

    # end virtual environment 
    deactivate_virtual_environment()
