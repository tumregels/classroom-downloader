import glob
import logging
import os
import textwrap
import zipfile

import rarfile
from tabulate import tabulate


def find_all_html_files(directory):
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.abspath(os.path.join(root, file))
                p('---------------')
                p(file_path)
                html_files.append(file_path)
    return html_files


def unzip(xpath):
    for file_zip in glob.glob('{}/*.zip'.format(xpath)):
        zip_ref = zipfile.ZipFile(file_zip, 'r')
        # p(*zip_ref.namelist())
        for libitem in zip_ref.namelist():
            if not (libitem.startswith('__MACOSX/') or '.git/' in libitem or 'node_modules/' in libitem):
                zip_ref.extract(libitem, path=xpath)
        # zip_ref.extractall(new_path)
        zip_ref.close()


def unrar(xpath):
    for file_rar in glob.glob('{}/*.rar'.format(xpath)):
        # filepath = os.path.join(dpath, file_rar)
        with rarfile.RarFile(file_rar) as rar_ref:
            # for f in rar_ref.infolist():
            #     print (f.filename, f.file_size)
            rar_ref.extractall(xpath)


def extract_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".zip") or file.endswith(".rar"):
                file_path = os.path.join(root, file)
                p('---------------')
                p('Unzipping:', file_path)
                try:
                    if file.endswith(".zip"):
                        unzip(root)
                    elif file.endswith(".rar"):
                        unrar(root)
                except Exception as e:
                    logger.error(e)


def p(*args):
    """print and log at once"""
    if not args: return

    message = ' '.join(args) if len(args) > 1 else args[0]
    print(message.encode('utf-8'))
    logger.info(message)


def show_course_works(course_id, course_works, title=''):
    if not course_works:
        return

    table_data = [[
        textwrap.fill('assignment ids for {} {}'.format(course_id, title), width=45),
        'assignment title',
        'assignment description'
    ]]

    for cw in course_works:
        table_data.append([
            cw.get('id', ''),
            textwrap.fill(cw.get('title', ''), width=45),
            textwrap.fill(cw.get('description', ''), width=45)
        ])

    table = os.linesep + tabulate(table_data, headers="firstrow", tablefmt="simple") + os.linesep
    p(table)


def show_courses(courses):
    table_data = [['course id', 'course name', 'course description', 'course title']]

    for c in courses:
        table_data.append([
            c.get('id', ''),
            textwrap.fill(c.get('name', ''), width=45),
            textwrap.fill(c.get('description', ''), width=45),
            textwrap.fill(c.get('title', ''), width=45)
        ])

    p(os.linesep + tabulate(table_data, headers="firstrow", tablefmt="simple") + os.linesep)


logging.basicConfig(
    filename='log.txt',
    filemode='w',
    format='%(asctime)s: %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

# uncomment this line to print logs in console
# logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)
