from datetime import datetime
from typing import Tuple, List

import googleapiclient.discovery
from tqdm.notebook import tqdm

__DEVELOPER_KEY = 'AIzaSyAlL6yvd0YkA3Co-QA8AbUt7buW3Y0RnGg'


def download_video_categories(video_ids: List[str]) -> dict:
    youtube_client = __create_youtube_api_client()

    video_ids_chunks = list(__make_chunks(video_ids, 50))

    category_ids = {}
    for chunk in tqdm(video_ids_chunks):
        videos_result = __download_videos(youtube_client, ids=chunk, part='snippet')
        for item in videos_result['items']:
            category_ids[item['id']] = item['snippet']['categoryId']

    return category_ids


def download_youtube_data(
        start_date: datetime,
        end_date: datetime,
        view_count_threshold: int,
        excluded_ids: set = None
):
    if excluded_ids is None:
        excluded_ids = set()

    youtube_client = __create_youtube_api_client()

    # TODO: Check if trending (excluded_ids)
    # TODO: Use date range from trending dataframe
    # TODO: Add date loop
    # TODO: Save done dates to a file
    date = start_date
    while date <= datetime.today():
        # TODO: Sort videos by view_count
        # TODO: Use view_count_threshold to limit videos
        video_ids, next_page_token = __download_video_ids(youtube_client)
        # TODO: Save vide_ids to file
        while next_page_token:
            video_ids_next, next_page_token = __download_video_ids(youtube_client)
            video_ids.extend(video_ids_next)

            # TODO: Save vide_ids to file

    # TODO: Download video details
    # TODO: Save remaining video ids to a file


def __create_youtube_api_client():
    # API information
    api_service_name = 'youtube'
    api_version = 'v3'

    youtube_client = googleapiclient.discovery.build(api_service_name, api_version, developerKey=__DEVELOPER_KEY)
    return youtube_client


def __download_video_ids(
        youtube_client,
        date_after: str = '2022-04-10T00:00:00Z',
        page_token: str = '',
) -> Tuple[list, str]:
    search_result: dict = __search(youtube_client, date_after=date_after, page_token=page_token)
    video_ids = [item['id']['videoId'] for item in search_result['items']]

    return video_ids, search_result.get('nextPageToken', default='')


def __search(
        youtube_client,
        date_after: str = '2022-04-10T00:00:00Z',
        page_token: str = ''
) -> dict:
    request = youtube_client.search().list(
        type='video',
        part='snippet',
        regionCode='US',
        publishedAfter=date_after,
        pageToken=page_token,
        maxResults=50
    )
    search_result: dict = request.execute()
    return search_result


def __download_videos(
        youtube_client,
        page_token: str = '',
        ids=None,
        part: str = 'snippet,statistics'
) -> dict:
    if ids is None:
        ids = []

    request = youtube_client.videos().list(
        part=part,
        regionCode='US',
        id=','.join(ids),
        pageToken=page_token,
        maxResults=50
    )
    search_result: dict = request.execute()
    return search_result


def __make_chunks(list_, n):
    for i in range(0, len(list_), n):
        yield list_[i:i + n]
