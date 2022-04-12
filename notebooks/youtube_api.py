from datetime import datetime
from typing import Tuple

import googleapiclient.discovery


def download_youtube_data(start_date: datetime, developer_key: str):
    # API information
    api_service_name = 'youtube'
    api_version = 'v3'
    DEVELOPER_KEY = 'AIzaSyAlL6yvd0YkA3Co-QA8AbUt7buW3Y0RnGg'

    # API client
    youtube_client = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

    # TODO: Add date loop
    # TODO: Save done dates to a file
    date = start_date
    while date <= datetime.today():
        video_ids, next_page_token = __download_video_ids(youtube_client)
        # TODO: Save vide_ids to file
        while next_page_token:
            video_ids_next, next_page_token = __download_video_ids(youtube_client)
            video_ids.extend(video_ids_next)

            # TODO: Save vide_ids to file

    # TODO: Download video details
    # TODO: Save remaining video ids to a file


def __download_video_ids(youtube_client, page_token: str = '') -> Tuple[list, str]:
    request = youtube_client.search().list(
        type='video',
        part='snippet',
        regionCode='US',
        publishedAfter='2022-04-10T00:00:00Z',
        pageToken=page_token,
        maxResults=50
    )
    search_result: dict = request.execute()
    video_ids = [item['id']['videoId'] for item in search_result['items']]

    return video_ids, search_result.get('nextPageToken', default='')
