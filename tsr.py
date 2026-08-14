# -*- coding: utf-8 -*-

# Twitch Stream Recorder (tsr.py)
#
# Version: 15.08.2026-0050
# Developed by: DravenTec

import os
import time
import json
import sys
import subprocess
import datetime
import getopt
from concurrent.futures import ThreadPoolExecutor

class TwitchStreamRecorder:
    def __init__(self):

        # Global configuration
        # Every setting below can be overridden without editing this file,
        # either with the environment variable named in its comment or with
        # the same key in the config file (default: ~/.config/tsr/config,
        # overridable via TSR_CONFIG). Format: one KEY=VALUE per line,
        # '#' starts a comment. Precedence: environment variable > config
        # file > built-in default.
        self._config = self.load_config()

        # TSR_ROOT_PATH: folder where the recordings should be stored
        # Example: /home/username/recording/
        self.root_path = self.get_setting("TSR_ROOT_PATH", "/recording/")

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

        # TSR_STREAMLINK - Default: streamlink
        # If Streamlink is running in a virtual environment, please specify the path to it.
        self.streamlink = self.get_setting("TSR_STREAMLINK", 'streamlink')

        # TSR_FFMPEG - Default: ffmpeg
        # If ffmpeg is not defined globally please specify the appropriate path
        self.ffmpeg_path = self.get_setting("TSR_FFMPEG", 'ffmpeg')

        # TSR_STREAMLINK_ARG
        # Default: --twitch-api-header Client-ID=ue6666qo983tsx6so1t0vnawi233wa
        # Streamlink running arguments
        # (--twitch-disable-hosting and --twitch-disable-ads were dropped:
        # hosting is gone since Streamlink 5.0 and ads are always filtered
        # since 7.5 - both flags are silent no-ops today.)
        self.streamlink_arg = self.get_setting("TSR_STREAMLINK_ARG", '--twitch-api-header Client-ID=ue6666qo983tsx6so1t0vnawi233wa')

        # TSR_TWITCH_CLI - Default: /home/linuxbrew/.linuxbrew/bin/twitch
        # If the installation instructions of Twitch-Cli were followed, the path does not need to be adjusted.
        self.twitch_path = self.get_setting("TSR_TWITCH_CLI", '/home/linuxbrew/.linuxbrew/bin/twitch')

        # TSR_REFRESH - Default: 15.0
        # Minimum value for checking if a streamer is online is 15 seconds,
        # values below that are automatically set to 15 regardless of the entered value.
        try:
            self.refresh = float(self.get_setting("TSR_REFRESH", 15.0))
        except ValueError:
            print(f"Invalid TSR_REFRESH value, falling back to 15 seconds.")
            self.refresh = 15.0

        # For file post-processing
        self.quality_suffixes = ['_audioonly', '_best', '_high', '_medium', '_low', '_mobile']
        self.valid_qualities = ['best', 'high', 'medium', 'low', 'mobile', 'audio_only']

        # Twitch stopped exposing the high/medium/low/mobile stream names
        # years ago; today the names are e.g. 1080p60, 720p60, 480p30 and
        # the fps suffix varies per channel. Instead of hardcoding names,
        # cap the selection with --stream-sorting-excludes and record the
        # best stream below the cap.
        self.quality_caps = {'high': '>720p', 'medium': '>480p', 'low': '>360p', 'mobile': '>160p'}
        self.valid_audio = ['mp3', 'ogg', 'aac']
        self.audio = ""
        self.savefile = "yes"

        # Limits how many ffmpeg post-processing jobs run at the same time.
        # This pool is used ONLY for post-processing (fix_video_file): the
        # streamlink recording runs in the main thread and must never be
        # scheduled on this executor, so recording can never be delayed by
        # queued post-processing jobs.
        self.executor = ThreadPoolExecutor(max_workers=2)

    def load_config(self):
        config = {}
        config_path = os.environ.get("TSR_CONFIG") or os.path.join(
            os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "tsr", "config")
        try:
            with open(config_path) as f:
                for lineno, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        print(f"Ignoring invalid line {lineno} in config file {config_path}: {line}")
                        continue
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"Warning: could not read config file {config_path}: {e}")
        return config

    def get_setting(self, name, default):
        value = os.environ.get(name)
        if value is None:
            value = self._config.get(name, default)
        return value

    def fix_video_file(self, recorded_filename, filename):
        print(f"Processing file: {filename}")
        try:
            quality, cleaned_filename = self.get_quality_from_filename(filename)
            if quality == 'audioonly':
                self.process_audio_file(recorded_filename, cleaned_filename, filename)
            else:
                self.process_video_file(recorded_filename, cleaned_filename, filename)
        except subprocess.CalledProcessError as e:
            print(f"Error during video repair/convert, ffmpeg exited with {e.returncode}")
        except Exception as e:
            print(f"Error during file processing: {e}")

    def process_audio_file(self, recorded_filename, cleaned_filename, filename):
        if self.audio in self.valid_audio:
            self.audio_convert(recorded_filename, cleaned_filename)
            if self.savefile == 'yes' and self.audio != 'aac':
                self.remux_audio(recorded_filename, cleaned_filename)
            else:
                # For 'aac' the converted file is already a copy of the
                # original audio, keeping the .ts as well would just
                # duplicate it under the same target name.
                os.remove(recorded_filename)
        else:
            self.remux_audio(recorded_filename, cleaned_filename)

    def remux_audio(self, recorded_filename, cleaned_filename):
        new_filename = self.replace_ts_suffix(cleaned_filename, ".aac")
        ffmpeg_remux = [self.ffmpeg_path, '-y', '-err_detect', 'ignore_err', '-i', recorded_filename, '-vn', '-acodec', 'copy', os.path.join(self.processed_path, new_filename)]
        subprocess.run(ffmpeg_remux, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        os.remove(recorded_filename)
        print(f"Audio remuxed to {new_filename} and moved to processed folder.")


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
        new_filename = self.replace_ts_suffix(cleaned_filename, ".mp4")
        ffmpeg_video = [self.ffmpeg_path, '-y', '-err_detect', 'ignore_err', '-i', recorded_filename, '-c', 'copy', '-movflags', 'faststart', os.path.join(self.processed_path, new_filename)]
        subprocess.run(ffmpeg_video, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        os.remove(recorded_filename)
        print(f"Video file {filename} repaired, converted to {new_filename} and moved to processed folder.")
            
    def audio_convert(self,recorded_filename,cleaned_filename):
        new_filename = self.replace_ts_suffix(cleaned_filename, f".{self.audio}")
        ffmpeg_audio =[]
        if self.audio == 'mp3':
            ffmpeg_audio = [self.ffmpeg_path, '-y', '-err_detect', 'ignore_err', '-i', recorded_filename, '-codec:a', 'libmp3lame', '-qscale:a', self.mp3_quality, os.path.join(self.processed_path, new_filename)]
        if self.audio == 'ogg':
            ffmpeg_audio = [self.ffmpeg_path, '-y', '-err_detect', 'ignore_err', '-i', recorded_filename, '-codec:a', 'libvorbis', '-qscale:a', self.ogg_quality, os.path.join(self.processed_path, new_filename)]
        if self.audio == 'aac':
            ffmpeg_audio = [self.ffmpeg_path, '-y', '-err_detect', 'ignore_err', '-i', recorded_filename, '-vn', '-acodec', 'copy', os.path.join(self.processed_path, new_filename)]
        subprocess.run(ffmpeg_audio, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        print(f"Audio file converted to {self.audio} renamed to {new_filename} and moved to processed folder.")
            
    def replace_ts_suffix(self, filename, new_ext):
        # Only touch the trailing extension - str.replace would also hit a
        # ".ts" inside the stream title.
        if filename.endswith(".ts"):
            return filename[:-3] + new_ext
        return filename

    def get_quality_from_filename(self, filename):
        quality = 'best'
        for suffix in self.quality_suffixes:
            if filename.endswith(suffix + '.ts'):
                quality = suffix.strip('_')
                filename = filename[:-len(suffix + '.ts')] + '.ts'
                break
        return quality, filename

    def sanitize_filename(self, name, max_length=180):
        safe = "".join(x for x in name if x.isalnum() or x in [" ", "-", "_", "."]).strip()
        safe = " ".join(safe.split())
        if len(safe) > max_length:
            safe = safe[:max_length].rstrip()
        return safe

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
                self.executor.submit(self.fix_video_file, recorded_filename, f)
        except Exception as e:
            print(e)

        try:
            twcli_usercheck = [self.twitch_path, "api", "get", "users", "-q", f"login={self.username}"]
            usercheck = subprocess.run(twcli_usercheck, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            user_data = usercheck.stdout
            user_err = usercheck.stderr
            if usercheck.returncode != 0:
                print(f"Error executing Twitch API command: {user_err}")
            else: 
                try:
                    info_user = json.loads(user_data)
                except json.JSONDecodeError as e:
                    print(f"Error parsing user data: {e}")
                    return
                user_data_list = info_user.get('data') or []
                if user_data_list and 'id' in user_data_list[0]:
                    print(f"Checking for {self.username} every {self.refresh} seconds. Record with {self.quality} quality.")
                    running = True
                    try:
                        while running:
                            try:
                                self.loopcheck()
                            except KeyboardInterrupt:
                                running = False
                            except Exception as e:
                                print(f"An unexpected error occurred: {e}. Retrying in 5 minutes.")
                                try:
                                    time.sleep(300)
                                except KeyboardInterrupt:
                                    running = False
                    finally:
                        print(f"Waiting for running post-processing jobs to finish...")
                        self.executor.shutdown(wait=True)
                        print(f"Twitch Stream Recorder... closing.")
                else:
                    print(f"Username not found. Invalid username or typo.")
        except Exception as e:
            print (f"Error calling Twitch API: {e}")

    def check_user(self):
        info = None
        status = 3
        try:
            twcli_streamcheck = [self.twitch_path, "api", "get", "streams", "-q", f"user_login={self.username}"]
            streamcheck = subprocess.run(twcli_streamcheck, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stream_data = streamcheck.stdout
            stream_err = streamcheck.stderr
            if streamcheck.returncode != 0:
                print(f"Error executing Twitch API command: {stream_err}")
            else:
                try:
                    info = json.loads(stream_data)
                except json.JSONDecodeError as e:
                    print(f"Error parsing stream data: {e}")
                    return status, info
                if 'data' in info and len(info['data']) > 0 and info['data'][0].get('type') == 'live':
                    status = 0
                else:
                    status = 1
        except Exception as e:
            print(f"Error calling Twitch API: {e}")
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
            filename = self.sanitize_filename(filename)
            recorded_filename = os.path.join(self.recorded_path, filename)

            try:
                cap = self.quality_caps.get(self.quality)
                cap_args = ["--stream-sorting-excludes", cap] if cap else []
                stream_selection = "best" if cap else self.quality
                streamlink_record = [self.streamlink] + self.streamlink_arg.split() + cap_args + ["twitch.tv/" + self.username, "--default-stream", stream_selection, "-o", recorded_filename]
                subprocess.run(streamlink_record, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during streamlink recording, streamlink exited with {e.returncode}")

            if os.path.exists(recorded_filename):
                self.executor.submit(self.fix_video_file, recorded_filename, filename)
            else:
                print(f"Recording produced no file. Skipping post-processing.")
            # Always pause before the next online check - without this a
            # streamlink that fails instantly would hammer the API in a
            # tight loop.
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
        opts, args = getopt.getopt(argv, "hu:q:a:s:", ["help", "username=", "quality=", "audio=", "savefile="])
    except getopt.GetoptError:
        print (usage_message)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ('-h', '--help'):
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
