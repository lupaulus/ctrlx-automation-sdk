#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2021-2022 Bosch Rexroth AG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import time
from datetime import datetime
from typing import List
import flatbuffers

import ctrlxdatalayer
from ctrlxdatalayer.variant import Result, Variant
from comm.datalayer import SubscriptionProperties

from helper.ctrlx_datalayer_helper import get_client

def main():

    print()
    print("=================================================================")
    print("sdk-py-datalayer-client - A ctrlX Data Layer Client App in Python")
    print("=================================================================")

    with ctrlxdatalayer.system.System("") as datalayer_system:
        datalayer_system.start(False)

        datalayer_client, datalayer_client_connection_string = get_client(datalayer_system)
        if datalayer_client is None:
            print("ERROR Connecting", datalayer_client_connection_string, "failed.")
            sys.exit(1)

        with datalayer_client: # datalayer_client is closed automatically when leaving with block

            if datalayer_client.is_connected() is False:
                print("ERROR Data Layer is NOT connected:", datalayer_client_connection_string)
                sys.exit(2)


            # Define the subscription properties by using Flatbuffers class SubscriptionProperties
            builder = flatbuffers.Builder(1024)
            id = builder.CreateString("sdk-py-sub")
            SubscriptionProperties.SubscriptionPropertiesStart(builder)
            SubscriptionProperties.SubscriptionPropertiesAddId(builder, id)
            SubscriptionProperties.SubscriptionPropertiesAddKeepaliveInterval(builder, 10000)
            SubscriptionProperties.SubscriptionPropertiesAddPublishInterval(builder, 1000)
            SubscriptionProperties.SubscriptionPropertiesAddErrorInterval(builder, 10000)
            properties = SubscriptionProperties.SubscriptionPropertiesEnd(builder)
            builder.Finish(properties)
            sub_prop = Variant()
            sub_prop.set_flatbuffers(builder.Output())

            # Create subscription
            print("INFO Creating subscription")
            result, sub = datalayer_client.create_subscription_sync(sub_prop, cb_subscription_sync)
            if result is not Result.OK:
                print("ERROR Creating subscription failed:", result)

            # Add subscription node
            print("INFO Add subscription node")
            sub_adr = "framework/metrics/system/cpu-utilisation-percent"
            result = sub.subscribe(sub_adr)   
            if result is not Result.OK:
                print("ERROR Adding subscription node failed:", result)

            while datalayer_client.is_connected():

                dt_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")

                addr = "framework/metrics/system/memused-percent"
                result, read_var = datalayer_client.read_sync(addr)
                val = read_var.get_float64()
                print("INFO read_sync: %s, %s: %f" % (dt_str, addr, val))
               
                time.sleep(5.0)

            print("ERROR Data Layer is NOT connected")
            print("INFO Closing subscription")
            sub.close()

        stop_ok = datalayer_system.stop(False)  # Attention: Doesn't return if any provider or client instance is still running
        print("System Stop", stop_ok)


# Response notify callback function
def cb_subscription_sync(result: Result, items: List[ctrlxdatalayer.subscription.NotifyItem], userdata):
    if result is not Result.OK:
        print("ERROR notify subscription:", result)
        return
    timestamp = items[0].get_timestamp()
    dt = datetime.fromtimestamp(timestamp/10000000-11644473600) # convert ldap to unix timestamp
    dt_str = dt.strftime("%d/%m/%Y %H:%M:%S.%f")
    address = items[0].get_address()
    val = Variant.get_float64(items[0].get_data())
    print("INFO Subscription notification: %s, %s: %f" % (dt_str, address, val))


if __name__ == '__main__':
    main()