import json
import logging

from collections import defaultdict
from .lightstreamer import LSClient, Subscription


logger = logging.getLogger(__name__)


class NadexStreamApi(object):
    def __init__(self, account_id, xst, endpoint):
        self.account_id = account_id
        self.ACCOUNT = account_id.upper().replace('-', '')
        self.ls_client = LSClient(endpoint,
                                  adapter_set="InVisionProvider",
                                  user=account_id,
                                  password='XST-{}'.format(xst))
        self.ls_client_keys = []
        self.current_epics = {}
        self.epic_details = defaultdict(dict)
        self.last_hearbeat = 0

    def connect(self):
        self.ls_client_keys = []
        self.ls_client.connect()

        # iOS app subscribes to the stream in this order
        self.subscribe_account_detail()
        self.subscribe_signal_centre()
        self.subscribe_ers()
        self.subscribe_mge()
        self.subscribe_abu()
        self.subscribe_heartbeat()

    def disconnect(self):
        for key in self.ls_client_keys:
            self.unsubscribe(key)
        self.ls_client.disconnect()

    def unsubscribe(self, key):
        self.ls_client.unsubscribe(key)

    def subscribe_account_detail(self):
        s = Subscription(
            mode="MERGE",
            items=['V2-AD-AC_AVAILABLE_BALANCE'],
            fields=["ACC"],
        )
        s.addlistener(self.on_account_update)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_signal_centre(self):
        s = Subscription(
            mode="RAW",
            items=["V2-M-MESSAGE_EVENT_HANDLER|SIGNAL_CENTRE_en_US"],
            fields=["SIGNAL"]
        )
        s.addlistener(self.on_signal_centre)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_ers(self):
        s = Subscription(
            mode="RAW",
            items=["V2-M-MESSAGE_EVENT_HANDLER|{account}-ERS".format(account=self.ACCOUNT)],
            fields=["ERS"]
        )
        s.addlistener(self.on_ers)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_mge(self):
        """
        Message
        RAD - refresh account detail
        ALT - alert message
        ARS
        HIU
        LGN
        INV
        AFC
        MSG - status=<msgStatus>|body=<msg> IN_PRGRESS, CONFIRMED, WORKING, PARTIAL_FILL, REJECTED
            - order_type=<orderType>|body=<msg> OTC, DMA, FUNDING
        OPU - OP-JSON message
              OpenPositionDelete
              OpenPositionUpdate
                epic business area F
              EPIC_REPLACE
              OpenPositionEpicReplace
        OHU - Order History
        WOU - working order update
              WorkingOrderDelete
              WorkingOrderAdd
              WorkingOrderUpdate
              WorkingOrderEpicReplace
        LGT - session revocation caused by account being suspended via Wintergrate
        ALU - alert?
        ABU - Available Balance Update
              available balance
              available cache
              profit loss
        """
        s = Subscription(
            mode="RAW",
            items=["M___.MGE|{account}".format(account=self.ACCOUNT),
                   "M___.MG|{account}-ACTION".format(account=self.ACCOUNT),
                   "M___.MG|{account}-LGT".format(account=self.ACCOUNT),
                   "M___.MGE|{account}-OP-JSON".format(account=self.ACCOUNT),  # open position updates in JSON
                   "M___.MGE|{account}-WO-JSON".format(account=self.ACCOUNT),  # working order updates in JSON
                   "M___.MG|{account}-ACTION".format(account=self.ACCOUNT)
                   ],
            fields=["MGE", "ACTION", "LGT", "OP-JSON", "WO-JSON", "ACTION2"]
        )
        s.addlistener(self.on_mge)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_abu(self):
        s = Subscription(
            mode="MERGE",
            items=["V2-AD-AC_AVAILABLE_BALANCE,AC_USED_MARGIN|ACC.{account}".format(account=self.ACCOUNT)],
            fields=["availableBalance", "usedMargin"]
        )
        s.addlistener(self.on_abu)
        self.ls_client_keys.append(self.ls_client.subscribe(s))
        
    def subscribe_heartbeat(self):
        """
        Heartbeat
        """
        s = Subscription(
            mode="MERGE",
            items=['M___.HB|HB.U.HEARTBEAT.IP'],
            fields=['HB']
        )
        s.addlistener(self.on_heartbeat)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_epic(self, instrument_id, epic):
        """
        Price / Quote
        """
        if epic in self.current_epics:
            logger.info("already subscribed: %s", epic)
            return

        self.current_epics.setdefault(epic, [])

        # hierarchy instrument_id
        s = Subscription(
            mode="MERGE",
            items=['M___.MGE|HIER-{instrument_id}-JSON'.format(instrument_id=instrument_id)],
            fields=["MGE"]
        )
        s.addlistener(self.on_instrument)
        key = self.ls_client.subscribe(s)
        self.current_epics[epic].append(key)

        # price
        s = Subscription(
            mode="MERGE",
            # web client subscribes to
            #       V2-F-UBS,BS1,BD1,AK1,AS1,UTM| NB.I.AUD-USD.OPT-285-5-23Nov16.IP
            items=['V2-F-UBS,BS1,BD1,AK1,AS1,UTM|{epic}'.format(epic=epic)],
            fields=["UBS", "BS1", "BD1", "AK1", "AS1", "UTM"],
        )
        s.addlistener(self.on_price)
        key = self.ls_client.subscribe(s)
        self.current_epics[epic].append(key)

        # market
        s = Subscription(
            mode="MERGE",
            items=['V2-F-MKT|{epic}'.format(epic=epic)],
            fields=["MKT"],
        )
        key = self.ls_client.subscribe(s)
        self.current_epics[epic].append(key)

    def unsubscribe_epic(self, epic):
        self.epic_details.pop(epic)
        keys = self.current_epics.pop(epic, None)
        if keys:
            for key in keys:
                self.unsubscribe(key)

    # A simple function acting as a Subscription listener
    def on_account_update(self, message):
        """
        Account
        """
        logger.info("name=%s values=%s", message.get('name'), message.get('values'))

    def on_signal_centre(self, message):
        """
        Signal
        """
        logger.info("name=%s values=%s", message.get('name'), message.get('values'))

    def on_ers(self, message):
        logger.info("name=%s values=%s", message.get('name'), message.get('values'))

    def on_abu(self, message):
        logger.info("name=%s values=%s", message.get('name'), message.get('values'))

    def on_mge(self, message):
        name = message.get('name')
        values = message.get('values') or {}
        mge = values.get('MGE')
        if name.endswith('-JSON') and mge:
            if mge.startswith('WOU '):
                mge = json.loads(mge[4:])
                logger.info('WOU %s', mge)
                return
        logger.info("%s %s", name, mge)

    def on_heartbeat(self, message):
        try:
            self.last_heartbeat = int(message.get('values', {}).get('HB'))
        except:
            pass

    def on_instrument(self, message):
        """
        Process hierarchyId3 messages
        """
        pos = message.get('pos')
        name = message.get('name')
        values = message.get('values')
        if not name.endswith('-JSON'):
            logger.warn("%s %s", message.get('name'), message.get('values'))
            return
        msg = json.loads(values['MGE'][4:]) # skip {"MGE": "SDM {.....
        header= msg.get('header')
        body = msg.get('body')
        #---
        if header and header.get('contentType') == 'InstrumentDeletionMessage':
            instrument_id = body.get('hierarchyId3')
            epic = body.get('epic')
            logger.info("start delete on EPIC %s", epic)
            if epic in self.current_epics:
                logger.info("unsubscribe epic %s", epic)
                self.unsubscribe_epic(epic)
        elif body:
            # header.get('contentType') == 'InstrumentCreationRefresh'
            instrument_id = body.get('persistInStrument', {}).get('hierarchyId3')
            epic = body.get('persistInStrument', {}).get('epic')
            if instrument_id and epic:
                logger.info("Instrument creation refresh: %s %s", instrument_id, epic)
                self.subscribe_epic(instrument_id, epic)
            else:
                logger.info("duplicate epic to add: %s", epic)

    def on_price(self, message):
        name = message.get('name', '').split('|')[1]
        self.epic_details[name].update(message.get('values', {}))
        logger.info("PRICE: %s %s", message.get('name'), message.get('values'))

    def on_market(self, message):
        logger.info("MARKET: %s %s", message.get('name'), message.get('values'))
