# Twitch-Stream-Recorder
A customized version of [junian's twitch-recorder](https://gist.github.com/junian/b41dd8e544bf0e3980c971b0d015f5f6), OAuth and API calls via twitch-cli.

This script is a Python program for recording Twitch streams. 
It uses the Twitch CLI, streamlink and FFmpeg to record and process the video files. The script is set to use the "best" quality for recording by default, 
but you can specify other options such as "high", "medium", "low", and "mobile". The script will check if the user is online every 15 seconds by default, 
but this value can be changed. If a user is online, the stream will be recorded and saved to a folder named after the user's username under the "recorded" folder. 
The recorded files will then be processed to remove any errors and to adjust the moov atom header for quicker playback. The processed files will be saved in the "processed" folder under the same subfolder as the recorded files. The script will also check for any previously recorded files in the recorded folder and process 
them if necessary.

## Requirements
1. [python3.8](https://www.python.org/downloads/release/python-380/) or higher  
2. [streamlink](https://streamlink.github.io/) newest Version
3. [ffmpeg](https://ffmpeg.org/) 
4. [twitch-cli](https://github.com/twitchdev/twitch-cli)

## tsr.py
Starts recording as soon as the streamer is live. It is recommended that the streamer makes a "Starting soon" at the beginning. 
It takes about 15-45 seconds before the Twitch API reports the status Live. Additionally tsr.py only checks every 15 seconds if 
the streamer is live. If necessary the time can be reduced as long as you don't make too many requests.

To access the Twitch API it is necessary to install and configure the Twtich Cli. 

## Install Streamlink and Twitch Cli to run tsr.py
Tested under Ubuntu 20.04.3 LTS (Focal Fossa) and Debian 11 (Bullseye)
1) Install Dependencies: `sudo apt install pip curl git`
2) Install Streamlink: `sudo pip3 install streamlink`
3) Install Homebrew:  
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
4) After installing Homebrew, run the two commands:  
   `echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/$USER/.profile`  
   and  
   `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`  
   - Optional: `brew install gcc`
5) Install Twitch-Cli: `brew install twitchdev/twitch/twitch-cli`
6) With the following command we now configure Twitch-Cli: `twitch configure`
	- You have to create a Twitch App https://dev.twitch.tv/ to get Client ID and Secret
	- Set OAUTH URL To http://localhost:3000 as Category use Application Integration
7) After `twitch configure` run `twitch-token` once
8) Download tsr.py and edit self.root_path = "YOUR_RECORDER_FOLDER": `nano tsr.py`
9) Run with `python3 tsr.py -u STREAMERNAME`
	- Example: `python3 tsr.py - u diedoni` By default, recording is done with the best quality
	- Optional: (WIP) [tsrcontrol](https://github.com/DravenTec/tsrcontrol) can also be used for administration.

To ensure that the Twitch token is always renewed, I use Crontab and have the token updated once a week.  
If you want to update it manually you can do that at any time with `twitch token`.

Set up a cronjob under the user running tsr.py and twitch with `crontab -e`  
In my case, I have the token renewed every Monday at 2am.  
`0 2 * * MON /home/linuxbrew/.linuxbrew/bin/twitch token > /home/YOUR_USERNAME/logs/twitch.log 2>&1`  
I have the output of the twitch token command written in a log file to have a clue in case of problems.  
The folder and file must be created before. `mkdir ~/logs && touch ~/logs/twitch.log`

**Note that the token itself is also entered here.**  

If you want to do without a log, you can do so with the following crontab entry:   
`0 2 * * MON /home/linuxbrew/.linuxbrew/bin/twitch token > /dev/null 2>&1`



