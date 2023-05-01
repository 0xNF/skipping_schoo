# Requirements
* Python 3.10+
* FFMpeg



# Installation
`pip install -r requirements.txt`

# Usage

To make the first use of this flow easier, it is recommended to install `faster_whisper` and download the `large-v2` model before running.

# Pipeline
## (1) Downloading a Schoo Video
### `download_schoo.py $url`
Schoo videos are numbered by a `${video_id}`, e.g.,  

```javascript
let video_id = 2799;
let room_url = `https://schoo.jp/class/${video_id}/room`;
```

This class number can be used to fetch a `.m3u8` file, which contains a playlist listing tiny pieces of the whole video. This playlist file can be  found at the following url scheme:
    
    
```javascript
let m3u8_url = `https://video.schoo.jp/full/2001/${video_id}.m3u8`;
```

Using FFMPEG, we can download the m3u8, get each individual piece, and stitch it back into a full video  

```javascript
let output_directory = `./${video_id}`;
let schoo_output_file = `schoo_${video_id}.mp4";
```

```bash
ffmpeg -i "$m3u8_url" -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 $output_directory
```


## (2) Ripping Audio
### `rip_audio.py $video_file`

 Some whisper models prefer the audio output to be in 16khz WAV file format. Additionally, it is better to have Mono, not Stereo, audio. We use FFMPEG to make a mono 16khz wav file from the audio channels:

```javascript
let audio_rip = `schoo_${video_id}.wav`
```
```bash
ffmpeg -i $schoo_output_file -acodec pcm_s16le -ac 1 -ar 16000 $audo_rip
 ```

## (3) Making a Transcription
### `transcribe.py $video_file`

Loads Whisper into VRAM and outputs a transcription of the audio

## (3(a)) Sends to OpenAPI for translation
## (4) Send to OpenAPI for summary

