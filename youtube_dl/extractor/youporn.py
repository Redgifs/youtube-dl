from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_to_int,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)
from ..aes import aes_decrypt_text


class YouPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youporn\.com/(?:watch|embed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#&]+))?'
    _TESTS = [{
        'url': 'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'md5': '3744d24c50438cf5b6f6d59feb5055c2',
        'info_dict': {
            'id': '505835',
            'display_id': 'sex-ed-is-it-safe-to-masturbate-daily',
            'ext': 'mp4',
            'title': 'Sex Ed: Is It Safe To Masturbate Daily?',
            'description': 'Love & Sex Answers: http://bit.ly/DanAndJenn -- Is It Unhealthy To Masturbate Daily?',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Ask Dan And Jennifer',
            'upload_date': '20101217',
            'average_rating': int,
            'view_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
    }, {
        # Unknown uploader
        'url': 'http://www.youporn.com/watch/561726/big-tits-awesome-brunette-on-amazing-webcam-show/?from=related3&al=2&from_id=561726&pos=4',
        'info_dict': {
            'id': '561726',
            'display_id': 'big-tits-awesome-brunette-on-amazing-webcam-show',
            'ext': 'mp4',
            'title': 'Big Tits Awesome Brunette On amazing webcam show',
            'description': 'http://sweetlivegirls.com Big Tits Awesome Brunette On amazing webcam show.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'Unknown',
            'upload_date': '20110418',
            'average_rating': int,
            'view_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.youporn.com/embed/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'only_matching': True,
    }, {
        'url': 'http://www.youporn.com/watch/505835',
        'only_matching': True,
    }, {
        'url': 'https://www.youporn.com/watch/13922959/femdom-principal/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+\bsrc=["\']((?:https?:)?//(?:www\.)?youporn\.com/embed/\d+)',
            webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        meta_url = 'https://www.youporn.com/api/video/media_definitions/%s/' % video_id
        raw_meta = self._download_webpage(meta_url, display_id,
            headers={'Cookie': 'age_verified=1'})

        meta = self._parse_json(raw_meta, video_id, fatal=True)

        webpage = self._download_webpage(
            'http://www.youporn.com/watch/%s' % video_id, display_id,
            headers={'Cookie': 'age_verified=1'})

        title = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']watchVideoTitle[^>]+>(.+?)</div>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'title', webpage, fatal=True)

        formats = self._get_formats(meta)

        description = self._html_search_regex(
            r'(?s)<div[^>]+\bid=["\']description["\'][^>]*>(.+?)</div>',
            webpage, 'description',
            default=None) or self._og_search_description(
            webpage, default=None)
        thumbnail = self._search_regex(
            r'(?:imageurl\s*=|poster\s*:)\s*(["\'])(?P<thumbnail>.+?)\1',
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        uploader = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']submitByLink["\'][^>]*>(.+?)</div>',
            webpage, 'uploader', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            [r'UPLOADED:\s*<span>([^<]+)',
             r'Date\s+[Aa]dded:\s*<span>([^<]+)',
             r'(?s)<div[^>]+class=["\']videoInfo(?:Date|Time)["\'][^>]*>(.+?)</div>'],
            webpage, 'upload date', fatal=False))

        age_limit = self._rta_search(webpage)

        average_rating = int_or_none(self._search_regex(
            r'<div[^>]+class=["\']videoRatingPercentage["\'][^>]*>(\d+)%</div>',
            webpage, 'average rating', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'(?s)<div[^>]+class=(["\']).*?\bvideoInfoViews\b.*?\1[^>]*>.*?(?P<count>[\d,.]+)<',
            webpage, 'view count', fatal=False, group='count'))
        comment_count = str_to_int(self._search_regex(
            r'>All [Cc]omments? \(([\d,.]+)\)',
            webpage, 'comment count', default=None))

        def extract_tag_box(regex, title):
            tag_box = self._search_regex(regex, webpage, title, default=None)
            if not tag_box:
                return []
            return re.findall(r'<a[^>]+href=[^>]+>([^<]+)', tag_box)

        categories = extract_tag_box(
            r'(?s)Categories:.*?</[^>]+>(.+?)</div>', 'categories')
        tags = extract_tag_box(
            r'(?s)Tags:.*?</div>\s*<div[^>]+class=["\']tagBoxContent["\'][^>]*>(.+?)</div>',
            'tags')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'average_rating': average_rating,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
        }

    def _get_formats(self, meta):
        formats = []

        for item in meta:
            format = {
                'url': item['videoUrl'],
                'format_id': '%s-%s' % (item['quality'], item['codec']),
                'height': int(item['quality']),
            }

            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', item['videoUrl'])
            if mobj:
                height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                format.update({
                    'height': height,
                    'tbr': bitrate,
                })

            formats.append(format)

        return formats
