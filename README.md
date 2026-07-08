![GitHub](https://img.shields.io/github/license/DravenTec/Twitch-Stream-Recorder)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/DravenTec/Twitch-Stream-Recorder)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/DravenTec/Twitch-Stream-Recorder)

## Twitch Stream Recorder (tsr.py)
Twitch Stream Recorder is a Python script for recording live streams from Twitch.
The script allows you to record the stream in various quality options, including audio-only,
and convert the audio to different formats.

Features:
- Record Twitch streams in different qualities (best, high, medium, low, mobile, and audio_only).
- Automatic stream checking to start recording when a streamer goes live.
- Post-processing: recordings are repaired and remuxed to MP4 (`-c copy`, `faststart`) after the stream ends.
- Convert audio to formats like MP3, OGG, and AAC.
- Unfinished recordings from a previous run are picked up and processed automatically at startup.
- Post-processing runs in the background (max. 2 parallel ffmpeg jobs) and never delays or blocks a recording.
- Configurable via config file (`~/.config/tsr/config`) or environment variables — no need to edit the script.

## Requirements
1. [python3.8](https://www.python.org/downloads/release/python-380/) or higher
2. [streamlink](https://streamlink.github.io/) newest version
3. [ffmpeg](https://ffmpeg.org/)
4. [twitch-cli](https://github.com/twitchdev/twitch-cli)

## How it works
tsr.py checks via the Twitch API whether the streamer is live and starts recording as soon as they are.
It is recommended that the streamer makes a "Starting soon" at the beginning: it takes about 15-45 seconds
before the Twitch API reports the status Live, and tsr.py only checks every 15 seconds (configurable,
15 seconds is the minimum).

Recordings are written as `.ts` files to `<root_path>/recorded/<streamer>/` and moved to
`<root_path>/processed/<streamer>/` after post-processing.

To access the Twitch API it is necessary to install and configure the Twitch CLI.

## Usage
```
python3 tsr.py -u <username> [-q <quality>] [-a <audio format>] [-s <yes|no>]
```

| Option | Description |
| ------ | ----------- |
| `-h`, `--help` | Display the help message and exit. |
| `-u`, `--username` | The Twitch streamer's username, lowercase (required; you will be prompted if omitted). |
| `-q`, `--quality` | Stream quality: `best`, `high`, `medium`, `low`, `mobile`, `audio_only`. Default: `best`. |
| `-a`, `--audio` | Additionally convert the audio track: `mp3`, `ogg` or `aac`. |
| `-s`, `--savefile` | Keep (`yes`, default) or delete (`no`) the original recording after audio conversion. |

Examples:
```bash
# Record with best quality
python3 tsr.py -u diedoni

# Record in low quality and additionally extract the audio as MP3
python3 tsr.py -u diedoni -q low -a mp3

# Audio-only recording, converted to OGG, original AAC file deleted afterwards
python3 tsr.py -u diedoni -q audio_only -a ogg -s no
```

Optional: (WIP) [tsrcontrol](https://github.com/DravenTec/tsrcontrol) can also be used for administration.

## Configuration
All settings have sensible defaults and can be overridden without editing the script —
either with a config file or with environment variables. The precedence is:

**environment variable > config file > built-in default**

### Config file
tsr.py looks for `~/.config/tsr/config` (respecting `XDG_CONFIG_HOME`); an alternative
path can be set with the `TSR_CONFIG` environment variable. The format is one
`KEY=VALUE` per line, `#` starts a comment:

```ini
# ~/.config/tsr/config
TSR_ROOT_PATH=/home/username/recording/
TSR_REFRESH=30
TSR_TWITCH_CLI=/home/linuxbrew/.linuxbrew/bin/twitch
```

### Environment variables
The same keys can be set as environment variables, which take precedence over
the config file:

| Key | Default | Description |
| --- | ------- | ----------- |
| `TSR_ROOT_PATH` | `/recording/` | Folder where recordings are stored. |
| `TSR_STREAMLINK` | `streamlink` | Path to the streamlink binary (e.g. inside a virtualenv). |
| `TSR_FFMPEG` | `ffmpeg` | Path to the ffmpeg binary. |
| `TSR_STREAMLINK_ARG` | see tsr.py | Extra arguments passed to streamlink. |
| `TSR_TWITCH_CLI` | `/home/linuxbrew/.linuxbrew/bin/twitch` | Path to the Twitch CLI binary. |
| `TSR_REFRESH` | `15.0` | Check interval in seconds (minimum 15). |
| `TSR_CONFIG` | `~/.config/tsr/config` | Path to the config file (environment variable only). |

Example:
```bash
TSR_ROOT_PATH=/home/username/recording/ python3 tsr.py -u diedoni
```

Alternatively, the defaults can still be changed directly in the configuration block
at the top of `tsr.py`.

## Install Streamlink and Twitch CLI to run tsr.py
Tested under Ubuntu 20.04.3 LTS (Focal Fossa) and Debian 12 (Bookworm)
1) Install dependencies: `sudo apt install pip curl git`
2) Install Streamlink: `sudo pip3 install streamlink`
3) Install Homebrew:
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
4) After installing Homebrew, run the two commands:
   `echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/$USER/.profile`
   and
   `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"`
   - Optional: `brew install gcc`
5) Install Twitch CLI: `brew install twitchdev/twitch/twitch-cli`
6) With the following command we now configure the Twitch CLI: `twitch configure`
	- You have to create a Twitch App at https://dev.twitch.tv/ to get Client ID and Secret
	- Set OAuth URL to http://localhost:3000 and use Application Integration as category
7) After `twitch configure` run `twitch token` once
8) Download tsr.py and set your recording folder, either in the config file
   (`TSR_ROOT_PATH=/your/recorder/folder/` in `~/.config/tsr/config`), via the
   environment variable of the same name, or by editing `self.root_path` in `tsr.py`
9) Run with `python3 tsr.py -u STREAMERNAME`

## Automatic token renewal
To ensure that the Twitch token is always renewed, I use crontab and have the token updated once a week.
If you want to update it manually you can do that at any time with `twitch token`.

Set up a cronjob under the user running tsr.py and twitch with `crontab -e`
In my case, I have the token renewed every Monday at 2am.
`0 2 * * MON /home/linuxbrew/.linuxbrew/bin/twitch token > /home/YOUR_USERNAME/logs/twitch.log 2>&1`
I have the output of the twitch token command written in a log file to have a clue in case of problems.
The folder and file must be created before: `mkdir ~/logs && touch ~/logs/twitch.log`

**Note that the token itself is also entered here.**

If you want to do without a log, you can do so with the following crontab entry:
`0 2 * * MON /home/linuxbrew/.linuxbrew/bin/twitch token > /dev/null 2>&1`
