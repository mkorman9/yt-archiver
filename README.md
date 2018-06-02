# yt-archiver
yt-archiver offers automatic backup for YouTube videos and livestreams. All you need to do is to choose channels to follow and leave it
running 24/7. It will automatically download any new content. Copies will be accessible even if original video or
associated channel would become unavailable.

*Nothing gets deleted from the Internet*

## Installation

### Prerequirements
- Python 3
- pip
- YouTube API key (this could be obtained by following 
[the official guide](https://developers.google.com/youtube/registering_an_application), most interesting sections would be 
*"Create your project and select API services"* and *"Creating API Keys"*)
- Identifiers of channels that you would like to follow. To obtain these simply open YouTube in browser and navigate to your favorite channel. 
In the navigation bar there will be an URL in format: ```https://www.youtube.com/channel/<ID>```. Series of characters
visible in place of  ```<ID>``` will indicate the unique identifier of the channel. Copy it.

### Steps
1. Install command line tool:
    ```
    pip3 install yt-archiver
    ```
2. Start monitoring with:
    ```
    ytarchiver -k <YOUR_API_KEY> -m <CHANNELS_ID>
    ```
    Of course replace ```<YOUR_API_KEY>``` with your personal YouTube API key and ```<CHANNELS_ID>``` with identifiers of
    channels that you would like to monitor. Multiple identifiers could be specified after space. ```ytarchiver```
    command is installed globally, so you can invoke it from any directory.

Now application should automatically download any new video. By default videos are stored in ```out``` folder. 


### Custom options
#### Record livestreams
yt-archiver offers an option to automatically record any livestream started on monitored channels.
All you need to do is to add ```-s``` option.
```
ytarchiver -k <YOUR_API_KEY> -m <CHANNELS_ID> -s
```

#### Changing output directory
By default yt-archiver saves all downloaded videos to ```out``` directory, in application's folder.
```-o``` option allows to change it.
```
ytarchiver -k <YOUR_API_KEY> -m <CHANNELS_ID> -o <CUSTOM_OUTPUT_DIRECTORY>
```

#### Downloading historical data
By default yt-archiver only downloads videos published after it is started. To download all videos from the past specify
```-a``` option.
```
ytarchiver -k <YOUR_API_KEY> -m <CHANNELS_ID> -a
```
**WARNING:** downloading all videos from channel might take a lot of time and consume a lot of disk space

#### Changing refresh time
Default delay between consecutive requests for new videos is 5 minutes. It might be changed with ```-t``` option.
```
ytarchiver -k <YOUR_API_KEY> -m <CHANNELS_ID> -t 60
```
```-t``` expects time in seconds. Command above will fetch channels every 1 minute.
