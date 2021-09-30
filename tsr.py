# This code is based on tutorial by slicktechies modified as needed to use oauth token from Twitch.
# You can read more details at: https://www.junian.net/2017/01/how-to-record-twitch-streams.html
# original code is from https://slicktechies.com/how-to-watchrecord-twitch-streams-using-livestreamer/

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
        # You get your Client-ID with: curl -X GET 'https://id.twitch.tv/oauth2/validate' -H 'Authorization: Bearer OAUTH_TOKEN'
        #self.client_id = "ADD_CLIENT_ID_HERE" 
        #self.oauth_token = "ADD_OAUTH_TOKEN_HERE"
        self.ffmpeg_path = 'ffmpeg'
        self.refresh = 15.0
        self.root_path = "/home/..."

        # user configuration
        self.username = "ADD_STREAMER"
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

        print("Checking for", self.username, "every", self.refresh, "seconds. Record with", self.quality, "quality.")
        self.loopcheck()


    def loopcheck(self):
        while True:
            print(self.username, "checking if Stream is online and starting recording.")
            filename = self.username + " - " + datetime.datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss") + ".mp4"

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
    usage_message = 'twitch-recorder.py -u <username> -q <quality>'

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
