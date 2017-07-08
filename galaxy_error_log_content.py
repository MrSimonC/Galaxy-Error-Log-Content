from slackclient import SlackClient
from pyparsing import *
import datetime
import os
import shutil
import sys
import tempfile
__version__ = '1.1'
# v1.1 = updated slack calling

"""
Processes Galaxy Error Log, finding where c-code is missing from config
(Finished 13/Jul/16 - only finished after 2 days straight, when I gave up previously!)
Look for:
A05	Pre-admit a patient (=Access Plan Entry creation)
(A01	Admit/visit notification (=Admission/ED Create Attendance) - not all admissions are for Theatre, so don't use)
e.g. The Consultant [C6103187] Does Not Exist Within The Surgery Application.
"""


def _get_files(folder):
    return [os.path.join(folder, file) for file in os.listdir(folder) if os.path.isfile(os.path.join(folder, file))]


def most_recent_file(folder):
    """
    Returns most recently modified file with timestamp
    :param folder: folder to process
    :return: filename_full_path, dateobject
    """
    files = _get_files(folder)
    files_with_mod_dates = [[os.path.abspath(file),
                             datetime.datetime.fromtimestamp(os.path.getmtime(file))]  # modified date
                            for file in files]
    if not files_with_mod_dates:
        return None, None
    most_recent_file = files_with_mod_dates[0][0]
    most_recent_file_date = files_with_mod_dates[0][1]
    for file, mod_date in files_with_mod_dates:
        if mod_date > most_recent_file_date:
            most_recent_file = file
            most_recent_file_date = mod_date
    return most_recent_file, most_recent_file_date


def create_temporary_copy(path):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name.txt')
    shutil.copy2(path, temp_path)
    return temp_path


def slack_notify(message, me_only=False):
    s = SlackClient(os.environ['SLACK_LORENZOBOT'])
    if me_only:
        # IM me only
        simon_id = _slack_get_value(s.api_call('users.list'), 'Simon Crouch', 'real_name', 'id', 'members')
        user_dm_channel = _slack_get_value(s.api_call('im.list'), simon_id, 'user', 'id', 'ims')
        response = s.api_call('chat.postMessage', as_user=True, channel=user_dm_channel, text=message)
    else:
        # Back Office group
        response = s.api_call('chat.postMessage', as_user=True, channel='backoffice', text=message)
    if not response['ok']:
        return False
    return True


def _slack_get_value(slack_response, search_value, search_field, return_field, classifier):
    """
    Traverses a slack response to obtain a single value
    :param slack_response: json response from slackclient api_call
    :param search_value: value to search for
    :param search_field: field to search for the value in
    :param return_field: field who's value you want to return
    :param classifier: specific slack identifying string which is found in the slack_response e.g. 'groups'
    :return: string value
    """
    if not slack_response['ok']:
        return False
    for item in slack_response[classifier]:
        if search_field in item and search_value == item[search_field] and return_field in item:
            return item[return_field]


def process_error_log(path):
    ParserElement.setDefaultWhitespaceChars(' \t')  # set spaces and tabs as default whitespace characters

    word = Word(alphas)
    num = Word(nums)
    alpha_nums_symbols = Word(alphanums + "-'\/[]_=+!@£$%^&*().:,")  # like Pokemon - ensure you get them all
    EOL = LineEnd().suppress()
    SOL = LineStart().suppress()

    date_stamp = Combine(num + Literal('-') + word + Literal('-') + num)  # 14-sep-15 09:35:01:
    time_stamp = Combine(num + Literal(':') + num + Literal(':') + num + Suppress(Literal(':')))
    date_and_time = Combine(date_stamp + ' ' + time_stamp)
    date_and_time.setParseAction(lambda dates: datetime.datetime.strptime(dates[0], '%d-%b-%y %H:%M:%S'))
    segment = Combine(word + num)  # A03
    for_patient = Suppress((OneOrMore(word) + Literal(':')))  # for Patient:
    mrn = Group(OneOrMore(num) + Suppress(Literal('-')))  # 654321 -
    first_line = SOL + date_and_time('date_time') + segment('seg') + for_patient + mrn('mrn') + EOL

    merge = EOL + EOL + Literal('***End of Merge Message(s)***') + EOL
    error_line = originalTextFor(OneOrMore(alpha_nums_symbols)) + ZeroOrMore(merge) + EOL
    error_lines = OneOrMore(error_line)
    error = Group(first_line + OneOrMore(error_lines('error')) + OneOrMore(EOL))  # this requires end of file has a new line
    errors = OneOrMore(error)

    result = errors.parseString(open(path).read())
    output = []
    for result in result:
        if result.seg == 'A05':  # or result.seg == 'A01': # removed as patient still created, and not all admissions need theatre
            # print(result)
            # print(result.error[0])
            consultant_code = Suppress(Literal('[')) + Word(alphanums) + Suppress(Literal(']'))
            consultant_error_line = Optional(OneOrMore(word) + consultant_code('c_code') + OneOrMore(word)
                                            + ZeroOrMore(Literal('.')))
            if result.error:
                consultant_error = consultant_error_line.parseString(result.error[0])
                # print(consultant_error)
                if consultant_error:
                    error_type = 'Access Plan Entry' if result.seg == 'A05' else 'Admission'  # will always be A05
                    output.append('Galaxy C-Code Missing: {code} for Patient MRN: {mrn} ({error_type})'.format(
                        code=consultant_error.c_code[0], mrn=result.mrn[0], error_type=error_type))
    return output

if __name__ == '__main__':
    # -t = send test direct message to Simon Crouch
    try:
        if sys.argv[1] == '-t':
            slack_notify('Test message from slack_lorenzobot.py', True)
            sys.exit(0)
    except IndexError:
        pass

    # ***Process live error log***
    # copy to temp file, find c-code errors, if not already alerted, tell slack and record for later
    if hasattr(sys, 'frozen'):
        this_module = os.path.dirname(sys.executable)
    else:
        this_module = os.path.dirname(os.path.realpath(__file__))
    previous_errors_file = 'galaxy_error_log_content_previous_errors.txt'
    previous_errors_path = os.path.join(this_module, previous_errors_file)

    # Testing:
    # live_folder = r'C:\auto_delete'
    live_folder = r'\\nbsvr139\SFTP\GalaxyConfig\LIVE'

    print('Checking folder')
    live_file = most_recent_file(live_folder)
    print(live_file)
    temp_file = create_temporary_copy(live_file[0])
    list_of_c_code_errors = process_error_log(temp_file)
    print(list_of_c_code_errors)
    all_previous_errors = open(previous_errors_path).read()
    if list_of_c_code_errors:
        for each_error in list_of_c_code_errors:
            if each_error not in all_previous_errors:
                # Testing:
                # slack_notify(each_error, True)
                slack_notify(each_error)
                with open(previous_errors_path, 'a', newline='') as file_out:
                    file_out.writelines(each_error)
    os.remove(temp_file)
