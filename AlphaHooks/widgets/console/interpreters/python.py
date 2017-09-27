import sys
from code import InteractiveConsole

from qtpy.QtCore import QObject, Signal, Slot

from AlphaHooks.widgets.console.io import Stream, StringBuffer


class PythonInterpreter(QObject, InteractiveConsole):
    """
    A reimplementation of the builtin InteractiveConsole to
    work with threads.

    :signal push_command: receive commands from console_input
    :signal multi_line: signal whether more lines are needed by the
                        interpreter
    :signal error: send stderr immediately to console_log if an error
                   occurs.
    """
    push_command = Signal(str)
    push_source = Signal(str)
    multi_line = Signal(bool)
    error = Signal(str)

    def __init__(self, config, parent=None):
        super(PythonInterpreter, self).__init__(parent)
        self.config = config
        self.locals = {}
        InteractiveConsole.__init__(self, self.locals)

        # Stream
        self.stream = Stream(self)
        self.stream_buffer = StringBuffer(
            delay=config["Console"]["Write Delay"]
        )

        # Slots
        self.stream.written.connect(self.stream_buffer.consume)
        self.push_command.connect(self.command)
        self.push_source.connect(self.source)

    @Slot(str)
    def write(self, string):
        """
        Override and signal to write directly to console_log.
        Usually used to emit that a traceback happened.
        """
        self.error.emit(string)
        print(string, file=sys.__stdout__)

    def runcode(self, code):
        """
        Overrides and captures stdout and stdin from
        InteractiveConsole.
        """
        sys.stdout = self.stream
        sys.stderr = self.stream
        sys.excepthook = sys.__excepthook__
        result = InteractiveConsole.runcode(self, code)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return result

    @Slot(str)
    def command(self, command):
        """
        Get line of code to be run and signal if more lines needed.

        :param command: line retrieved from console_input on
                        returnPressed
        """
        result = self.push(command)
        self.multi_line.emit(result)

    @Slot(str)
    def source(self, source):
        result = self.runsource(source)
