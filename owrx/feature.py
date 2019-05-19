import os
import subprocess
from functools import reduce
from operator import and_

import logging
logger = logging.getLogger(__name__)


class UnknownFeatureException(Exception):
    pass

class FeatureDetector(object):
    features = {
        "core": [ "csdr", "nmux" ],
        "rtl_sdr": [ "rtl_sdr" ],
        "sdrplay": [ "rx_tools" ],
        "hackrf": [ "hackrf_transfer" ],
        "digital_voice_digiham": [ "digiham", "sox" ],
        "digital_voice_dsd": [ "dsd", "sox" ]
    }

    def feature_availability(self):
        return {name: self.is_available(name) for name in FeatureDetector.features}

    def is_available(self, feature):
        return self.has_requirements(self.get_requirements(feature))

    def get_requirements(self, feature):
        try:
            return FeatureDetector.features[feature]
        except KeyError:
            raise UnknownFeatureException("Feature \"{0}\" is not known.".format(feature))

    def has_requirements(self, requirements):
        passed = True
        for requirement in requirements:
            methodname = "has_" + requirement
            if hasattr(self, methodname) and callable(getattr(self, methodname)):
                passed = passed and getattr(self, methodname)()
            else:
                logger.error("detection of requirement {0} not implement. please fix in code!".format(requirement))
        return passed

    def command_is_runnable(self, command):
        return os.system("{0} 2>/dev/null >/dev/null".format(command)) != 32512

    def has_csdr(self):
        return self.command_is_runnable("csdr")

    def has_nmux(self):
        return self.command_is_runnable("nmux --help")

    def has_rtl_sdr(self):
        return self.command_is_runnable("rtl_sdr --help")

    def has_rx_tools(self):
        return self.command_is_runnable("rx_sdr --help")

    """
    To use a HackRF, compile the HackRF host tools from its "stdout" branch:
     git clone https://github.com/mossmann/hackrf/
     cd hackrf
     git fetch
     git checkout origin/stdout
     cd host
     mkdir build
     cd build
     cmake .. -DINSTALL_UDEV_RULES=ON
     make
     sudo make install
    """
    def has_hackrf_transfer(self):
        # TODO i don't have a hackrf, so somebody doublecheck this.
        # TODO also check if it has the stdout feature
        return self.command_is_runnable("hackrf_transfer --help")

    def command_exists(self, command):
        return os.system("which {0}".format(command)) == 0

    def has_digiham(self):
        # the digiham tools expect to be fed via stdin, they will block until their stdin is closed.
        def check_with_stdin(command):
            try:
                process = subprocess.Popen(command, stdin=subprocess.PIPE)
                process.communicate("")
                return process.wait() == 0
            except FileNotFoundError:
                return False
        return reduce(and_,
                      map(
                          check_with_stdin,
                          ["rrc_filter", "ysf_decoder", "dmr_decoder", "mbe_synthesizer", "gfsk_demodulator"]
                      ),
                      True)

    def has_dsd(self):
        return self.command_is_runnable("dsd")

    def has_sox(self):
        return self.command_is_runnable("sox")