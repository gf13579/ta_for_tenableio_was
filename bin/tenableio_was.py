import sys
import os
import json
from loguru import logger
import bin.tenablelib as tenablelib
from pprint import pprint

log_file = os.environ["SPLUNK_HOME"] + "/var/log/splunk/ta_for_tenableio_was.log"
logger.remove()
logger.add(sink=log_file, level="INFO")
logger.add(sink=sys.stderr, level="ERROR")

# for development
logger.add(sink=log_file, level="DEBUG")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.modularinput import *
import splunklib.results as results


class MyScript(Script):
    """All modular inputs should inherit from the abstract base class Script
    from splunklib.modularinput.script.
    They must override the get_scheme and stream_events functions, and,
    if the scheme returned by get_scheme has Scheme.use_external_validation
    set to True, the validate_input function.
    """

    def get_scheme(self):
        # The name Splunk will display to users for this input.
        scheme = Scheme("Tenable IO WAS")

        scheme.description = "Ingest WAS results from tenable.io."
        scheme.use_external_validation = False

        # Set to false so each input can have an optional interval parameter
        scheme.use_single_instance = False

        earliest_argument = Argument("earliest_date")
        earliest_argument.title = "Query Date Range (days)"
        earliest_argument.data_type = Argument.data_type_string
        earliest_argument.description = (
            "Filter results by discovery/index date, where supported. 0 = all time."
        )
        scheme.add_argument(earliest_argument)
        return scheme

    def validate_input(self, validation_definition):
        """In this example we are using external validation to verify that min is
        less than max. If validate_input does not raise an Exception, the input is
        assumed to be valid. Otherwise it prints the exception as an error message
        when telling splunkd that the configuration is invalid.

        When using external validation, after splunkd calls the modular input with
        --scheme to get a scheme, it calls it again with --validate-arguments for
        each instance of the modular input in its configuration files, feeding XML
        on stdin to the modular input to do validation. It is called the same way
        whenever a modular input's configuration is edited.

        :param validation_definition: a ValidationDefinition object
        """
        # Get the parameters from the ValidationDefinition object,

        earliest_date = str(validation_definition.parameters["earliest_date"])
        if not earliest_date or (earliest_date == ""):
            earliest_date = "0"

        logger.debug(f"Chance to validate earliest_date: {earliest_date}")

        # lazy validation
        if not earliest_date.isascii():
            raise ValueError("earliest_date must be a datetime string")


    def stream_events(self, inputs, ew):
        """This function handles all the action: splunk calls this modular input
        without arguments, streams XML describing the inputs to stdin, and waits
        for XML on stdout describing events.

        If you set use_single_instance to True on the scheme in get_scheme, it
        will pass all the instances of this input to a single instance of this
        script.

        :param inputs: an InputDefinition object
        :param ew: an EventWriter object
        """

        # there should only be one input as we're setting scheme.use_single_instance = False
        stanza = list(inputs.inputs.keys())[0]
        logger.debug(f"stanza is {stanza}")

        # Get mod input params
        earliest_date = str(inputs.inputs[stanza]["earliest_date"])

        api_key = None
        storage_passwords = self.service.storage_passwords
        for k in storage_passwords:
            p = str(k.content.get("clear_password"))
            realm = str(k.content.get("realm"))
            if realm == "ta_for_tenableio_was_realm":
                api_key = p
                break

        tlib = tenablelib.dorklib(
            api_key=api_key,
        )

        for r in tlib.get_results(earliest_date=earliest_date):
            if isinstance(r, list):
                for list_item in r:
                    event = Event()
                    event.stanza = stanza
                    event.data = json.dumps(list_item)
                    # Tell the EventWriter to write this event
                    ew.write_event(event)
            else:
                ew.write_event(event)
                event = Event()
                event.stanza = stanza
                event.data = json.dumps(r)
                # Tell the EventWriter to write this event
                ew.write_event(event)

        logger.debug(f"Finished queries. Events created: {len(results)}")

if __name__ == "__main__":
    sys.exit(MyScript().run(sys.argv))
