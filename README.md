# Twitch-Stream-Recorder
Twitch Stream Recorder

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
Allows to easily create systemd services via the root account to create recorders.

When starting the script you will be asked for the username to run tsr.py, 
just put the tsr.py in the home folder of the user. Or adjust the path in the script.
