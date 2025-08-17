# Radio Multicasting

## Overview

Radio Multicasting is a Python-based client-server application that simulates a radio broadcasting system using UDP multicast. The server streams audio files from multiple stations, and clients can connect, select stations, and listen to live audio streams in real time.

## Features

- **Multicast Streaming:** Server streams audio from multiple stations using UDP multicast.
- **Multiple Stations:** Each station has its own playlist and multicast group.
- **Live Audio Playback:** Clients can select stations and listen to live audio.
- **Station Info:** Clients receive station and song information upon connection.
- **Pause/Resume/Change Station:** Clients can pause, resume, or switch stations interactively.

## Project Structure

```
code/
	client/
		client.py         # Client application to connect and listen to stations
	server/
		server.py         # Server application to stream audio from stations
		station1/         # Audio files for station 1
		station2/         # Audio files for station 2
		station3/         # Audio files for station 3
		station4/         # Audio files for station 4
```

## Requirements

- Python 3.x
- `pyaudio` (for audio playback)
- Audio files in WAV format for each station

Install dependencies:

```bash
pip install pyaudio
```

## Usage

### 1. Start the Server

Navigate to the `server` directory and run:

```bash
python server.py
```

The server will start streaming audio from all stations.

### 2. Start the Client

Navigate to the `client` directory and run:

```bash
python client.py <server_ip>
```

Replace `<server_ip>` with the IP address of the server.

### 3. Client Controls

- Enter the station number to start listening.
- Use the following commands during playback:
  - `P` to pause
  - `R` to resume
  - `C` to change station
  - `X` to quit

## How It Works

- The server creates a multicast group for each station and streams audio frames.
- Clients connect to the server, receive station info, and join the multicast group of the selected station.
- Audio is played live using PyAudio.

## Notes

- Ensure all WAV files are present in the respective station folders.
- The server and client must be on the same network for multicast to work.
