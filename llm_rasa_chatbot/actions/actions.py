from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
from datetime import datetime
import requests
import threading
import time

class TokenManager:
    def __init__(self, api_url, username, password, refresh_interval=600):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.token = None
        self.refresh_interval = refresh_interval
        self.token_expiry_time = 0

    def _refresh_token(self):
        while True:
            try:
                print("Refreshing token...")
                auth_url = f"{self.api_url}/api/oauth/token"
                data = {
                    "client_id": self.username,
                    "client_secret": self.password,
                    "grant_type": "client_credentials",
                     # "client_id": "administration",
                     # "grant_type": "password",
                     # "scopes": "write",
                     # "username": "admin",
                     # "password": "shopware"
                }
                response = requests.post(auth_url, data=data)

                if response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data.get("access_token")
                    print(f"New token: {self.token}")
                    self.token_expiry_time = time.time() + token_data.get("expires_in", 600)
                else:
                    print(f"Failed to get token: {response.status_code}, {response.text}")

            except Exception as e:
                print(f"Error refreshing token: {e}")

            # Wait until the next refresh interval
            time.sleep(self.refresh_interval)

    def start_token_refresh(self):
        refresh_thread = threading.Thread(target=self._refresh_token, daemon=True)
        refresh_thread.start()

    def get_token(self):
        return self.token

token_manager = TokenManager(
    
)
token_manager.start_token_refresh()


class ActionCheckSufficientFunds(Action):
    def name(self) -> Text:
        return "action_check_sufficient_funds"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # hard-coded balance for tutorial purposes. in production this
        # would be retrieved from a database or an API
        balance = 1000
        transfer_amount = tracker.get_slot("amount")
        has_sufficient_funds = transfer_amount <= balance
        return [SlotSet("has_sufficient_funds", has_sufficient_funds)]

class ActionCheckTrackingNumber(Action):
    def name(self):
        return "action_check_tracking_number"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        order_number = tracker.get_slot('order_number')
        order_last_name = tracker.get_slot('order_last_name')

        token = token_manager.get_token()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = {
            "filter[0][type]": "equals",
            "filter[0][field]": "orderNumber",
            "filter[0][value]": order_number,
        }

        try:
            response = requests.get(f"{token_manager.api_url}/api/order?associations[deliveries][]", headers=headers, params=params)

            if response.status_code == 200:
                order_data = response.json()
                order_data = order_data['data'][0]

                if order_last_name.lower() in (order_data["orderCustomer"]["lastName"]).lower():

                    tracking_number = None
                    if order_data["deliveries"][0]["trackingCodes"]:
                        tracking_number = order_data["deliveries"][0]["trackingCodes"][0]
                    else:
                        tracking_number = order_data["deliveries"][1]["trackingCodes"][0]
                    
                    SlotSet("order_number", None)
                    SlotSet("order_last_name", None)
                    return [SlotSet("tracking_number", tracking_number)]

                else:
                    #dispatcher.utter_message(text="Der Bestellungsnummer und das Bestelldatum stimmen nicht überein. Bitte Versuchen Sie nocheinmal.")
                    SlotSet("order_number", None)
                    SlotSet("order_last_name", None)
                    return [SlotSet("tracking_number", None)]
            else:
                #dispatcher.utter_message(text="Ihre Bestellung wurde nicht gefunden. Bitte versuchen Sie es erneut.")
                #tracker.slots["order_validation"] = False
                SlotSet("order_number", None)
                SlotSet("order_last_name", None)
                return [SlotSet("tracking_number", None)]

        except Exception as e:
            #dispatcher.utter_message(text=f"Leider is etwas schief gelauen.Entweder könnnen Sie sich an Kundenservice wenden, oder was kann ich sonst für Sie tun?")
            SlotSet("order_number", None)
            SlotSet("order_last_name", None)
            return [SlotSet("tracking_number", None)]
        
class ActionResetAllSlots(Action):
    def name(self) -> str:
        return "reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        SlotSet("order_number", None)
        SlotSet("order_last_name", None)
        SlotSet("country", None)
        SlotSet("stone_size", None)
        return [AllSlotsReset()]