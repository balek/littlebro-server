LittleBro

LittleBro is a CCTV system.

littlebro-stream - captures RTSP and translate it to HLS using ffmpeg.
littlebro-motion - listens for motion events from cameras or motion service and makes video records.
littlebro-archive - scans archive and prepares JSON-files for Web-interface. Watches by inotify for archive changes to update files.
littlebro-trigger - sends motion event for littlebro-motion.