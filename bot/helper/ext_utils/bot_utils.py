import logging
import re
import threading
import time

from bot import download_dict, download_dict_lock

LOGGER = logging.getLogger(__name__)

URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'


def getDownloadByGid(gid):
    with download_dict_lock:
        for dl in download_dict.values():
            if dl.status() == MirrorStatus.STATUS_DOWNLOADING or dl.status() == MirrorStatus.STATUS_WAITING:
                if dl.gid() == gid:
                    return dl
    return None

def get_readable_message():
    with download_dict_lock:
        msg = ""
        for download in list(download_dict.values()):
            msg += f"<b>Filename:</b> <i>{download.name()}</i>"
            msg += f"\n<b>Status:</b> <code>{download.status()}</code>"
            if download.status() != MirrorStatus.STATUS_ARCHIVING:
                msg += f"\n<code>{get_progress_bar_string(download)}</code>\n<b>Progress:</b> <i>{download.progress()} of {download.size()}</i>" \
                    f"\n<b>Speed:</b> {download.speed()}\n<b>ETA:</b> {download.eta()}"
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if hasattr(download, 'is_torrent'):
                    msg += f"\n<b>Peers:</b> {download.download().connections} " \
                           f"| <b>Seeds:</b> {download.download().num_seeders}"
                msg += f"\nGID: <code>{download.gid()}</code>"
            msg += "\n\n"
        return msg


def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result


def is_url(url: str):
    url = re.findall(URL_REGEX, url)
    if url:
        return True
    return False


