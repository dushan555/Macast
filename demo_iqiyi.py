# Copyright (c) 2022 by xfangfang. All Rights Reserved.
#
# IQIYI protocol
#
# Macast Metadata
# <macast.title>IQIYI Protocol</macast.title>
# <macast.protocol>IQIYIProtocol</macast.protocol>
# <macast.platform>darwin,win32,linux</macast.platform>
# <macast.version>0.1</macast.version>
# <macast.host_version>0.71</macast.host_version>
# <macast.author></macast.author>
# <macast.desc>IQIYI protocol support for Macast.</macast.desc>


import cherrypy
import logging
import json
from lxml import etree

from macast.protocol import DLNAProtocol, DLNAHandler, SERVICE_STATE_OBSERVED
from macast.utils import XMLPath, load_xml, Setting

# todo: A_ARG_TYPE_NOTIFYMSG 改变时会动态的通知客户端（DLNA订阅事件）
# todo: 我注意到有这样的数据，但是不太确定具体数据内容是什么
# tips: 在数据改变时调用 self.set_state('A_ARG_TYPE_NOTIFYMSG', '')即可
SERVICE_STATE_OBSERVED.update({
    'PrivateServer': ['A_ARG_TYPE_NOTIFYMSG']
})

PrivateServer = """<scpd xmlns="urn:schemas-upnp-org:service-1-0">
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

logger = logging.getLogger("IQIYIRotocol")


@cherrypy.expose
class IQIYIHandler(DLNAHandler):
    def build_description(self):
        print('ddd build_description')
        self.description = load_xml(XMLPath.DESCRIPTION.value).format(
            # 括号中的内容原本应为服务32位ip的后八位，如：192.168.1.111，则为 111
            friendly_name='客厅的奇异果TV(Macast)',
            manufacturer="Microsoft Corporation",
            manufacturer_url="http://www.microsoft.com",
            model_description="TVGUO Media Renderer",
            model_name="Windows Media Player",
            model_url="http://go.microsoft.com/fwlink/?LinkId=105927",
            model_number="",
            uuid=Setting.get_usn(),
            # TV端uuid规范格式
            # 'tv_00000000000000000000000000000000_1646000000000_0000000000_0000000',
            # todo 探明id生成算法
            serial_num="",
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
        print(f'ddd GET param {param} xml {xml}')
        if param == 'dlna' and xml == 'PrivateServer.xml':
            return PrivateServer
        if param == 'dlna' and xml == 'QPlay.xml':
            return QPlay_SERVICE
        return super(IQIYIHandler, self).GET(param, xml, **kwargs)

    # 下列三个方法本来是不需要重写的
    # 原因是爱奇艺手机客户端为了加快投屏速度，没有从description.xml中读取地址，而是向固定的地址发送数据
    #
    # 当注册SSDP时，将SERVER值改为其他内容后，（目前：Linux/3.14.29 UPnP/1.0 IQIYIDLNA/1.0）
    # 手机客户端就会读取description.xml中规范的地址，不过那样功能虽然正常但是在投屏搜索时不会标注"推荐"字样，
    # 速度也会稍慢一点点（无感知）
    def POST(self, service=None, param=None, *args, **kwargs):
        if service == '_urn:schemas-upnp-org:service:PrivateServer_control':
            service = 'PrivateServer'
            param = 'action'
        return super(IQIYIHandler, self).POST(service, param, *args, **kwargs)

    def SUBSCRIBE(self, service="", param=""):
        if service == '_urn:schemas-upnp-org:service:PrivateServer_event':
            service = 'PrivateServer'
            param = 'event'
        return super(IQIYIHandler, self).SUBSCRIBE(service, param)

    def UNSUBSCRIBE(self, service="", param=""):
        if service == '_urn:schemas-upnp-org:service:PrivateServer_event':
            service = 'PrivateServer'
            param = 'event'
        return super(IQIYIHandler, self).UNSUBSCRIBE(service, param)


class IQIYIProtocol(DLNAProtocol):

    def __init__(self):
        super(IQIYIProtocol, self).__init__()

    @property
    def handler(self):
        if self._handler is None:
            self._handler = IQIYIHandler()
        return self._handler

    def init_devices(self):
        # todo: 或许可以使用爱奇艺tv端的uuid样式，不过这个貌似没啥影响
        usn = Setting.get_usn()
        self.devices = [
            f'uuid:{usn}::upnp:rootdevice',
            f'uuid:{usn}',
            f'uuid:{usn}::urn:schemas-upnp-org:device:MediaRenderer:1',
            f'uuid:{usn}::urn:schemas-upnp-org:service:RenderingControl:1',
            f'uuid:{usn}::urn:schemas-upnp-org:service:ConnectionManager:1',
            f'uuid:{usn}::urn:schemas-upnp-org:service:AVTransport:1',
            f'uuid:{usn}::urn:schemas-upnp-org:service:PrivateServer:1',
            f'uuid:{usn}::urn:schemas-upnp-org:service:QPlay:1',
        ]

    def init_services(self, description=XMLPath.DESCRIPTION.value):
        super(IQIYIProtocol, self).init_services()
        self.build_action('urn:schemas-upnp-org:service:PrivateServer:1',
                          'PrivateServer',
                          etree.fromstring(PrivateServer))
        self.build_action('urn:schemas-tencent-com:service:QPlay:1', 'QPlay',
                          etree.fromstring(QPlay_SERVICE))

    def register_service(self):
        ext = {
            'MYNAME': 'NOTAG的奇异果TV',
            'FILEMD5': '00000000000000000000000000000000',  # todo 探明含义
            'IQIYIConnection': 'close',
            'IQIYIDEVICE': '3',
            'IQIYIVERSION': '2',
            'appversion': '12.2.1.143694',
            'DEVICEVERSION': '0',
            'IQIYIPORT': '39621',
            'IQIYIUDPPORT': '39622'
        }
        devices = [{'usn': i, 'nt': i[43:] if i[43:] != '' else i} for i in self.devices]
        cherrypy.engine.publish('ssdp_register',
                                devices,
                                f'http://{{}}:{Setting.get_port()}/description.xml',
                                'Linux/3.14.29 UPnP/1.0 IQIYIDLNA/1.0',
                                30,
                                ext)

    # 如下两个方法的定义在：PrivateServer

    # todo: 协议具体内容，data为手机发过来的，Result是电视回复的
    def PrivateServer_SendMessage(self, data):
        logger.info(f'PrivateServer_SendMessage: {data}')

        res = {"control": "unknown",
               "type": "result",
               "value": {"result": "false"},
               "version": "reserved"
               }
        return {'Result': json.dumps(res).replace('"', '&quot;')}

    # 不知道具体是干嘛的
    def PrivateServer_NotifyMessage(self, data):
        logger.info(f'PrivateServer_NotifyMessage: {data}')
        return {}


if __name__ == '__main__':
    from macast import gui
    from macast_renderer.mpv import MPVRenderer

    Setting.setup_logger()
    gui(renderer=MPVRenderer(path='mpv'), protocol=IQIYIProtocol())
