#
# Twitch-Stream-Recorder
#
# Version adapted by Draventec to work with the new Twitch API
#
# Original by junian https://gist.github.com/junian/b41dd8e544bf0e3980c971b0d015f5f6
# This code is based on tutorial by slicktechies modified as needed to use oauth token from Twitch.
# You can read more details at: https://www.junian.net/2017/01/how-to-record-twitch-streams.html

import requests
import os
import time
import json
import sys
import subprocess
import datetime
import getopt

class TwitchRecorder:
    def __init__(self):
        # global configuration
        self.ffmpeg_path = 'ffmpeg'
        self.twitch_path = '/home/linuxbrew/.linuxbrew/bin/twitch'
        self.refresh = 15.0
        self.root_path = "/media/daten/recorder"

        # user configuration
        self.username = "diedoni"
        self.quality = "best"

    def run(self):
        # path to recorded stream
        self.recorded_path = os.path.join(self.root_path, "recorded", self.username)

        # path to finished video, errors removed
        self.processed_path = os.path.join(self.root_path, "processed", self.username)

        # create directory for recordedPath and processedPath if not exist
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        # make sure the interval to check user availability is not less than 15 seconds
        if(self.refresh < 15):
            print("Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print("System set check interval to 15 seconds.")

        # fix videos from previous recording session
        try:
            video_list = [f for f in os.listdir(self.recorded_path) if os.path.isfile(os.path.join(self.recorded_path, f))]
            if(len(video_list) > 0):
                print('Fixing previously recorded files.')
            for f in video_list:
                recorded_filename = os.path.join(self.recorded_path, f)
                print('Fixing ' + recorded_filename + '.')
                try:
                    subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', os.path.join(self.processed_path,f)])
                    os.remove(recorded_filename)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
        proc = subprocess.Popen([self.twitch_path, "api", "get", "users", "-q", "login=" + self.username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        data_user, data_err = proc.communicate()
        info_user = json.loads(data_user)
        if 'id' in str(info_user):
            print("Checking for", self.username, "every", self.refresh, "seconds. Record with", self.quality, "quality.")
            self.loopcheck()
        else:
            print("Username not found. Invalid username or typo.")
            
    def check_user(self):
        # 0: online,
        # 1: offline,
        # 2: not found,
        # 3: error
        info = None
        status = 3
        try:
            proc = subprocess.Popen([self.twitch_path, "api", "get", "streams", "-q", "user_login=" + self.username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            data, err = proc.communicate()
            info = json.loads(data)
            if 'type' in str(info):
             status = 0
            else:
             status = 1
            if ('type' not in info):
             for element in info['data']:
                if element['type'] == "live":
                  status = 0
                else:
                  status = 1
        except subprocess.CalledProcessError as e:
            if e == 'Not Found' or e == 'Unprocessable Entity':
                status = 3
        return status, info

    def loopcheck(self):
        while True:
            status, info = self.check_user()
            if status == 3:
                print(datetime.datetime.now().strftime("%Hh%Mm%Ss")," ","unexpected error. will try again in 5 minutes.")
                time.sleep(300)
            elif status == 1:
                print(self.username, "currently offline, checking again in", self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 0:
                print(self.username, "online. Stream recording in session.")
                filename = self.username + " - " + datetime.datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss") + " - " + info['data'][0]['title'] + ".mp4"

                # clean filename from unecessary characters
                filename = "".join(x for x in filename if x.isalnum() or x in [" ", "-", "_", "."])

                recorded_filename = os.path.join(self.recorded_path, filename)

                # start streamlink process
                subprocess.call(["streamlink", "--twitch-disable-hosting", "--twitch-disable-ads", "twitch.tv/" + self.username, self.quality, "-o", recorded_filename])

                print("Recording stream is done. Fixing video file.")
                if(os.path.exists(recorded_filename) is True):
                    try:
                        subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', os.path.join(self.processed_path, filename)])
                        os.remove(recorded_filename)
                    except Exception as e:
                        print(e)
                else:
                    print("Skip fixing. File not found.")

                print("Fixing is done. Going back to checking..")
                time.sleep(self.refresh)

def main(argv):
    twitch_recorder = TwitchRecorder()
    usage_message = 'tsr.py -u <username> -q <quality>'

    try:
        opts, args = getopt.getopt(argv,"hu:q:",["username=","quality="])
    except getopt.GetoptError:
        print (usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-u", "--username"):
            twitch_recorder.username = arg
        elif opt in ("-q", "--quality"):
            twitch_recorder.quality = arg

    twitch_recorder.run()

if __name__ == "__main__":
    main(sys.argv[1:])
