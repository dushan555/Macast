# Copyright (c) 2022 by NOTAG. All Rights Reserved.
#
# IQIYI protocol
#
# Macast Metadata
# <macast.title>IQIYI Protocol</macast.title>
# <macast.protocol>IQIYIProtocol</macast.protocol>
# <macast.platform>darwin,win32,linux</macast.platform>
# <macast.version>0.1</macast.version>
# <macast.host_version>0.7</macast.host_version>
# <macast.author>dushan555</macast.author>
# <macast.desc>IQIYI protocol support for Macast.</macast.desc>

import os
import json
import cherrypy
import logging
import time
import socket
import threading
import requests
from lxml import etree
from macast.utils import load_xml, XMLPath, Setting, SETTING_DIR
from macast.protocol import DLNAProtocol, DLNAHandler, SERVICE_STATE_OBSERVED, Argument

SERVICE_STATE_OBSERVED.update({
    'PrivateServer': ['A_ARG_TYPE_NOTIFYMSG']
})

PRIVATE_SERVER_SERVICE = """<scpd xmlns="urn:schemas-upnp-org:service-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <serviceStateTable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_InstanceID</name>
            <dataType>ui4</dataType>
        </stateVariable>
        <stateVariable sendEvents="yes">
            <name>A_ARG_TYPE_NOTIFYMSG</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_INFOR</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_SendMessage_Result</name>
            <dataType>string</dataType>
        </stateVariable>
    </serviceStateTable>
    <actionList>
        <action>
            <name>SendMessage</name>
            <argumentList>
                <argument>
                    <name>InstanceID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_InstanceID</relatedStateVariable>
                </argument>
                <argument>
                    <name>Infor</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_INFOR</relatedStateVariable>
                </argument>
                <argument>
                    <name>Result</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_SendMessage_Result</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>NotifyMessage</name>
            <argumentList>
                <argument>
                    <name>NotifyMsg</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_NOTIFYMSG</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
    </actionList>
</scpd>
""".encode()
QPlay_SERVICE = """<scpd xmlns="urn:schemas-upnp-org:service-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <actionList>
        <action>
            <name>SetNetwork</name>
            <argumentList>
                <argument>
                    <name>SSID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_SSID</relatedStateVariable>
                </argument>
                <argument>
                    <name>Key</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_Key</relatedStateVariable>
                </argument>
                <argument>
                    <name>AuthAlgo</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_AuthAlgo</relatedStateVariable>
                </argument>
                <argument>
                    <name>CipherAlgo</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_CipherAlgo</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>QPlayAuth</name>
            <argumentList>
                <argument>
                    <name>Seed</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_Seed</relatedStateVariable>
                </argument>
                <argument>
                    <name>Code</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_Code</relatedStateVariable>
                </argument>
                <argument>
                    <name>MID</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_MID</relatedStateVariable>
                </argument>
                <argument>
                    <name>DID</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_DID</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>InsertTracks</name>
            <argumentList>
                <argument>
                    <name>QueueID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_QueueID</relatedStateVariable>
                </argument>
                <argument>
                    <name>StartingIndex</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_StartingIndex</relatedStateVariable>
                </argument>
                <argument>
                    <name>TracksMetaData</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_TracksMetaData</relatedStateVariable>
                </argument>
                <argument>
                    <name>NumberOfSuccess</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>RemoveTracks</name>
            <argumentList>
                <argument>
                    <name>QueueID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_QueueID</relatedStateVariable>
                </argument>
                <argument>
                    <name>StartingIndex</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_StartingIndex</relatedStateVariable>
                </argument>
                <argument>
                    <name>NumberOfTracks</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
                <argument>
                    <name>NumberOfSuccess</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>RemoveAllTracks</name>
            <argumentList>
                <argument>
                    <name>QueueID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_QueueID</relatedStateVariable>
                </argument>
                <argument>
                    <name>UpdateID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_StartingIndex</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>GetTracksInfo</name>
            <argumentList>
                <argument>
                    <name>StartingIndex</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_StartingIndex</relatedStateVariable>
                </argument>
                <argument>
                    <name>NumberOfTracks</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
                <argument>
                    <name>TracksMetaData</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_TracksMetaData</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>SetTracksInfo</name>
            <argumentList>
                <argument>
                    <name>QueueID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_QueueID</relatedStateVariable>
                </argument>
                <argument>
                    <name>StartingIndex</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_StartingIndex</relatedStateVariable>
                </argument>
                <argument>
                    <name>NextIndex</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_NextIndex</relatedStateVariable>
                </argument>
                <argument>
                    <name>TracksMetaData</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_TracksMetaData</relatedStateVariable>
                </argument>
                <argument>
                    <name>NumberOfSuccess</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>GetTracksCount</name>
            <argumentList>
                <argument>
                    <name>NrTracks</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>GetMaxTracks</name>
            <argumentList>
                <argument>
                    <name>MaxTracks</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_NumberOfTracks</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>GetLyricSupportType</name>
            <argumentList>
                <argument>
                    <name>LyricType</name>
                    <direction>out</direction>
                    <relatedStateVariable>A_ARG_TYPE_LYRIC_TYPE</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
        <action>
            <name>SetLyric</name>
            <argumentList>
                <argument>
                    <name>SongID</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_SONG_ID_TYPE</relatedStateVariable>
                </argument>
                <argument>
                    <name>LyricType</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_LYRIC_TYPE</relatedStateVariable>
                </argument>
                <argument>
                    <name>Lyric</name>
                    <direction>in</direction>
                    <relatedStateVariable>A_ARG_TYPE_LYRIC_TEXT_TYPE</relatedStateVariable>
                </argument>
            </argumentList>
        </action>
    </actionList>
    <serviceStateTable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_SSID</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_Key</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_AuthAlgo</name>
            <dataType>string</dataType>
            <allowedValueList>
                <allowedValue>open</allowedValue>
                <allowedValue>shared</allowedValue>
                <allowedValue>WPA</allowedValue>
                <allowedValue>WPAPSK</allowedValue>
                <allowedValue>WPA2</allowedValue>
                <allowedValue>WPA2PSK</allowedValue>
            </allowedValueList>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_CipherAlgo</name>
            <dataType>string</dataType>
            <allowedValueList>
                <allowedValue>none</allowedValue>
                <allowedValue>WEP</allowedValue>
                <allowedValue>TKIP</allowedValue>
                <allowedValue>AES</allowedValue>
            </allowedValueList>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_Seed</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_Code</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_MID</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_DID</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_QueueID</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_StartingIndex</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_NextIndex</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_NumberOfTracks</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_TracksMetaData</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_LYRIC_TYPE</name>
            <dataType>string</dataType>
            <allowedValueList>
                <allowedValue>none</allowedValue>
                <allowedValue>QRC</allowedValue>
                <allowedValue>LRC</allowedValue>
            </allowedValueList>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_SONG_ID_TYPE</name>
            <dataType>string</dataType>
        </stateVariable>
        <stateVariable sendEvents="no">
            <name>A_ARG_TYPE_LYRIC_TEXT_TYPE</name>
            <dataType>string</dataType>
        </stateVariable>
    </serviceStateTable>
</scpd>
""".encode()

logger = logging.getLogger("IQIYIProtocol")
logger.setLevel(logging.INFO)


@cherrypy.expose
class IQIYIHandler(DLNAHandler):
    def build_description(self):
        self.description = load_xml(XMLPath.DESCRIPTION.value).format(
            friendly_name='NOTAG的奇异果TV',
            manufacturer="Microsoft Corporation",
            manufacturer_url="http://www.microsoft.com",
            model_description="TVGUO Media Renderer",
            model_name="Windows Media Player",
            model_url="http://go.microsoft.com/fwlink/?LinkId=105927",
            model_number=Setting.get_version(),
            uuid=Setting.get_usn(),
            serial_num=1024,
            header_extra="""<qq:X_QPlay_SoftwareCapability xmlns:qq="http://www.tencent.com">QPlay:2.1</qq:X_QPlay_SoftwareCapability>""",
            service_extra="""<service>
                <serviceType>urn:schemas-upnp-org:service:PrivateServer:1</serviceType>
                <serviceId>urn:upnp-org:serviceId:PrivateServer</serviceId>
                <controlURL>PrivateServer/action</controlURL>
                <eventSubURL>PrivateServer/event</eventSubURL>
                <SCPDURL>dlna/PrivateServer.xml</SCPDURL>
            </service>
            <service>
                <serviceType>urn:schemas-tencent-com:service:QPlay:1</serviceType>
                <serviceId>urn:tencent-com:serviceId:QPlay</serviceId>
                <controlURL>QPlay/action</controlURL>
                <SCPDURL>dlna/QPlay.xml</SCPDURL>
                <eventSubURL>QPlay/event</eventSubURL>
            </service>"""
        ).encode()

    def GET(self, param=None, xml=None, **kwargs):
        print(f'ddd GET xml {xml} param: {param}')
        if param == 'dlna' and xml == 'PrivateServer.xml':
            return PRIVATE_SERVER_SERVICE
        if param == 'dlna' and xml == 'QPlay.xml':
            return QPlay_SERVICE
        return super(IQIYIHandler, self).GET(param, xml, **kwargs)

    def POST(self, service=None, param=None, *args, **kwargs):
        print(f'ddd POST SERVICE {service} param: {param}')
        if service == '_urn:schemas-upnp-org:service:PrivateServer_control':
            service = 'PrivateServer'
            param = 'action'
        return super(IQIYIHandler, self).POST(service, param, *args, **kwargs)

    def SUBSCRIBE(self, service="", param=""):
        print(f'ddd SUBSCRIBE SERVICE {service} param: {param}')
        if service == '_urn:schemas-upnp-org:service:PrivateServer_event':
            service = 'PrivateServer'
            param = 'event'
        return super(IQIYIHandler, self).SUBSCRIBE(service, param)

    def UNSUBSCRIBE(self, service="", param=""):
        print(f'ddd UNSUBSCRIBE SERVICE {service} param: {param}')
        if service == '_urn:schemas-upnp-org:service:PrivateServer_event':
            param = 'event'
        return super(IQIYIHandler, self).UNSUBSCRIBE(service, param)


class NetworkManager:
    proxies = None

    @staticmethod
    def GET(url):
        try:
            data = requests.get(url, proxies=NetworkManager.proxies)
            return data
        except OSError as e:
            # fix proxy error with clash
            logger.error(f'nva requests.get OSError:{e}')
            if 'proxy' in str(e):
                try:
                    NetworkManager.proxies = {'http': None, "https": None}
                    data = requests.get(url, proxies=NetworkManager.proxies)
                    return data
                except Exception as e:
                    logger.error(f'nva requests.get Exception:{e}')

        cherrypy.engine.publish('app_notify', 'ERROR', 'Network error')
        raise Exception('Cannot get any data from network.')


class DanmakuManager:
    @staticmethod
    def get_danmaku(xmlurl: str, file_path: str):
        """

        :param cid:
        :param file_path:
        :param is_portrait:
        :return:
        """
        # http://www.perlfu.co.uk/projects/asa/ass-specs.doc
        api = xmlurl
        exist_time = 10
        res_x = 638
        res_y = 447

        lines = res_y // 25  # todo fix
        layers = [[-1 for _ in range(lines)] for _ in range(4)]

        def int2color(color_int):
            """
            :return: string, \c&Hbbggrr&
            """
            if color_int == 16777215:  # default color #FFFFFF
                return 'dark', ''
            color_int = hex(color_int)[2:]
            if len(color_int) < 6:
                color_int = '0' * (6 - len(color_int)) + color_int
            r = int(color_int[0:2], 16)
            g = int(color_int[2:4], 16)
            b = int(color_int[4:6], 16)
            gray = (r * 299 + g * 587 + b * 114) / 1000
            border_style = 'dark'
            if gray < 60:
                border_style = 'light'

            color_str = color_int[4:6] + color_int[2:4] + color_int[0:2]
            return border_style, rf'\c&H{color_str}&'

        def sec2str(t: float) -> str:
            sec = int(t)
            return f'{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}.{int(t * 100) % 100:02d}'

        def create_postion(danmaku_position_type, layer_index, danmaku_text,
                           font_size, danmaku_start_time) -> str:
            if layer_index > 1:  # 是否是字幕层
                layer_index = 1

            y = -100
            if danmaku_position_type == 5:  # 顶部弹幕
                layer_index = 2
                for index, l in enumerate(layers[layer_index]):
                    if danmaku_start_time < l:
                        continue
                    layers[layer_index][index] = danmaku_start_time + exist_time
                    y = index * 25
                    break
                position_str = rf'\an8\pos({int(res_x / 2)},{y})'
            elif danmaku_position_type == 4:  # 底部弹幕
                layer_index = 3
                for index, l in enumerate(layers[layer_index]):
                    if danmaku_start_time < l:
                        continue
                    layers[layer_index][index] = danmaku_start_time + exist_time
                    y = res_y - index * 25
                    break
                position_str = rf'\an2\pos({int(res_x / 2)},{y})'
            else:  # 普通弹幕
                length = len(danmaku_text) * font_size
                for index, l in enumerate(layers[layer_index]):
                    danmaku_text_length = len(danmaku_text) * font_size
                    danmaku_text_time = (res_x * exist_time) / (res_x + danmaku_text_length)

                    if (danmaku_start_time + danmaku_text_time) < l:
                        continue
                    # 找到空位
                    layers[layer_index][index] = danmaku_start_time + exist_time
                    y = index * 25  # fix font size
                    break

                position_str = rf'\move({res_x},{y},{-length},{y})'

            # todo 根据视频大小 动态改变字体大小
            font_size = int(font_size)
            font = ''
            if font_size == 18:
                font = r'\fs18'
            elif font_size == 36:
                font = r'\fs36'

            return position_str + font

        try:
            danmaku = etree.fromstring(NetworkManager.GET(api).content)
            danmaku = danmaku.xpath("/i/d")
            ass = """[Script Info]
Title: 弹幕
Original Script: """ + api + """
Script Updated By: https://github.com/xfangfang/Macast-Plugin
Update Details: xml to ass
ScriptType: V4.00+
Collisions: Normal

PlayResX: 638
PlayResY: 447
PlayDepth: 8
Timer: 100.0
WrapStyle: 2


[v4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: dark, sans-serif, 25, &H36FFFFFF, &H36FFFFFF, &H36000000, &H36000000, 1, 0, 0, 0, 100, 100, 0.00, 0.00, 1, 1, 0, 7, 0, 0, 0, 0
Style: light, sans-serif, 25, &H36FFFFFF, &H36FFFFFF, &H36FFFFFF, &H36000000, 1, 0, 0, 0, 100, 100, 0.00, 0.00, 1, 1, 0, 7, 0, 0, 0, 0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

            dms = []
            for i in danmaku:
                a = i.attrib['p'].split(',')
                a.append(i.text)
                dms.append(a)

            dms.sort(key=lambda e: float(e[0]))

            for data in dms:
                text = data[-1]
                danmaku_type = int(data[1])
                danmaku_layer = int(data[5])
                if danmaku_type < 7:
                    start_time = float(data[0])
                    end_time = start_time + exist_time
                    position = create_postion(danmaku_type, danmaku_layer, text, int(data[2]), start_time)
                    style, color = int2color(int(data[3]))
                    comment = f'Dialogue: {danmaku_layer},{sec2str(start_time)},{sec2str(end_time)},' + \
                              f'{style},{data[8]},0000,0000,0000,,{{{position}{color}}}{text}\n'
                    ass += comment
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ass)
        except Exception as e:
            logger.error(f'Error create sub file: {e}')
            cherrypy.engine.publish('app_notify', 'ERROR', f'Error create sub file: {e}')
            return None

        return file_path


class IQIYIProtocol(DLNAProtocol):
    def __init__(self):
        super(IQIYIProtocol, self).__init__()
        self.video_info = None
        self.sync = None
        self.qyid = None
        self.sub = os.path.join(SETTING_DIR, 'iqiyi.ass')

    @property
    def handler(self):
        if self._handler is None:
            self._handler = IQIYIHandler()
        return self._handler

    def init_devices(self):
        # todo: 或许可以使用爱奇艺tv端的uuid样式，不过这个貌似没啥影响
        usn = f'tv_{Setting.get_usn()}'
        self.devices = [
            f'uuid:{usn}::upnp:rootdevice',
            f'uuid:{usn}',
            f'uuid:{usn}::urn:schemas-upnp-org:device:MediaRenderer:1',
        ]

    def init_services(self):
        super(IQIYIProtocol, self).init_services()
        self.build_action('urn:schemas-upnp-org:service:PrivateServer:1', 'PrivateServer',
                          etree.fromstring(PRIVATE_SERVER_SERVICE))
        self.build_action('urn:schemas-tencent-com:service:QPlay:1', 'QPlay',
                          etree.fromstring(QPlay_SERVICE))

    def register_service(self):
        ext = {
            'MYNAME': 'NOTAG的奇异果TV',
            'FILEMD5': 'f2a04e7661582e369d3c18c3338b96bb',  # todo 探明含义
            'IQIYIConnection': 'close',
            'IQIYIDEVICE': '3',
            'IQIYIVERSION': '2',
            'appversion': '12.2.3.143694',
            'DEVICEVERSION': '0',
            'IQIYIPORT': '39621',
            'IQIYIUDPPORT': '39622'
        }

        devices = [{'usn': i, 'nt': i[46:] if i.find('::') > 0 else i} for i in self.devices]
        cherrypy.engine.publish('ssdp_register',
                                devices,
                                f'http://{{}}:{Setting.get_port()}/description.xml',
                                'Linux/3.14.29 UPnP/1.0 IQIYIDLNA/1.0',
                                30,
                                ext)

    def set_notify(self, value):
        print('state_queue A_ARG_TYPE_NOTIFYMSG')
        self.state_queue.put(("A_ARG_TYPE_NOTIFYMSG", value))

    def send_play_cmd(self, start='0'):
        tvid = self.video_info.tvid
        pck = self.video_info.auth
        title = self.video_info.title
        print('play tvid', tvid)
        url = f'http://notag.cn/iqiyi?tvid={tvid}&pck={pck}'
        # self.protocol.set_state_url(url)
        self.renderer.set_media_url(url, start)
        # self.renderer.set_media_speed(self.desire_speed)
        self.renderer.set_media_title(title)
        cherrypy.engine.publish('renderer_av_uri', url)

        def get_extra_info():
            logger.info("start get_extra_info")
            suburl = f'http://notag.cn/iqiyi?tvid={tvid}&dm=1'
            resp = requests.get(suburl)
            print(f'resp {resp.ok} {resp.text}')
            DanmakuManager.get_danmaku(resp.text, self.sub)
            self.renderer.set_media_sub_file({
                'url': self.sub,
                'title': '弹幕'
            })
            # self.get_video_info()
            logger.info("end get_extra_info")
        threading.Thread(target=get_extra_info).start()

    # todo: 协议具体内容，data为手机发过来的，Result是电视回复的
    def PrivateServer_SendMessage(self, data):
        # logger.info(f'PrivateServer_SendMessage: {data}')
        instanceID = data['InstanceID'].value
        infor = data['Infor'].value
        print(f'instanceID {instanceID} infor {infor}')

        try:
            infor = json.loads(str(infor).encode())
            infor_type = infor['type']
            value = {"result": "true"}
            if infor_type == 'sync':
                if self.sync is None:
                    value = None
                    self.sync = True
                else:
                    value = {"result": "true"}
            elif infor_type == 'control':
                if infor['control'] == 'pushvideo':
                    self.video_info = VideoInfo(infor['value'])
                    value = {"errcode": "",
                             "key": self.video_info.key,
                             "result": "true",
                             "session": self.video_info.session
                             }
                    self.send_play_cmd()
                    state = {"control": "play",
                             "type": "sync",
                             "value": {"album_id": self.video_info.aid,
                                       "audiotrack": self.video_info.audiotrack,
                                       "boss": self.video_info.boss,
                                       "channel_id": self.video_info.channel_id,
                                       "collection_id": self.video_info.collection_id,
                                       "ctype": self.video_info.ctype,
                                       "dongle_ver": "1",
                                       "feature_bitmap": "8388603",
                                       "key": self.video_info.key,
                                       "offline_state": "0",
                                       "play_duration": "",
                                       "play_position": -1,
                                       "play_state": 1,
                                       "player_rate": 1.0,
                                       "player_state": 1,
                                       "player_type": 1,
                                       "res": "",
                                       "session": self.video_info.session,
                                       "title": self.video_info.title,
                                       "video_id": self.video_info.tvid,
                                       "vip_purchase": "false",
                                       "volume": 0},
                             "version": "12.2.3.143694"}
                    self.set_notify(state)

            elif infor_type == 'setskipinfo':
                value = {"result": infor["value"]["skip_info"]}
            elif infor_type == 'changedanmakuconfig':
                value = {"result": "false"}
            elif infor_type == 'getposition':
                value = {"key": self.video_info.key,
                         "result": "true",
                         "session": self.video_info.session,
                         "time_stamp": "711"
                         }
            elif infor_type == 'playlist':
                playlist = infor['value']['playlist'][0]
                # print(f'playlist {playlist} {playlist["title"]}')

            if value is None:
                res = ""
            else:
                res = {"control": "unknown",
                       "type": "result",
                       "value": value,
                       "version": "reserved"
                       }
        except Exception as e:
            print(f'exception e {e}')
            res = ""

        return {'Result': res}

    # 不知道具体是干嘛的
    def PrivateServer_NotifyMessage(self, data):
        print(f'PrivateServer_NotifyMessage: {data}')
        return {}

    def QPlay_SetNetwork(self, data):
        print(f'QPlay_SetNetwork {data}')
        # logger.info(f'QPlay_SetNetwork: {ssid} {key} {auth_algo} {cipher_algo}')
        return {}

    def QPlay_QPlayAuth(self, data):
        print(f'QPlay_QPlayAuth: {data}')
        res = {
            'Code': '',
            'MID': '',
            'DID': ''
        }
        return json.dumps(res)

    def QPlay_InsertTracks(self, data):
        print(f'QPlay_InsertTracks {data}')
        # logger.info(f'QPlay_InsertTracks: {queueID} {startingIndex} {tracksMetaData}')
        res = {
            'NumberOfSuccess': ''
        }
        return json.dumps(res)


class VideoInfo:
    def __init__(self, info):
        self.session = info['session']
        self.aid = info['aid']
        self.auth = info['auth']
        self.key = info['key']
        self.title = info['title']
        self.tvid = info['tvid']
        self.audiotrack = info['audiotrack']
        self.boss = info['boss']
        self.channel_id = info['channel_id']
        self.collection_id = info['collection_id']
        self.ctype = info['ctype']
