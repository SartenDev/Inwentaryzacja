import platform
import os
system_name = platform.system()

if system_name == 'Windows':
    os.system("pip install windows_tools")
    from windows_tools.installed_software import get_installed_software
    for software in get_installed_software():
        print(software['name'], "\t", software['version'], "\t", software['publisher'])
elif system_name == 'Darwin':
    import os

    output = os.popen("find / -iname *.app").read()
    print(output)
else:
    import subprocess
    print(subprocess.run("apt-mark showmanual", capture_output=True, text=True))