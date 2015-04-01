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
import glob

from utils import *
import config


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


def save_video(video_url,output_dir,download_videos=False):
    """Use Youtube-dl to collect info for a video"""
    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    logging.debug("processing video:"+repr(video_url))
    program_path = config.youtube_dl_path
    video_id = crop_youtube_id(video_url)
    assert(os.path.exists(program_path))
    if download_videos:
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
    return


def spider(start_url="",output_path="",download_videos=False,max_loops=100):
    # Run yt-dl normally
    videos_to_save = [start_url]
    video_ids_saved = []
    scanned_files = []
    loop_counter = 0
    while ( (len(videos_to_save) > 0)
    and (loop_counter <= max_loops) ):
        # Run ty-dl for a new video
        video_to_download = videos_to_save.pop()
        save_video(video_to_download, output_path, download_videos)
        # Scan for metadata files
        # Read and parse new metadata files for video links
        # Find files
        # .info.json
        json_glob_string = os.path.join(output_path,"*.info.json")
        info_paths = glob.glob(json_glob_string)
        logging.debug("info_paths: "+repr(info_paths))
        for info_path in info_paths:
            if info_path in scanned_files:
                continue
            logging.debug("info_path: "+repr(info_paths))
            # Read data from file
            info_json = read_file(info_path)
            info_dict = json.loads(info_json)
            # Parse file data
            # Get video ID
            video_id = info_dict["id"]
            logging.debug("video_id: "+repr(video_id))
            video_ids_saved.append(video_id)
            # Find URLS
            description = info_dict["description"]
            info_file_links = find_url_links(description)
            # Collect YT URLS
            logging.debug("Seperating youtube links")
            info_file_youtube_links = []
            for info_file_link in info_file_links:
                link_yt_id = crop_youtube_id(info_file_link)
                if link_yt_id:
                    info_file_youtube_links.append(info_file_link)
            # Keep YT URLS with new IDs
            logging.debug("Seperating new IDs")
            for info_file_youtube_link in info_file_youtube_links:
                # Keep only unsaved links
                new_video_id = crop_youtube_id(annotations_file_youtube_link)
                if (new_video_id in video_ids_saved):
                    continue
                # Keep only new unsaved links
                elif (info_file_youtube_link in videos_to_save):
                    continue
                else:
                    logging.debug("adding video to to-save list:"+repr(info_file_youtube_link))
                    videos_to_save.append(info_file_youtube_link)
                    continue
            # Add processed filepath to done list
            scanned_files.append(info_path)
            continue

        # .annotations.xml
        annotations_glob_string = os.path.join(output_path, "*.annotations.xml")
        annotation_paths = glob.glob(annotations_glob_string)
        logging.debug("annotation_paths: "+repr(annotation_paths))
        for annotation_path in annotation_paths:
            if annotation_path in scanned_files:
                continue
            logging.debug("annotation_path: "+repr(annotation_path))
            # Read data from file
            annotations_xml = read_file(info_path)
            # Find URLS
            annotations_file_links = find_url_links(annotations_xml)
            # Collect YT URLS
            logging.debug("Seperating youtube links")
            annotations_file_youtube_links = []
            for info_file_link in info_file_links:
                link_yt_id = crop_youtube_id(info_file_link)
                if link_yt_id:
                    info_file_youtube_links.append(info_file_link)
            # Keep YT URLS with new IDs
            logging.debug("Seperating new IDs")
            for annotations_file_youtube_link in annotations_file_youtube_links:
                # Keep only unsaved links
                new_video_id = crop_youtube_id(annotations_file_youtube_link)
                if (new_video_id in video_ids_saved):
                    continue
                # Keep only new unsaved links
                elif (annotations_file_youtube_link in videos_to_save):
                    continue
                else:
                    logging.debug("adding video to to-save list:"+repr(annotations_file_youtube_link))
                    videos_to_save.append(annotations_file_youtube_link)
                    continue
            # Add processed filepath to done list
            scanned_files.append(annotation_path)
            continue
        continue
    logging.info("Spider operation finished.")
    logging.debug("video_ids_saved: "+repr(video_ids_saved))
    logging.debug("scanned_files: "+repr(scanned_files))
    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","youtube-spider-log.txt"))
        # Program
        spider(
            start_url=config.start_url,
            output_path=config.output_path,
            download_videos=config.download_videos,
            max_loops=100
            )
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
