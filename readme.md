# Galaxy Error Log Content
Made for North Bristol Trust Back Office Team, whilst working as a Senior Clinical Systems Analyst.

## Background
Interface (between CSC Lorenzo and Galaxy) error monitoring system which observes errors, then informs Back Office team via Slack.

The program processes CSC Galaxy Theatres System error log for Lorenzo Access Plan entries where the clinician ID is missing and results in an error (and therefore won't be created in Galaxy).

## Prerequisite
Install "Visual C++ Redistributable for Visual Studio 2015 x86.exe" (on 32-bit, or x64 on 64-bit) which allows Python 3.5 dlls to work, found here:
https://www.microsoft.com/en-gb/download/details.aspx?id=48145

## Installation and Running
Make a folder in "C:\Program Files\Galaxy Error Log Content" (or another location of you choice) and put all the following files in there:
- Galaxy Error Log Content.xml
- galaxy_error_log_content.exe
- galaxy_error_log_content_previous_errors.txt

In Windows Task Scheduler, Import Task, choose the .xml file, then change the "Run only when user is logged on" username to your own.
OR create a new task with the following attributes:
- General: Run only when user is logged on
- Trigger: at 8am everyday, repeat every 10 minutes indefinitely
- Actions: Start a program: "C:\Program Files\Galaxy Error Log Content\galaxy_error_log_content.exe"
    - Start in (optional): C:\Program Files\Galaxy Error Log Content
- Settings:
    - Allow ask to be run on demand
    - Stop the task if it runs longer than: 3 days
    - If the running task does not end when requested, force it stop
    - If the task is already running, then the following rule applies: Stop the existing instance

## Notes
### Explorer
The user whom this program is run under MUST have read access to folder: `\\nbsvr139\SFTP\GalaxyConfig\LIVE`

### SDPlus API
This program communicates with the sdplus API via an sdplus api technician key which can be obtained via the sdplus section: Admin, Assignees, Edit Assignee (other than yourself), Generate API Key.
This program will look for an API key in a windows variable under name "SDPLUS_ADMIN". You can set this on windows with:
`setx SDPLUS_ADMIN <insert your own SDPLUS key here>`
in a command line.
In a command prompt, type:
`echo %SDPLUS_ADMIN%`
to check it exists.

### Slack
This program communicates with slack API via an API Token which can be obtained by: https://it-nbt.slack.com/services/B1FCFC4RL (or Browse Apps  > Custom Integrations  > Bots  > Edit configuration)  
This program will look for an API key in a windows variable under name "SLACK_LORENZOBOT". You can set this on windows with:
`setx SLACK_LORENZOBOT <insert your own SDPLUS key here>`
in a command line.
In a command prompt, type:
`echo %SLACK_LORENZOBOT%`
to check it exists.

Written by:
Simon Crouch, late 2016 in Python 3.5