# Twitch Stream Recorder (tsr.py)
#
# Version: 1.1.0
#
# Developed by: DravenTec
#
# Based on the script by junian https://gist.github.com/junian/b41dd8e544bf0e3980c971b0d015f5f6, 
# this code has been further modified to use Twitch oauth token. You can read more details about
# the original tutorial at: https://www.junian.net/2017/01/how-to-record-twitch-streams.html
#
# The script has been further modified to use the twitch-cli and added a processing of video files 
# as a thread for faster starting of the recorder in case of stream problems, as there is no need 
# to wait for video file processing. The video files are also directly adjusted to the "faststart" 
# video option.
#

import requests
import os
import time
import json
import sys
import subprocess
import datetime
import getopt
import threading

class TwitchRecorder:
    def __init__(self):
        # global configuration
        #
        # Default: ffmpeg
        # If ffmpeg is not defined globally please specify the appropriate path
        self.ffmpeg_path = 'ffmpeg'
        #
        # Default: /home/linuxbrew/.linuxbrew/bin/twitch
        # If the installation instructions of Twitch-Cli were followed, the path does not need to be adjusted.
        self.twitch_path = '/home/linuxbrew/.linuxbrew/bin/twitch'
        #
        # Default: 15
        # Minimum value for checking if a streamer is online is 15 seconds, 
        # values below that are automatically set to 15 regardless of the entered value.
        self.refresh = 15.0
        
        # Recording folder
        self.root_path = "/media/daten/recorder"
        
        # Default settings when the script is executed without arguments
        #
        # Username corresponds to the streamers name, the name must be lowercase
        # Standard quality in which, the stream should be recorded
        # Quality Options: best, high, medium, low, mobile
        self.username = "diedoni"
        self.quality = "best"
    
    def fix_video_file(self, recorded_filename, processed_path, ffmpeg_path, filename):
        print("Repairing the video file if necessary and moving the moov atom header for quick start...")
        if(os.path.exists(recorded_filename) is True):
            try:
                subprocess.call([ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', '-movflags', 'faststart', os.path.join(self.processed_path,filename)])
                os.remove(recorded_filename)
            except Exception as e:
                print(e)
        else:
            print("Skip fixing. File not found.")
    
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
                try:
                    thread = threading.Thread(target=self.fix_video_file, args=(recorded_filename, self.processed_path, self.ffmpeg_path, f))
                    thread.start()
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
                subprocess.call(["streamlink", "--twitch-api-header", "Client-ID=ue6666qo983tsx6so1t0vnawi233wa", "--twitch-disable-hosting", "--twitch-disable-ads", "twitch.tv/" + self.username, self.quality, "-o", recorded_filename])

                print("Recording stream is done. Repairing the video file if necessary and moving the moov atom header for a quick start .")
                if(os.path.exists(recorded_filename) is True):
                    try:
                        thread = threading.Thread(target=self.fix_video_file, args=(recorded_filename, self.processed_path, self.ffmpeg_path, filename))
                        thread.start()
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
