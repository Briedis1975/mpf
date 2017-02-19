"""Contains the Timed Switch device class."""

from mpf.core.device_monitor import DeviceMonitor
from mpf.core.mode_device import ModeDevice
from mpf.core.system_wide_device import SystemWideDevice


@DeviceMonitor("activation_count")
class TimedSwitch(SystemWideDevice, ModeDevice):

    """Timed Switch device."""

    config_section = 'timed_switches'
    collection = 'timed_switches'
    class_label = 'timed_switch'

    def __init__(self, machine, name):
        """Initialize Timed Switch."""
        super().__init__(machine, name)
        self.activation_count = 0

    def validate_and_parse_config(self, config: dict, is_mode_config: bool) -> dict:
        """Validate and parse config."""
        config = super().validate_and_parse_config(config, is_mode_config)

        for x in ('active', 'released'):
            if not config['events_when_{}'.format(x)]:
                config['events_when_{}'.format(x)] = [
                    "{}_{}".format(self.name, x)]

        if config['state'] == 'active':
            config['state'] = True
        elif config['state'] == 'inactive':
            config['state'] = False

        return config

    def _initialize(self):

        for tag in self.config['switch_tags']:
            for switch in self.machine.switches.items_tagged(tag):
                if switch not in self.config['switches']:
                    self.config['switches'].append(switch)

        self._register_switch_handlers()

    @property
    def can_exist_outside_of_game(self):
        """Return true if this device can exist outside of a game."""
        return True

    def device_removed_from_mode(self, mode):
        """Mode ended.

        Args:
            mode: mode which stopped
        """
        del mode
        self._remove_switch_handlers()

    def _register_switch_handlers(self):
        for switch in self.config['switches']:
            switch.add_handler(self._activate,
                               state=1 if self.config['state'] else 0,
                               ms=self.config['time'], return_info=False)
            switch.add_handler(self._deactivate,
                               state=0 if self.config['state'] else 1,
                               ms=0, return_info=False)

    def _remove_switch_handlers(self):
        for switch in self.config['switches']:
            switch.remove_handler(self._activate,
                                  state=1 if self.config['state'] else 0)
            switch.remove_handler(self._deactivate,
                                  state=0 if self.config['state'] else 1)

    def _activate(self):
        if not self.activation_count:
            for event in self.config['events_when_active']:
                self.machine.events.post(event)

        self.activation_count += 1

    def _deactivate(self):
        self.activation_count -= 1

        if not self.activation_count:
            for event in self.config['events_when_released']:
                self.machine.events.post(event)

        if self.activation_count < 0:
            self.activation_count = 0

        '''event: flipper_cradle

        desc: Posted when one of the flipper buttons has been active for 3
        seconds.

        Note that in order for this event to work, you have to add
        ``left_flipper`` as a tag to the switch for your left flipper,
        and ``right_flipper`` to your right flipper.

        See :doc:`/config/timed_switches` for details.
        '''

        '''event: flipper_cradle_release

        desc: Posted when one of the flipper buttons that has previously
        been active for more than 3 seconds has been released.

        If the player pushes in one flipper button for more than 3 seconds,
        and then the second one and holds it in for more than 3 seconds,
        this event won't be posted until both buttons have been released.

        Note that in order for this event to work, you have to add
        ``left_flipper`` as a tag to the switch for your left flipper,
        and ``right_flipper`` to your right flipper.

        See :doc:`/config/timed_switches` for details.
        '''
