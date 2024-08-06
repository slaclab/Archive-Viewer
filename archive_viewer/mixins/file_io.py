from os import getenv
from re import compile
from typing import Tuple
from pathlib import Path
from datetime import (datetime, timedelta)
from urllib.parse import urlparse
from qtpy.QtWidgets import (QMessageBox, QFileDialog)
from config import (logger, save_file_dir)
from av_file_convert import ArchiveViewerFileConverter


class FileIOMixin:
    """Mixins class to manage the file imports and exports for Trace"""
    def file_io_init(self) -> None:
        """Initialize the File IO capabilities of Trace by saving a default
        path and creating an ArchiveViewerFileConverter object
        """
        self.io_path = save_file_dir
        self.converter = ArchiveViewerFileConverter()

    def export_save_file(self) -> None:
        """Prompt the user for a file to export config data to"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Archive Viewer",
                                                   str(self.io_path),
                                                   "Python Archive Viewer (*.pyav)")
        file_name = Path(file_name)
        if file_name.is_dir():
            logger.warning("No file name provided")
            return

        try:
            self.io_path = file_name.parent
            self.converter.export_file(file_name, self.ui.archiver_plot)
        except FileNotFoundError as e:
            logger.error(e)
            self.export_save_file()

    def import_save_file(self, file_name: str | Path = None) -> None:
        """Prompt the user for which config file to import from"""
        # Get the save file from the user
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self, "Open Archive Viewer",
                                                       str(self.io_path),
                                                       "Python Archive Viewer (*.pyav);;"
                                                       + "Java Archive Viewer (*.xml);;"
                                                       + "All Files (*)")
        file_name = Path(file_name)
        if not file_name.is_file():
            return

        # Import the given file, and convert it from Java Archive Viewer's
        # format to Trace's format if necessary
        try:
            file_data = self.converter.import_file(file_name)
            if self.converter.import_is_xml():
                file_data = self.converter.convert_data(file_data)
            self.io_path = file_name.parent
        except FileNotFoundError as e:
            logger.error(e)
            self.import_save_file()
            return

        # Confirm the PYDM_ARCHIVER_URL is the same as the imported Archiver URL
        # If they are not the same, prompt the user to confirm continuing
        import_url = urlparse(file_data['archiver_url'])
        archiver_url = urlparse(getenv("PYDM_ARCHIVER_URL"))
        if import_url.hostname != archiver_url.hostname:
            ret = QMessageBox.warning(self,
                                      "Import Error",
                                      "The config file you tried to open reads from a different archiver.\n"
                                      f"\nCurrent archiver is:\n{archiver_url.hostname}\n"
                                      f"\nAttempted import uses:\n{import_url.hostname}",
                                      QMessageBox.Ok | QMessageBox.Cancel,
                                      QMessageBox.Ok)
            if ret == QMessageBox.Cancel:
                return

        # Parse the time range for the X-Axis
        try:
            start_str = file_data['time_axis']['start']
            end_str = file_data['time_axis']['end']
            start_dt, end_dt = IOTimeParser.parse_times(start_str, end_str)
            logger.debug(f"Starting time: {start_dt}")
            logger.debug(f"Ending time: {end_dt}")
        except ValueError as e:
            logger.error(e)
            self.import_save_file()
            return

        # Set the models to use the file data
        self.axis_table_model.set_model_axes(file_data['y-axes'])
        self.curves_model.set_model_curves(file_data['curves'])

        # Enable auto scroll if the end time is "now"
        self.ui.cursor_scale_btn.click()
        if end_str == "now":
            delta = end_dt - start_dt
            timespan = delta.total_seconds()
            self.ui.archiver_plot.setAutoScroll(True, timespan)
        else:
            x_range = (start_dt.timestamp(), end_dt.timestamp())
            self.ui.archiver_plot.plotItem.disableXAutoRange()
            self.ui.archiver_plot.plotItem.setXRange(*x_range)


class IOTimeParser:
    """Collection of classmethods to parse a given date time string. The
    string can contain an absolute date and time, or a date and time that
    are relative to another time or even each other.
    """
    full_relative_re = compile(r"^([+-]?\d+[yMwdHms] ?)*\s*((?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?)?$")
    full_absolute_re = compile(r"^\d{4}-[01]\d-[0-3]\d\s*((?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?)?$")

    relative_re = compile(r"(?<!\S)(?:[+-]?\d+[yMwdHms])")
    date_re = compile(r"^\d{4}-[01]\d-[0-3]\d")
    time_re = compile(r"(?:[01]\d|2[0-3])(?::[0-5]\d)(?::[0-5]\d(?:.\d*)?)?")

    @classmethod
    def is_relative(cls, input_str: str) -> bool:
        """Check if the given string is a relative time (e.g. '+1d',
        '-8h', '-1w 08:00')

        Parameters
        ---------
        input_str : str

        """
        found = cls.full_relative_re.fullmatch(input_str)
        return bool(found)

    @classmethod
    def is_absolute(cls, input_str: str) -> bool:
        """Check if the given string is an absolute time (e.g.
        '2024-07-16 08:00')
        """
        found = cls.full_absolute_re.fullmatch(input_str)
        return bool(found)

    @classmethod
    def relative_to_delta(cls, time: str) -> timedelta:
        """Convert the given string containing a relative time into a
        datetime.timedelta

        Parameters
        ----------
        time : str
            String consisting of a time in a relative format (e.g. '-1d')

        Returns
        -------
        datetime.timedelta
            A duration expressing the difference between two datetimes
        """
        td = timedelta()
        negative = True
        for token in cls.relative_re.findall(time):
            logger.debug(f"Processing relative time token: {token}")
            if token[0] in '+-':
                negative = token[0] == '-'
            elif negative:
                token = '-' + token
            number = int(token[:-1])

            unit = token[-1]
            if unit == 's':
                td += timedelta(seconds=number)
            elif unit == 'm':
                td += timedelta(minutes=number)
            elif unit == 'H':
                td += timedelta(hours=number)
            elif unit == 'w':
                td += timedelta(weeks=number)
            elif unit in 'yMd':
                if unit == 'y':
                    number *= 365
                elif unit == 'M':
                    number *= 30
                td += timedelta(days=number)
        logger.debug(f"Relative time '{time}' as delta: {td}")
        return td

    @classmethod
    def set_time_on_datetime(cls, dt: datetime, time_str: str) -> datetime:
        """Set an absolute time on a datetime object

        Parameters
        ----------
        dt : datetime
            The datetime to alter
        time_str : str
            The string containing the new time to set (e.g. '-1d 15:00')

        Returns
        -------
        datetime
            The datetime object with the same date and the new time
        """
        time = cls.time_re.search(time_str).group()
        if not time:
            return dt

        if time.count(':') == 1:
            time += ":00"
        h, m, s = map(int, map(float, time.split(':')))
        dt = dt.replace(hour=h, minute=m, second=s)

        return dt

    @classmethod
    def parse_times(cls, start_str: str, end_str: str) -> Tuple[datetime, datetime]:
        """Convert 2 strings containing a start and end date & time, return the
        values' datetime objects. The strings can be formatted as either absolute
        times or relative times. Both are needed as relative times may be relative
        to the other time.

        Parameters
        ----------
        start_str : str
            The leftmost time the x-axis of the plot should show
        end_str : str
            The rigthmost time the x-axis of the plot should show, should be >start

        Returns
        -------
        Tuple[datetime, datetime]
            The python datetime objects for the exact start and end datetimes referenced

        Raises
        ------
        ValueError
            One of the given strings is in an incorrect format
        """
        start_dt = start_delta = None
        end_dt = end_delta = None
        basetime = datetime.now()

        # Process the end time string first to determine
        # if the basetime is the start time, end time, or 'now'
        if end_str == "now":
            end_dt = basetime
        elif cls.is_relative(end_str):
            end_delta = cls.relative_to_delta(end_str)

            # end_delta >= 0 --> the basetime is start time, so are processed after the start time
            # end_delta <  0 --> the basetime is 'now'
            if end_delta < timedelta():
                end_dt = basetime + end_delta
                end_dt = cls.set_time_on_datetime(end_dt, end_str)
        elif cls.is_absolute(end_str):
            end_dt = datetime.fromisoformat(end_str)
            basetime = end_dt
        else:
            raise ValueError("Time Axis end value is in an unexpected format.")

        # Process the start time string second, it may be used as the basetime
        if cls.is_relative(start_str):
            start_delta = cls.relative_to_delta(start_str)

            # start_delta >= 0 --> raise ValueError; this isn't allowed
            if start_delta < timedelta():
                start_dt = basetime + start_delta
                start_dt = cls.set_time_on_datetime(start_dt, start_str)
            else:
                raise ValueError("Time Axis start value cannot be a relative time and be positive.")
        elif cls.is_absolute(start_str):
            start_dt = datetime.fromisoformat(start_str)
        else:
            raise ValueError("Time Axis start value is in an unexpected format.")

        # If the end time is relative and end_delta >= 0 --> start time is the base
        if end_delta and end_delta >= timedelta():
            basetime = start_dt
            end_dt = end_delta + basetime
            end_dt = cls.set_time_on_datetime(end_dt, end_str)

        return (start_dt, end_dt)
