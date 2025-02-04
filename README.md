![GitHub](https://img.shields.io/github/license/DravenTec/Twitch-Stream-Recorder)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/DravenTec/Twitch-Stream-Recorder)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/DravenTec/Twitch-Stream-Recorder)

## Twitch Stream Recorder (tsr.py)
Twitch Stream Recorder is a Python script for recording live streams from Twitch. 
The script allows you to record the stream in various quality options, including audio-only, 
and convert the audio to different formats. 

Features:
- Record Twitch streams in different qualities (best, high, medium, low, mobile, and audio_only).
- Convert audio to formats like MP3, OGG, and AAC.
- Post-processing options for video and audio files.
- Automatic stream checking to start recording when a streamer goes live.
- Error handling for stream recording, file conversion, and post-processing.
- File management for saving or deleting original files after conversion.

## Requirements
1. [python3.8](https://www.python.org/downloads/release/python-380/) or higher  
2. [streamlink](https://streamlink.github.io/) newest Version
3. [ffmpeg](https://ffmpeg.org/) 
4. [twitch-cli](https://github.com/twitchdev/twitch-cli)

## tsr.py
Starts recording as soon as the streamer is live. It is recommended that the streamer makes a "Starting soon" at the beginning. 
It takes about 15-45 seconds before the Twitch API reports the status Live. Additionally tsr.py only checks every 15 seconds if 
the streamer is live. 

To access the Twitch API it is necessary to install and configure the Twtich Cli. 

## Install Streamlink and Twitch Cli to run tsr.py
Tested under Ubuntu 20.04.3 LTS (Focal Fossa) and Debian 12 (Bookworm)
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
	- Example: `python3 tsr.py -u diedoni` By default, recording is done with the best quality
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



