# URL Processing:
import requests


def link_manager(url):
    # Check if URL is valid
    try:
        r = requests.get(url)
    except requests.exceptions.MissingSchema:
        return -1
    except requests.exceptions.InvalidSchema:
        return -1
    except requests.exceptions.InvalidURL:
        return -1

    # Check headers for size, cancel operation if larger than 50mb
    try:
        size = int(r.headers['content-length'])
        if size > 50e6:
            print('File too large...')
            return -1
    except (ValueError, KeyError):
        print('Error when parsing file size, continuing anyway...')

    # Check if URL is active
    if r.status_code != 200:
        print('Invalid status, aborting...')
        return -1

    print('URL passed validity tests...')
    # Construct file name using headers, could find the filename but if not make our own
    try:
        file_name = r.headers['filename']
    except KeyError:
        try:
            file_name = r.headers['content-type']
            file_name = file_name[file_name.find('/') + 1:]
            file_name = 'file.' + file_name
        except KeyError:
            return -1

    # Write the contents of the webpage to a local file and return the raw bytes
    with open(file_name, 'wb') as wb:
        wb.write(r.content)
    out_rb = open(file_name, 'rb')
    return out_rb
