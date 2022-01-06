from monitoring.monitorlib.typing import ImplicitDict
from typing import List
from monitoring.monitorlib.scd import Volume4D

SCOPE_SCD_QUALIFIER_INJECT = 'utm.inject_test_data'

## Definitions around operational intent data that need to be submitted to the test injection interface
  
class OperationalIntentTestInjection(ImplicitDict):
    ''' A class to hold data for operational intent data that will be submitted to the SCD testing interface. '''
    state: str
    priorty: int = 0
    volumes: List[Volume4D]
    off_nominal_volumes: List[Volume4D]= []

### End of definitions around operational intent data

## Definitions around flight authorisation data that need to be submitted to the test injection interface
   
class FlightAuthorisationData(ImplicitDict):
    '''A class to hold information about Flight Authorisation Test '''
    
    uas_serial_number: str
    operation_mode: str
    operation_category: str
    uas_class: str
    identification_technologies: List[str]
    uas_type_certificate: str
    connectivity_methods: List[str]
    endurance_minutes: int
    emergency_procedure_url: str
    operator_id: str
    uas_id: str    

### End of definitions around flight authorisation data

class InjectFlightRequest(ImplicitDict):
    ''' A class to hold the details of a test injection payload '''
    operational_intent: OperationalIntentTestInjection
    flight_authorisation: FlightAuthorisationData

class InjectFlightResponse(ImplicitDict):
    ''' A class to hold test flight submission response '''
    result: str
    operational_intent_id: str