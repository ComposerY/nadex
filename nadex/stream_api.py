import json

from .lightstreamer import LSClient, Subscription


class NadexStreamApi(object):
    def __init__(self, account_id, xst, endpoint):
        self.account_id = account_id
        self.ACCOUNT = account_id.upper().replace('-', '')
        self.ls_client = LSClient(endpoint,
                                  adapter_set="InVisionProvider",
                                  user=account_id,
                                  password='XST-{}'.format(xst))
        self.ls_client_keys = []

    def connect(self):
        self.ls_client_keys = []
        self.ls_client.connect()

        # iOS app subscribes to the stream in this order
        self.subscribe_account_detail()
        self.subscribe_signal_centre()
        self.subscribe_ers()
        self.subscribe_mge()
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
        s = Subscription(
            mode="RAW",
            items=["M___.MGE|{account}".format(account=self.ACCOUNT),
                   "M___.MG|{account}-ACTION".format(account=self.ACCOUNT),
                   "M___.MG|{account}-LGT".format(account=self.ACCOUNT),
                   "M___.MGE|{account}-OP-JSON".format(account=self.ACCOUNT),  # op? in JSON format
                   "M___.MGE|{account}-WO-JSON".format(account=self.ACCOUNT),  # working order in JSON format
                   "M___.MG|{account}-ACTION".format(account=self.ACCOUNT)
                   ],
            fields=["MGE", "ACTION", "LGT", "OP-JSON", "WO-JSON", "ACTION2"]
        )
        s.addlistener(self.on_mge)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_heartbeat(self):
        s = Subscription(
            mode="MERGE",
            items=['M___.HB|HB.U.HEARTBEAT.IP'],
            fields=['HB']
        )
        s.addlistener(self.on_heartbeat)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    def subscribe_price_update(self, instrument_id, epic):
        # hierarchy instrument_id
        s = Subscription(
            mode="MERGE",
            items=['M___.MGE|HIER-{instrument_id}-JSON'.format(instrument_id=instrument_id)],
            fields=["MGE"]
        )
        s.addlistener(self.on_instrument)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

        # price
        s = Subscription(
            mode="MERGE",
            items=['V2-F-HIG,CPC,UBS,AS1,CBS,BS1,AK1,CPT,LOW,CSP,UTM,BD1|{epic}'.format(epic=epic)],
            fields=["HIG", "CPC", "UBS", "AS1", "CBS", "BS1", "AK1", "CPT", "LOW", "CSP", "UTM", "BD1"],
        )
        s.addlistener(self.on_price)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

        # market
        s = Subscription(
            mode="MERGE",
            items=['V2-F-MKT|{epic}'.format(epic=epic)],
            fields=["MKT"],
        )
        s.addlistener(self.on_market)
        self.ls_client_keys.append(self.ls_client.subscribe(s))

    # A simple function acting as a Subscription listener
    def on_account_update(self, message):
        print(message.get('name'), message.get('values'))

    def on_signal_centre(self, message):
        print(message.get('name'), message.get('values'))

    def on_ers(self, message):
        print(message.get('name'), message.get('values'))

    def on_mge(self, message):
        name = message.get('name')
        values = message.get('values') or {}
        mge = values.get('MGE')
        if name.endswith('-JSON') and mge:
            if mge.startswith('WOU '):
                mge = json.loads(mge[4:])
                print('WOU', mge)
                return
        print(name, mge)

    def on_heartbeat(self, message):
        print(message.get('name'), message.get('values'))

    def on_instrument(self, message):
        print(message.get('name'), message.get('values'))

    def on_price(self, item_update):
        name = item_update.get('name', '').split('|')[1]
        print(name, item_update.get('values'))

    def on_market(self, message):
        print(message.get('name'), message.get('values'))