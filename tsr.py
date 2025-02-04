# -*- coding: utf-8 -*-

# Twitch Stream Recorder (tsr.py)
#
# Version: 04.02.2025-2220
# Developed by: DravenTec

import requests
import os
import time
import json
import sys
import subprocess
import datetime
import getopt
import threading
import shutil

class TwitchStreamRecorder:
    def __init__(self):

        # Global configuration

        # Please specify the folder where the recordings should be stored
        # Example: /home/username/recording/
        self.root_path = "/recording/"

        # Default settings when the script is executed without arguments
        # Username corresponds to the streamers name, the name must be lowercase
        self.username = ""
        # Standard quality in which, the stream should be recorded
        # Quality Options: audio_only, best, high, medium, low, mobile
        self.quality = "best"

        # Quality Settings for audio convert
        # MP3 Quality: 0 (highest) to 10 (lowest)
        self.mp3_quality = '2'
        # OGG Quality: 0 (lowest) to 10 (highest)
        self.ogg_quality = '5'

        # Default: streamlink
        # If Streamlink is running in a virtual environment, please specify the path to it.
        self.streamlink = 'streamlink'

        # Default: ffmpeg
        # If ffmpeg is not defined globally please specify the appropriate path
        self.ffmpeg_path = 'ffmpeg'

        # Default: --twitch-api-header Client-ID=ue6666qo983tsx6so1t0vnawi233wa --twitch-disable-hosting --twitch-disable-ads
        # Streamlink running arguments
        self.streamlink_arg = '--twitch-api-header Client-ID=ue6666qo983tsx6so1t0vnawi233wa --twitch-disable-hosting --twitch-disable-ads'

        # Default: /home/linuxbrew/.linuxbrew/bin/twitch
        # If the installation instructions of Twitch-Cli were followed, the path does not need to be adjusted.
        self.twitch_path = '/home/linuxbrew/.linuxbrew/bin/twitch'

        # Default: 15.0
        # Minimum value for checking if a streamer is online is 15 seconds,
        # values below that are automatically set to 15 regardless of the entered value.
        self.refresh = 15.0

        # For file post-processing
        self.quality_suffixes = ['_audioonly', '_best', '_high', '_medium', '_low', '_mobile']
        self.valid_qualities = ['best', 'high', 'medium', 'low', 'mobile', 'audio_only']
        self.valid_audio = ['mp3', 'ogg', 'aac']
        self.audio = ""
        self.savefile = "yes"

    def fix_video_file(self, recorded_filename, filename):
        print(f"Processing file: {filename}")
        try:
            quality, cleaned_filename = self.get_quality_from_filename(filename)
            if quality == 'audioonly':
                self.process_audio_file(recorded_filename, cleaned_filename, filename)
            else:
                self.process_video_file(recorded_filename, cleaned_filename, filename)
        except subprocess.CalledProcessError as e:
                        print(f"Error during video repair/convert: {e.returncode}")
                        print(f"Standard error output: {e.stderr}")
                        print(f"Standard output: {e.stdout}")
        except Exception as e:
            print(f"Error during file processing: {e}")

    def process_audio_file(self, recorded_filename, cleaned_filename, filename):
        if self.audio in self.valid_audio:
            self.audio_convert(recorded_filename, cleaned_filename)
            if self.savefile == 'yes':
                original_aac_filename = cleaned_filename.replace(".ts", ".aac")
                shutil.move(recorded_filename, os.path.join(self.processed_path, original_aac_filename))
            else:
                os.remove(recorded_filename)
        else:
            new_filename = cleaned_filename.replace(".ts", ".aac")
            shutil.move(recorded_filename, os.path.join(self.processed_path, new_filename))
            print(f"Audio file {filename} renamed to {new_filename} and moved to processed folder.")


    def process_video_file(self, recorded_filename, cleaned_filename, filename):
        if self.audio in self.valid_audio:
            self.audio_convert(recorded_filename, cleaned_filename)
            if self.savefile == 'no':
                os.remove(recorded_filename)
            else:
                self.video_check(recorded_filename, cleaned_filename, filename)
        else:
            self.video_check(recorded_filename, cleaned_filename, filename)


    def video_check(self,recorded_filename,cleaned_filename,filename):
        new_filename = cleaned_filename.replace(".ts", ".mp4")
        ffmpeg_video = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', '-movflags', 'faststart', os.path.join(self.processed_path, new_filename)]
        subprocess.run(ffmpeg_video, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        os.remove(recorded_filename)
        print(f"Video file {filename} repaired, converted to {new_filename} and moved to processed folder.")
            
    def audio_convert(self,recorded_filename,cleaned_filename):
        new_filename = cleaned_filename.replace(".ts", f".{self.audio}")
        ffmpeg_audio =[]
        if self.audio == 'mp3':
            ffmpeg_audio = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-codec:a', 'libmp3lame', '-qscale:a', self.mp3_quality, os.path.join(self.processed_path, new_filename)]
        if self.audio == 'ogg':
            ffmpeg_audio = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-codec:a', 'libvorbis', '-qscale:a', self.ogg_quality, os.path.join(self.processed_path, new_filename)]
        if self.audio == 'aac':
            ffmpeg_audio = [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', recorded_filename, '-vn', '-acodec', 'copy', os.path.join(self.processed_path, new_filename)]
        subprocess.run(ffmpeg_audio, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        print(f"Audio file converted to {self.audio} renamed to {new_filename} and moved to processed folder.")
            
    def get_quality_from_filename(self, filename):
        quality = 'best'
        for suffix in self.quality_suffixes:
            if suffix in filename:
                quality = suffix.strip('_')
                filename = filename.replace(suffix + '.ts', '.ts')
                break
        return quality, filename

    def run(self):
        if not self.username:
           self.username = input(f"Please specify a streamer (lowercase): ")
        if not self.username:
            print(f"No streamer specified. Exiting program.")
            sys.exit()

        self.recorded_path = os.path.join(self.root_path, "recorded", self.username)
        self.processed_path = os.path.join(self.root_path, "processed", self.username)
        os.makedirs(self.recorded_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)

        if(self.refresh < 15):
            print(f"Check interval should not be lower than 15 seconds.")
            self.refresh = 15
            print(f"System set check interval to 15 seconds.")

        try:
            video_list = [f for f in os.listdir(self.recorded_path) if os.path.isfile(os.path.join(self.recorded_path, f))]
            if(len(video_list) > 0):
                print(f"Fixing previously recorded files.")
            for f in video_list:
                recorded_filename = os.path.join(self.recorded_path, f)
                try:
                    thread = threading.Thread(target=self.fix_video_file, args=(recorded_filename, f))
                    thread.start()
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

        try:
            twcli_usercheck = [self.twitch_path, "api", "get", "users", "-q", f"login={self.username}"]
            usercheck = subprocess.run(twcli_usercheck, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            user_data = usercheck.stdout
            user_err = usercheck.stderr
            if usercheck.returncode != 0:
                print(f"Error executing Twitch API command: {user_err}")
            else: 
                info_user = json.loads(user_data)
                if 'id' in info_user.get('data',[{}])[0]:
                    print(f"Checking for {self.username} every {self.refresh} seconds. Record with {self.quality} quality.")
                    running = True
                    try:
                        while running:
                            try:
                                self.loopcheck()
                            except KeyboardInterrupt:
                                running = False
                    except Exception as e:
                            print(f"An error occurred: {e}")
                    finally:
                        print(f"Twitch Stream Recorder... closeing.")
                else:
                    print(f"Username not found. Invalid username or typo.")
        except Exception as e:
            print (f"Error calling Twitch API: {e}")

    def check_user(self):
        info = None
        status = 3
        try:
            twcli_streamcheck = [self.twitch_path, "api", "get", "streams", "-q", f"user_login={self.username}"]
            streamcheck = subprocess.run(twcli_streamcheck, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stream_data = streamcheck.stdout
            stream_err = streamcheck.stderr
            if streamcheck.returncode != 0:
                print(f"Error executing Twitch API command: {stream_err}")
            else:
                info = json.loads(stream_data)
                if 'data' in info and len(info['data']) > 0 and info['data'][0].get('type') == 'live':
                    status = 0
                else:
                    status = 1
                        
        except subprocess.CalledProcessError as e:
            if 'Not Found' in str(e) or 'Unprocessable Entity' in str(e):
                status = 2
            else:
                status = 3
        return status, info

    def loopcheck(self):
        status, info = self.check_user()
        if status == 3:
            print(f"{datetime.datetime.now().strftime('%Hh%Mm%Ss')} unexpected error. will try again in 5 minutes.")
            time.sleep(300)
        elif status == 1:
            print(f"{self.username} currently offline, checking again in {self.refresh} seconds.")
            time.sleep(self.refresh)
        elif status == 0:
            print(f"{self.username} online. Stream recording starting...")
            if self.quality == 'audio_only':
                filename = f"{self.username} - {datetime.datetime.now().strftime('%Y-%m-%d %Hh%Mm%Ss')} - {info['data'][0]['title']}_audioonly.ts"
            else:
                filename = f"{self.username} - {datetime.datetime.now().strftime('%Y-%m-%d %Hh%Mm%Ss')} - {info['data'][0]['title']}_{self.quality}.ts"
            filename = "".join(x for x in filename if x.isalnum() or x in [" ", "-", "_", "."])
            recorded_filename = os.path.join(self.recorded_path, filename)

            try:
                streamlink_record = [self.streamlink] + self.streamlink_arg.split() + ["twitch.tv/" + self.username, "--default-stream", self.quality, "-o", recorded_filename]
                subprocess.run(streamlink_record, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during streamlink recording: {e.returncode}")
                print(f"Standard error output: {e.stderr}")
                print(f"Standard output: {e.stdout}")

            if(os.path.exists(recorded_filename) is True):
                try:
                    thread = threading.Thread(target=self.fix_video_file, args=(recorded_filename, filename))
                    thread.start()
                except Exception as e:
                    print(e)
            else:
                print(f"Skip fixing. File not found.")
                print(f"Fixing is done. Going back to checking..")
                time.sleep(self.refresh)

def main(argv):
    tsr = TwitchStreamRecorder()
    usage_message = f'''Usage: tsr.py -u <username> -q <quality>
    
Options:
  -h, --help        Display this help message and exit.
  -u, --username    Specify the Twitch streamer's username (required).
  -a, --audio       Choose the audio format for conversion (e.g. mp3).
                    Valid options are: {', '.join(tsr.valid_audio)}.
  -s, --savefile    Decide whether to keep or delete the original file after conversion. 
                    Default is 'yes' (keep the original file). 
                    Use 'no' to delete the original file after conversion.
  -q, --quality     Specify the desired stream quality. Valid options are:
                    {', '.join(tsr.valid_qualities)}.
                    If not specified, the default is 'best'.'''

    try:
        opts, args = getopt.getopt(argv, "hu:q:a:s:", ["username=", "quality=", "audio=", "savefile="])
    except getopt.GetoptError:
        print (usage_message)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-u", "--username"):
            tsr.username = arg
        elif opt in ("-a", "--audio"):
            if arg not in tsr.valid_audio:
                print(f"Invalid audio option: '{arg}'. Valid options are: {', '.join(tsr.valid_audio)}.")
                print(usage_message)
                sys.exit(2)
            tsr.audio = arg
        elif opt in ("-q", "--quality"):
            if arg not in tsr.valid_qualities:
                print(f"Invalid quality option: '{arg}'. Valid options are: {', '.join(tsr.valid_qualities)}.")
                print(usage_message)
                sys.exit(2)
            tsr.quality = arg
        elif opt in ("-s", "--savefile"):
            if arg.lower() not in ['yes', 'no']:
                print(f"Invalid value for savefile: '{arg}'. Use 'yes' or 'no'.")
                print(usage_message)
                sys.exit(2)
            tsr.savefile = arg.lower()

    tsr.run()

if __name__ == "__main__":
    main(sys.argv[1:])
