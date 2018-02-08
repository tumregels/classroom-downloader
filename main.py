from __future__ import print_function, unicode_literals

import io
import os
import os.path as op
import sys
import textwrap
from random import randint
from time import sleep

import httplib2
import tqdm
from apiclient import discovery
from apiclient.errors import HttpError
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

from utils import logger, extract_all_files, show_courses, show_course_works, p

__version__ = "0.1.3"

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/classroom.googleapis.com-python-quickstart.json
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/classroom.profile.emails',
    'https://www.googleapis.com/auth/classroom.rosters',
    'https://www.googleapis.com/auth/drive.readonly'
]

CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Classroom API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'classroom.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        p('Storing credentials to ' + credential_path)
    return credentials


def download_drivefile(file_id, file_name):
    if os.path.isfile(file_name):  # continue if exists
        return

    try:
        request = drive_service.files().get_media(fileId=file_id)
    except:  # download as pdf
        request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
        file_name = file_name + '.pdf'
        if os.path.isfile(file_name): return  # continue if exists

    sleep(randint(10, 20))  # avoid google api limit

    fh = io.FileIO(file_name, mode='wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    pbar = tqdm.tqdm(total=100)  # progress bar
    try:
        while done is False:
            status, done = downloader.next_chunk(num_retries=5)
            pbar.update(int(status.progress() * 100))
    except KeyboardInterrupt:
        fh.flush()  # cleanup download files
        fh.close()
        os.remove(file_name)
        p('Download Interrupted')
        raise KeyboardInterrupt
    except HttpError as e:
        io.open(file_name + '.log.txt', mode='wb').write(e.content)
        logger.error(e)
        # raise e
    finally:
        pbar.close()


def download_attachments(attachments, down_path, email, full_name):
    for attachment in attachments:
        if 'driveFile' in attachment:
            file_id = attachment.get('driveFile').get('id')

            file_name = attachment.get('driveFile').get('title')
            # file_ext = os.path.splitext(file_name)[1]
            # file_name = os.path.join(full_name, email + file_ext)
            full_file_name = os.path.join(down_path, email, full_name, file_name)
            p(full_file_name)
            download_drivefile(file_id, full_file_name)
        elif 'link' in attachment:
            link_file = os.path.join(down_path, email, full_name, 'link.txt')
            with io.open(link_file, mode='ab') as f:
                f.write(attachment['link']['url'] + '\n')


def download_assignment(course_id, course_work_id, down_path='downloads'):
    studentSubmissions = classroom_service.courses().courseWork().studentSubmissions().list(
        courseId=course_id,
        courseWorkId=course_work_id).execute()

    if not os.path.exists(down_path):
        os.makedirs(down_path)

    sub_list = []

    for studentSubmission in studentSubmissions.get('studentSubmissions'):
        if bool(studentSubmission.get('assignmentSubmission')):
            userId = studentSubmission.get('userId')
            userProfile = classroom_service.userProfiles().get(userId=userId).execute()

            email = userProfile.get('emailAddress').split('@')[0]

            full_name = userProfile.get('name').get('fullName')  # .replace(' ', '-')
            line = full_name + ' ( ' + email + '@tumo.org ) - \n'
            sub_list.append(line)
            # full_name = os.path.join(down_path, email)
            if not op.exists(op.join(down_path, email, full_name)):
                os.makedirs(op.join(down_path, email, full_name))
            p('--------------')
            p(userProfile.get('emailAddress'), userProfile.get('name').get('fullName'))
            attachments = studentSubmission.get('assignmentSubmission').get('attachments')
            download_attachments(attachments, down_path, email, full_name)

    extract_all_files(down_path)

    with io.open('submissions.txt', 'w', encoding='utf-8') as sfile:
        for line in sorted(sub_list):
            sfile.write(line)


def get_courses():
    courses = []
    page_token = None

    while True:
        response = classroom_service.courses().list(pageToken=page_token,
                                                    pageSize=100).execute()
        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
    return courses


def get_course_works(course_id):
    course_works = []
    page_token = None

    response = classroom_service.courses().courseWork().list(
        pageToken=page_token,
        pageSize=100,
        courseId=course_id).execute()

    while True:
        course_works.extend(response.get('courseWork', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return course_works


def cli():

    courses = get_courses()
    show_courses(courses)

    course_ids = [c.get('id') for c in courses]
    course_meta = {c['id']: c.get('name', '') + ' ' + c.get('description', '') for c in courses}
    course_completer = WordCompleter(
        words=course_ids,
        meta_dict=course_meta,
        ignore_case=True)

    course_id = prompt('Enter classroom id: ',
                       completer=course_completer,
                       get_bottom_toolbar_tokens=lambda cli: [(Token.Toolbar,
                                                               'Press repeatedly TAB key to choose from the list of classrooms')],
                       style=style_from_dict({Token.Toolbar: '#ffffff bg:#333333'}),
                       display_completions_in_columns=True)

    course_works = get_course_works(course_id)
    show_course_works(course_id, course_works)
    course_work_ids = [cw['id'] for cw in course_works]

    if not course_work_ids:
        p(os.linesep + 'There are no assignments in this classroom. Exiting ...')
        return

    course_work_meta = {cw['id']: cw.get('title', '') + ' ' + cw.get('description', '') \
                        for cw in course_works}

    course_work_completer = WordCompleter(
        words=course_work_ids,
        meta_dict=course_work_meta,
        ignore_case=True)

    course_work_id = prompt('Enter assignment id: ',
                            completer=course_work_completer,
                            get_bottom_toolbar_tokens=lambda cli: [(Token.Toolbar,
                                                                    'Press repeatedly TAB key to choose from the list of assignments')],
                            style=style_from_dict({Token.Toolbar: '#ffffff bg:#333333'}),
                            display_completions_in_columns=True)

    download_message = 'You have chosen to download assignment "{}" from course "{}"'.format(
        course_work_meta[course_work_id], course_meta[course_id])
    download_message = os.linesep + textwrap.fill(download_message, width=45) + os.linesep
    p(download_message)
    answer = confirm('Should we do that? (y/n) ')

    if answer:
        download_assignment(course_id, course_work_id)


if __name__ == '__main__':

    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        bundle_dir = sys._MEIPASS
        cwd = op.dirname(sys.executable)
    else:
        # we are running in a normal Python environment
        bundle_dir = op.dirname(op.abspath(__file__))
        cwd = bundle_dir

    os.chdir(cwd)

    p("Executing classroom-downloader version {}".format(__version__))
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    classroom_service = discovery.build('classroom', 'v1', http=http, cache_discovery=False)
    drive_service = discovery.build('drive', 'v3', http=http, cache_discovery=False)

    try:
        cli()
    except KeyboardInterrupt:
        p('Exiting classroom-downloader. Bye!')
        sys.exit()

        # courses = get_courses()
        # show_courses(courses)
        # course_works = get_course_works(course_id='5088423307')
        # show_course_works(course_id='5088423307', course_works)
        # download_assignment(course_id='5088423307', course_work_id='7944623829') # prog III SK

    # extract_all_files('downloads-sk-sep-2017')