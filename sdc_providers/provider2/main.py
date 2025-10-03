from __future__ import annotations

import logging
import time
import uuid
import random
from decimal import Decimal

from sdc11073.location import SdcLocation
from sdc11073.loghelper import basic_logging_setup
from sdc11073.mdib import ProviderMdib
from sdc11073.provider import SdcProvider
from sdc11073.wsdiscovery import WSDiscoverySingleAdapter
from sdc11073.xml_types import pm_qnames as pm
from sdc11073.xml_types import pm_types
from sdc11073.xml_types.dpws_types import ThisDeviceType
from sdc11073.xml_types.dpws_types import ThisModelType

# The provider we use, should match the one in consumer example
# The UUID is created from a base
base_uuid = uuid.UUID('{cc013678-79f6-403c-998f-3cc0cc050230}')
my_uuid = uuid.uuid5(base_uuid, "00001")


if __name__ == '__main__':
    # start with discovery (MDPWS) that is running on the named adapter "wlan0"
    basic_logging_setup(level=logging.INFO)

    my_discovery = WSDiscoverySingleAdapter("wlan0")
    my_discovery.start()

    # Use the simplified MDIB file for a patient monitor
    my_mdib = ProviderMdib.from_mdib_file("mdib.xml")
    print(f"My UUID is {my_uuid}")

    # Set a location context to allow easy discovery
    my_location = SdcLocation(fac='HOSP', poc='ICU', bed='Bed01')

    # Set model information for discovery
    dpws_model = ThisModelType(manufacturer='MyCompany',
                               manufacturer_url='www.mycompany.com',
                               model_name='SimplePatientMonitor',
                               model_number='1.0',
                               model_url='www.mycompany.com/model',
                               presentation_url='www.mycompany.com/model/presentation')
    dpws_device = ThisDeviceType(friendly_name='Patient Monitor',
                                 firmware_version='Version_1.0',
                                 serial_number='123456789')

    # Create a device (provider) class
    sdc_provider = SdcProvider(ws_discovery=my_discovery,
                               epr=my_uuid,
                               this_model=dpws_model,
                               this_device=dpws_device,
                               device_mdib_container=my_mdib)
    sdc_provider.start_all()

    # Set the location on our device - THIS WILL NOW WORK
    sdc_provider.set_location(my_location)

    # Get the specific metric descriptors by their handles from the MDIB
    # These handles must match the handles in your mdib.xml file
    hr_descr = my_mdib.descriptions.handle.get_one('metric.hr')
    spo2_descr = my_mdib.descriptions.handle.get_one('metric.spo2')
    temp_descr = my_mdib.descriptions.handle.get_one('metric.temp')

    # Initialize the metric states with plausible starting values
    with my_mdib.metric_state_transaction() as transaction_mgr:
        # Heart Rate
        hr_state = transaction_mgr.get_state(hr_descr.Handle)
        hr_state.mk_metric_value()
        hr_state.MetricValue.Value = Decimal(70)
        hr_state.ActivationState = pm_types.ComponentActivation.ON

        # SpO2
        spo2_state = transaction_mgr.get_state(spo2_descr.Handle)
        spo2_state.mk_metric_value()
        spo2_state.MetricValue.Value = Decimal(98)
        spo2_state.ActivationState = pm_types.ComponentActivation.ON

        # Body Temperature
        temp_state = transaction_mgr.get_state(temp_descr.Handle)
        temp_state.mk_metric_value()
        temp_state.MetricValue.Value = Decimal('37.0')
        temp_state.ActivationState = pm_types.ComponentActivation.ON

    # Main loop to simulate changing vital signs
    loop_counter = 0
    while True:
        loop_counter += 1
        try:
            with my_mdib.metric_state_transaction() as transaction_mgr:
                # Simulate Heart Rate: fluctuates every 5 seconds
                hr_state = transaction_mgr.get_state(hr_descr.Handle)
                new_hr_value = 70 + random.uniform(-5, 5)
                hr_state.MetricValue.Value = Decimal(f'{new_hr_value:.1f}')

                # Simulate SpO2: fluctuates slightly every 5 seconds
                spo2_state = transaction_mgr.get_state(spo2_descr.Handle)
                new_spo2_value = 98.5 + random.uniform(-1.5, 1.0)
                # Ensure value stays within a realistic range
                new_spo2_value = max(90.0, min(100.0, new_spo2_value))
                spo2_state.MetricValue.Value = Decimal(f'{new_spo2_value:.1f}')

                # Simulate Temperature: updates less frequently (e.g., every 30 seconds)
                if loop_counter % 6 == 0:
                    temp_state = transaction_mgr.get_state(temp_descr.Handle)
                    new_temp_value = 37.0 + random.uniform(-0.2, 0.2)
                    temp_state.MetricValue.Value = Decimal(
                        f'{new_temp_value:.1f}')

            print("Updated metric values...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("Stopping provider...")
            sdc_provider.stop_all()
            break
