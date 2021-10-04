# Twitch-Stream-Recorder
A customized version of [junian's twitch-recorder](https://gist.github.com/junian/b41dd8e544bf0e3980c971b0d015f5f6A), OAuth and API calls via twitch-cli.

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

## tsrcontrol.sh
Since I record various streams I made the tsrcontrol to make my life easier.

Allows to easily create systemd services via the root account to create recorders.

When starting the script you will be asked for the username to run tsr.py, 
just put the tsr.py in the home folder of the user. Or adjust the path in the script.

## Install Streamlink and Twitch Cli to run tsr.py
1) sudo apt install pip curl git
2) pip3 install streamlink
3) Add to ~/.profile or ~/.bashrc. ->> export PATH="${HOME}/.local/bin:${PATH}" 
4) /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
5) echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/draven/.profile
   eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
   Optional: brew install gcc
6) brew install twitchdev/twitch/twitch-cli
7) now configure twitch-cli with: twitch configure
	You have to create a Twitch App https://dev.twitch.tv/ to get Client ID and Secret
	Set OAUTH URL To http://localhost:3000 as Category use Application Integration
8) Download tsr.py and edit self.root_path = "YOUR_RECORDER_FOLDER"
9) Run with python3 tsr.py -u STREAMERNAME
