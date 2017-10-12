from __future__ import print_function

import io
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

from utils import *

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
    if os.path.isfile(file_name): # continue if exists
       return
    sleep(randint(10, 20))  # avoid google api limit

    if file_name.lower().endswith(('.zip','.rar','.7z')):
        request = drive_service.files().get_media(fileId=file_id)
    else: # download as pdf
        request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
        file_name = file_name + '.pdf'

    fh = io.FileIO(file_name, mode='wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    pbar = tqdm.tqdm(total=100)  # progress bar
    try:
        while done is False:
            status, done = downloader.next_chunk(num_retries=5)
            pbar.update(int(status.progress() * 100))
    except HttpError as e:
        io.open(file_name + '.log.txt', mode='wb').write(e.content)
        logger.error(e)
        # raise e
    finally:
        pbar.close()


def download_attachments(attachments, full_name, email):
    for attachment in attachments:
        if 'driveFile' in attachment:
            file_id = attachment.get('driveFile').get('id')

            file_name = attachment.get('driveFile').get('title')
            file_ext = os.path.splitext(file_name)[1]
            file_name = os.path.join(full_name, email + file_ext)
            p(file_name)
            download_drivefile(file_id, file_name)
        elif 'link' in attachment:
            link_file = os.path.join(full_name, 'link.txt')
            with open(link_file, 'a') as f:
                f.write(attachment['link']['url'] + '\n')


def download_assignment(courseId, courseWorkId, spath='downloads'):
    studentSubmissions = classroom_service.courses().courseWork().studentSubmissions().list(
        courseId=courseId,
        courseWorkId=courseWorkId).execute()

    if not os.path.exists(spath):
        os.makedirs(spath)

    sub_list = []

    for studentSubmission in studentSubmissions.get('studentSubmissions'):
        if bool(studentSubmission.get('assignmentSubmission')):
            userId = studentSubmission.get('userId')
            userProfile = classroom_service.userProfiles().get(userId=userId).execute()

            email = userProfile.get('emailAddress').split('@')[0]

            full_name = userProfile.get('name').get('fullName')  # .replace(' ', '-')
            line = full_name + ' ( ' + email + '@tumo.org ) - \n'
            sub_list.append(line)
            full_name = os.path.join(spath, full_name)
            if not os.path.exists(full_name):
                os.makedirs(full_name)
            p('--------------')
            p(userProfile.get('emailAddress'), userProfile.get('name').get('fullName'))
            attachments = studentSubmission.get('assignmentSubmission').get('attachments')
            download_attachments(attachments, full_name, email)

    extract_all_files(spath)

    with io.open('submissions.txt', 'w', encoding='utf-8') as sfile:
        for line in sorted(sub_list):
            sfile.write(line)


def show_courses():
    courses = []
    page_token = None

    while True:
        response = classroom_service.courses().list(pageToken=page_token,
                                                    pageSize=100).execute()
        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    if not courses:
        p('No courses found.')
    else:
        p('Courses:')
        for course in courses:
            p(u'{0} - ({1}) - {2} - {3}'.format(
                course.get('name'),
                course.get('id'),
                course.get('description'),
                course.get('title')
            ))
    return courses


def show_assignments(courseId):
    course_works = []
    page_token = None

    response = classroom_service.courses().courseWork().list(
        pageToken=page_token,
        pageSize=100,
        courseId=courseId).execute()

    while True:
        course_works.extend(response.get('courseWork', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    if not course_works:
        p('No course works found.')
    else:
        p('CourseWorks:')
        for cw in course_works:
            p(u'{0} - ({1}) - {2}'.format(
                cw.get('title'),
                cw.get('id'),
                cw.get('description'),
            ))


if __name__ == '__main__':
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    classroom_service = discovery.build('classroom', 'v1', http=http, cache_discovery=False)
    drive_service = discovery.build('drive', 'v3', http=http, cache_discovery=False)

    # show_courses()
    # show_assignments(courseId='5088423307')
    # prog III SK
    download_assignment(courseId='5088423307', courseWorkId='7944623829')
