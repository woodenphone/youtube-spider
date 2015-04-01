#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     31/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import subprocess# For video and some audio downloads
import urllib# For encoding audio urls
import re
import logging
import json

from utils import *
import config

class Video:
    """Hold everything for one video together in one place"""
    video_id = None
    annotations_xml = None
    info_json = None
    saved = False
    def __init__(self,video_id,annotations_xml=None,info_json=None,saved=False):
        self.video_id = video_id
        self.annotations_xml = annotations_xml
        self.info_json = info_json
        self.saved = saved
        return


def find_url_links(html):
    """Find URLS in a string of text"""
    # Should return list of strings
    # Copied from:
    # http://stackoverflow.com/questions/520031/whats-the-cleanest-way-to-extract-urls-from-a-string-using-python
    # old regex http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    links = re.findall(url_regex,html, re.DOTALL)
    #logging.debug("find_url_links() links: "+repr(links))
    assert(type(links) is type([]))# Should be list
    return links


def crop_youtube_id(url):
    video_id_regex ="""youtube.com/(?:(?:embed/)|(?:watch\?v=))([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        #logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        #logging.error("Could not extract video ID!")
        #logging.debug("locals(): "+repr(locals()))
        return


def scan_video(video_url,output_dir,save_video=False):
    """Use Youtube-dl to collect info for a video"""
    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    logging.debug("processing video:"+repr(video_url))
    program_path = config.youtube_dl_path
    video_id = crop_youtube_id(video_url)
    assert(os.path.exists(program_path))
    if save_video:
       skip_dl_arg =""
    else:
        skip_dl_arg = "--skip-download"
    ignore_errors = "-i"
    safe_filenames = "--restrict-filenames"
    output_arg = "-o"
    info_json_arg = "--write-info-json"
    annotations_arg ="--write-annotations"
    output_template = os.path.join(output_dir, video_id+".%(ext)s")
    # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
    command = [program_path, ignore_errors, safe_filenames, info_json_arg, annotations_arg, output_arg, output_template, skip_dl_arg, video_url]
    logging.debug("command: "+repr(command))
    # Call youtube-dl
    command_result = subprocess.call(command)
    logging.debug("command_result: "+repr(command_result))
    # Fail if bad exit code
    if command_result != 0:
        logging.error("Command did not return correct exit code! (Normal exit is 0)")
        logging.debug("locals(): "+repr(locals()))
        return None
    # gather all data together
    expected_info_path = os.path.join(output_dir, (video_id+".info.json") )
    info_json = read_file(expected_info_path)
    yt_dl_info_dict = json.loads(info_json)
    media_filepath = yt_dl_info_dict["_filename"]

    expected_annotations_path = (media_filepath+".annotations.xml")
    annotations_xml = read_file(expected_annotations_path)
    return Video(video_id,annotations_xml,info_json,save_video)


def spider(start_video_id,output_dir="download",save_videos=False):
    new_video_ids = [start_video_id]# strings of ids to be done
    processed_video_ids = []# Strings of successful yt-dl ids
    failed_video_ids = []# Strings of video ids that did not return success code on yt-dl
    processed_videos = []# Video objects
    all_seen_links = []# Strings of all seen links
    counter = 0
    while (len(new_video_ids) > 0):
        counter += 1
        logging.debug("counter:"+repr(counter))
        # Get an ID to work on
        current_video_id = new_video_ids.pop()
        video_url = "https://www.youtube.com/watch?v="+current_video_id
        # Call YT-DL
        delay(2)
        done_video = scan_video(video_url,output_dir,save_video=False)
        if done_video is None:# Handle failed YT-DL commands
            failed_video_ids.append(current_video_id)
            continue
        else:
            processed_videos.append(done_video)
        processed_video_ids.append(current_video_id)
        # Grab links from metadata
        links = []
        links += find_url_links(done_video.annotations_xml)
        links += find_url_links(done_video.info_json)
        logging.debug("Links found for video "+repr(links))
        # Remove links that have been done or are not YT
        for link in links:
            all_seen_links.append(link)
            link_yt_id = crop_youtube_id(link)
            if link_yt_id:
                if (link_yt_id not in processed_video_ids) and (link_yt_id not in new_video_ids):
                    logging.debug("Adding new ID: "+repr(link_yt_id)+" from link: "+repr(link))
                    new_video_ids.append(link_yt_id)
            continue
        #logging.debug("all_seen_links: "+repr(all_seen_links))
        logging.debug("new_video_ids: "+repr(new_video_ids))
        logging.debug("processed_video_ids: "+repr(processed_video_ids))
        #logging.debug("processed_videos: "+repr(processed_videos))
        continue
    logging.info("Finished spidering")
    logging.debug("all_seen_links: "+repr(all_seen_links))
    logging.debug("new_video_ids: "+repr(new_video_ids))
    logging.debug("failed_video_ids: "+repr(failed_video_ids))
    logging.debug("processed_video_ids: "+repr(processed_video_ids))
    logging.debug("processed_videos: "+repr(processed_videos))
    return






def newspider(base_path="",max_loops=100):
    # Run yt-dl normally
    videos_to_save = []
    video_ids_saved = []
    scanned_files = []
    loop_counter = 0
    while ( (len(videos_to_save) > 0)
    and (loop_counter <= max_loops) ):
        # Scan for metadata files
        # .info.json
        # Find files
        json_glob_string = os.path.join(base_path,"*.info.json")
        info_paths = glob.glob(json_glob_string)
        logging.debug("info_paths: "+repr(info_paths))

        # Process found files
        for info_path in info_paths:
            if info_path not in scanned_files:
                # Read data from file
                info_json = read_file(info_path)
                info_dict = json.loads(info_json)
                # Parse file data
                # Get video ID
                video_id = info_dict
                # Find URLS
                # Collect YT URLS
                # Keep YT URLS with new IDs

                # Add processed filepath to done list
                scanned_files.append(info_path)



        # .annotations.xml
        annotations_glob_string = os.path.join(base_path,"*.annotations.xml")
        annotation_paths = glob.glob(annotations_glob_string)
        logging.debug("annotation_paths: "+repr(annotation_paths))
        # Read and parse new metadata files for video links
        # Run ty-dl for new videos







def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","youtube-spider-log.txt"))
        # Program
        start_video_id = crop_youtube_id(config.video_url)
        spider(start_video_id=start_video_id,output_dir="download",save_videos=config.save_videos)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
