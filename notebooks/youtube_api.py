import datetime as dt
import json
from typing import Tuple, List, Union

import googleapiclient.discovery
import tqdm
from googleapiclient.errors import HttpError

API_KEYS = {
    "API_KEY_1": True,
    "API_KEY_2": True
}
api_key = ""


def download_video_categories(video_ids: List[str]) -> dict:
    youtube_client = __create_youtube_api_client()

    video_ids_chunks = list(__make_chunks(video_ids, 50))

    category_ids = {}
    for chunk in tqdm.tqdm(video_ids_chunks):
        videos_result = __download_videos(youtube_client, ids=chunk, part='snippet')
        for item in videos_result['items']:
            category_ids[item['id']] = item['snippet']['categoryId']

    return category_ids


def download_non_trending_video_ids(
        date: dt.datetime,
        video_count: int,
        excluded_ids: Union[list, set] = None
) -> List[Tuple[str, dt.datetime]]:
    if excluded_ids is None:
        excluded_ids = set()

    if type(excluded_ids) is list:
        excluded_ids = set(excluded_ids)

    youtube_client = __create_youtube_api_client()

    video_ids = []
    next_page_token = ''
    while len(video_ids) < video_count:
        while True:
            try:
                video_ids_next, next_page_token = __download_video_ids(youtube_client, date, next_page_token)
                video_ids.extend(video_ids_next)
                video_ids = [video_id for video_id in video_ids if video_id[0] not in excluded_ids]
                break
            except HttpError:
                API_KEYS[api_key] = False
                youtube_client = __create_youtube_api_client()
        if not next_page_token:
            break

    return video_ids


def download_video_details():
    # TODO: Implement
    pass


def __create_youtube_api_client():
    global api_key

    # API information
    api_service_name = 'youtube'
    api_version = 'v3'
    try:
        api_key = [key for key in API_KEYS if API_KEYS[key]][0]
    except IndexError:
        raise IndexError("Daily quota exceeded for all api keys")

    youtube_client = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)
    return youtube_client


def __download_video_ids(
        youtube_client,
        date: dt.datetime,
        page_token: str = '',
) -> Tuple[List[Tuple[str, dt.datetime]], str]:
    request = youtube_client.search().list(
        type='video',
        part='snippet',
        regionCode='US',
        order="viewCount",
        publishedAfter=__iso_format(date),
        publishedBefore=__iso_format(date + dt.timedelta(days=1)),
        pageToken=page_token,
        maxResults=50
    )
    search_result: dict = request.execute()
    print(json.dumps(search_result))
    video_ids = [(item['id']['videoId'], __iso_parse(item['snippet']['publishedAt'])) for item in
                 search_result['items']]

    return video_ids, search_result.get('nextPageToken', '')


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


def __iso_parse(date_str: str) -> dt.datetime:
    return dt.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def __iso_format(date: dt.datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")
