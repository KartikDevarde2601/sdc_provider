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

base_uuid = uuid.UUID('{cc013678-79f6-403c-998f-3cc0cc050230}')
my_uuid = uuid.uuid5(base_uuid, "00001")


if __name__ == '__main__':

    basic_logging_setup(level=logging.INFO)

    my_discovery = WSDiscoverySingleAdapter("en0")
    my_discovery.start()

    my_mdib = ProviderMdib.from_mdib_file("mdib.xml")
    print(f"My UUID is {my_uuid}")

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

    ibp_mean_descr = my_mdib.descriptions.handle.get_one('metric.ibp.mean')
    cvp_descr = my_mdib.descriptions.handle.get_one('metric.cvp')
    pap_mean_descr = my_mdib.descriptions.handle.get_one('metric.pap.mean')

    with my_mdib.metric_state_transaction() as transaction_mgr:

        ibp_state = transaction_mgr.get_state(ibp_mean_descr.Handle)
        ibp_state.mk_metric_value()
        ibp_state.MetricValue.Value = Decimal(88)
        ibp_state.ActivationState = pm_types.ComponentActivation.ON

        cvp_state = transaction_mgr.get_state(cvp_descr.Handle)
        cvp_state.mk_metric_value()
        cvp_state.MetricValue.Value = Decimal(10)
        cvp_state.ActivationState = pm_types.ComponentActivation.ON

        pap_state = transaction_mgr.get_state(pap_mean_descr.Handle)
        pap_state.mk_metric_value()
        pap_state.MetricValue.Value = Decimal(65)
        pap_state.ActivationState = pm_types.ComponentActivation.ON

        # Main loop to simulate changing vital signs
    loop_counter = 0
    while True:
        loop_counter += 1
        try:
            with my_mdib.metric_state_transaction() as transaction_mgr:
                # Simulate Heart Rate: fluctuates every 5 seconds
                ibp_state = transaction_mgr.get_state(ibp_mean_descr.Handle)
                new_ibp_value = 65 + random.uniform(-5, 5)
                ibp_state.MetricValue.Value = Decimal(f'{new_ibp_value:.1f}')

                # Simulate SpO2: fluctuates slightly every 5 seconds
                cvp_state = transaction_mgr.get_state(cvp_descr.Handle)
                new_cvp_value = 98.5 + random.uniform(-1.5, 1.0)
                # Ensure value stays within a realistic range
                new_cvp_value = max(90.0, min(100.0, new_cvp_value))
                cvp_state.MetricValue.Value = Decimal(f'{new_cvp_value:.1f}')

                # Simulate Temperature: updates less frequently (e.g., every 30 seconds)
                if loop_counter % 6 == 0:
                    pap_state = transaction_mgr.get_state(
                        pap_mean_descr.Handle)
                    new_pap_value = 37.0 + random.uniform(-0.2, 0.2)
                    pap_state.MetricValue.Value = Decimal(
                        f'{new_pap_value:.1f}')

            print("Updated metric values...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("Stopping provider...")
            sdc_provider.stop_all()
            break
