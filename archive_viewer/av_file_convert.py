import json
import logging
import xml.etree.ElementTree as ET
from os import (path, getenv)
from typing import (Dict, Union)
from pathlib import Path
from datetime import datetime
from argparse import (ArgumentParser, Action, Namespace)
from qtpy.QtGui import QColor
from collections import OrderedDict
from pydm.widgets.timeplot import PyDMTimePlot


if __name__ in logging.Logger.manager.loggerDict:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger("")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("INFO")
    handler.setLevel("INFO")


class ArchiveViewerFileConverter():
    def __init__(self, input_file: Union[str, Path] = "", output_file: Union[str, Path] = "") -> None:
        self.input_file = input_file
        self.output_file = output_file

        self.stored_data = None

    def import_is_xml(self):
        """Helper function to determine if the import file is in XML format."""
        with self.input_file.open() as f:
            return f.readline().startswith("<?xml")

    def import_file(self, file_name: Union[str, Path] = None) -> Dict:
        """Import Archive Viewer save data from the provided file. The file
        should be one of two types: '.pyav' or '.xml'. The data is returned as
        well as saved in the stored_data property.

        Parameters
        ----------
        file_name : str or pathlib.Path
            The absolute filepath for the input file to import

        Returns
        -------
        dict
            A python dictionaty containing the data imported from the provided file
        """
        if file_name:
            self.input_file = Path(file_name)
        if not self.input_file.is_file():
            raise FileNotFoundError(f"Data file not found: {self.input_file}")

        with self.input_file.open() as f:
            is_xml = f.readline().startswith("<?xml")

        text = self.input_file.read_text()
        if is_xml:
            etree = ET.ElementTree(ET.fromstring(text))
            self.stored_data = self.xml_to_dict(etree)
            if not (self.stored_data['pv'] or self.stored_data['formula']):
                raise FileNotFoundError(f"Incorrect input file format: {self.input_file}")
        else:
            self.stored_data = json.loads(text)
            if not self.stored_data['curves']:
                raise FileNotFoundError(f"Incorrect input file format: {self.input_file}")

        return self.stored_data

    def export_file(self, file_name: Union[str, Path] = None, output_data: Union[Dict, PyDMTimePlot] = None) -> None:
        """Export the provided Archive Viewer save data to the provided file.
        The file to export to should be of type '.pyav'. The provided data can
        be either a dictionary or a PyDMTimePlot object. If no data is provided,
        then the converter's previously imported data is exported.

        Parameters
        ----------
        file_name : str or pathlib.Path
            The absolute file path of the file that save data should be written
            to. Should be of file type '.pyav'.
        output_data : dict or PyDMTimePlot, optional
            The data that should be exported, by default uses previously imported data

        Raises
        ------
        FileNotFoundError
            If the provided file name does not match the expected output file type '.pyav'
        ValueError
            If no output data is provided and the converter hasn't imported data previously
        """
        if file_name:
            self.output_file = Path(file_name)
        if not self.output_file.suffix:
            self.output_file = self.output_file.with_suffix(".pyav")
        elif not self.output_file.match("*.pyav"):
            raise FileNotFoundError(f"Incorrect output file format: {self.output_file.suffix}")

        if not output_data:
            if not self.stored_data:
                raise ValueError("Output data is required but was not provided "
                                 "and the 'stored_data' property is not populated.")
            output_data = self.stored_data
        elif isinstance(output_data, PyDMTimePlot):
            output_data = self.get_plot_data(output_data)

        for obj in output_data['y-axes'] + output_data['curves']:
            for k, v in obj.copy().items():
                if v is None:
                    del obj[k]

        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=4)

    def convert_data(self, data_in: Dict = {}) -> Dict:
        """Convert the inputted data from being formatted for the Java Archive
        Viewer to a format used by the PyDM Archive Viewer. This is accomplished
        by converting one dictionary structure to another.

        Parameters
        ----------
        data_in : dict, optional
            The input data to be converted, by default uses previously imported data

        Returns
        -------
        dict
            The converted data in a format that can be used by the PyDM Archive Viewer
        """
        if not data_in:
            data_in = self.stored_data

        converted_data = {}

        converted_data['archiver_url'] = data_in.get("connection_parameter",
                                                     getenv("PYDM_ARCHIVER_URL"))
        converted_data['archiver_url'] = converted_data['archiver_url'].replace("pbraw://", "http://")

        legend_dict = data_in['legend_configuration']
        legend_dict['show_curve_name'] = legend_dict['show_ave_name']
        del legend_dict['show_ave_name']

        converted_data['plot'] = {'title': data_in['plot_title'],
                                  'legend': legend_dict}

        converted_data['time_axis'] = data_in['time_axis'][0]
        converted_data['y-axes'] = []
        for axis_in in data_in['range_axis']:
            ax_dict = {'name': axis_in['name'],
                       'label': axis_in['name'],
                       'minRange': axis_in['min'],
                       'maxRange': axis_in['max'],
                       'orientation': axis_in['location'],
                       'logMode': axis_in['type'] != "normal"}
            filtered_dict = self.remove_null_values(ax_dict)
            converted_data['y-axes'].append(filtered_dict)

        converted_data['curves'] = []
        for pv_in in data_in['pv']:
            color = self.srgb_to_qColor(pv_in['color'])
            pv_dict = {'name': pv_in['name'],
                       'channel': pv_in['name'],
                       'yAxisName': pv_in['range_axis_name'],
                       'lineWidth': float(pv_in['draw_width']),
                       'color': color.name(),
                       'thresholdColor': color.name()}
            filtered_dict = self.remove_null_values(pv_dict)
            converted_data['curves'].append(filtered_dict)

        for formula_in in data_in['formula']:
            # TODO convert formulas once formulas are implemented for ArchiveViewer
            pass

        self.stored_data = converted_data
        return self.stored_data

    @staticmethod
    def xml_to_dict(xml: ET.ElementTree) -> Dict:
        """Convert an XML ElementTree containing an Archive Viewer save
        file to a dictionary for easier use

        Parameters
        ----------
        xml : ET.ElementTree
            The XML ElementTree object read from the file

        Returns
        -------
        dict
            The data in a dictionary format
        """
        data_dict = {'connection_parameter': '',
                    'plot_title': '',
                    'legend_configuration': {},
                    'time_axis': [],
                    'range_axis': [],
                    'pv': [],
                    'formula': []}

        data_dict['connection_parameter'] = xml.find("connection_parameter").text
        data_dict['plot_title'] = xml.find("plot_title").text
        data_dict['legend_configuration'] = xml.find("legend_configuration").attrib

        for key in ("time_axis", "range_axis", "pv", "formula"):
            for element in xml.findall(key):
                ele_dict = element.attrib
                ele_dict |= {sub_ele.tag: sub_ele.text for sub_ele in element}
                data_dict[key].append(ele_dict)

        return data_dict

    @staticmethod
    def get_plot_data(plot: PyDMTimePlot) -> Dict:
        """Extract plot, axis, and curve data from a PyDMTimePlot object"""
        output_dict = {'archiver_url': getenv("PYDM_ARCHIVER_URL"),
                       'plot': {},
                       'time_axis': {},
                       'y-axes': [],
                       'curves': []}

        [start_ts, end_ts] = plot.getXAxis().range
        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(end_ts)

        output_dict['time_axis'] = {'name': "Main Time Axis",
                                    'start': start_dt.isoformat(sep=' ', timespec='seconds'),
                                    'end': end_dt.isoformat(sep=' ', timespec='seconds'),
                                    'location': "bottom"}

        for a in plot.getYAxes():
            axis_dict = json.loads(a, object_pairs_hook=OrderedDict)
            output_dict['y-axes'].append(axis_dict)

        for c in plot.getCurves():
            curve_dict = json.loads(c, object_pairs_hook=OrderedDict)
            if not curve_dict['channel']:
                continue
            output_dict['curves'].append(curve_dict)

        return output_dict

    @staticmethod
    def srgb_to_qColor(srgb: str) -> QColor:
        """Convert RGB strings to QColors. The string is a 32-bit
        integer containing the aRGB values of a color. (e.g. #FF0000 or -65536)

        Parameters
        ----------
        srgb : str
            Either a hex value or a string containing a signed 32-bit integer

        Returns
        -------
        QColor
            A QColor object storing the color described in the string
        """
        if not srgb:
            return QColor()
        elif srgb[0] != '#':
            rgb_int = int(srgb) & 0xFFFFFFFF
            srgb = f"#{rgb_int:08X}"
        return QColor(srgb)

    @staticmethod
    def remove_null_values(dict_in: Dict) -> Dict:
        """Remove all key-value pairs from a given dictionary where the value is None"""
        dict_out = dict_in.copy()
        for k, v in dict_in.items():
            if v is None:
               del dict_out[k]
        return dict_out


def main(input_file: Path = None, output_file: Path = None, overwrite: bool = False, clean: bool = False):
    # Check that the input file is usable
    if not input_file:
        raise FileNotFoundError("Input file not provided")
    elif not input_file.is_file():
        raise FileNotFoundError(f"Data file not found: {input_file}")
    elif not input_file.match("*.xml"):
        raise FileNotFoundError(f"Incorrect input file format: {input_file}")

    # Check that the output file is usable
    if not output_file:
        output_file = input_file.with_suffix(".pyav")
    elif not output_file.suffix:
        output_file = output_file.with_suffix(".pyav")
    elif not output_file.match("*.pyav"):
        raise FileNotFoundError(f"Incorrect output file format: {output_file}")

    # Check if file exists, and if it does if the overwrite flag is used
    if output_file.is_file() and not overwrite:
        raise FileNotFoundError(f"Output file exists but overwrite not enabled: {output_file}")

    # Complete the requested conversion
    converter = ArchiveViewerFileConverter()

    converter.import_file(input_file)
    converter.convert_data()
    converter.export_file(output_file)

    # Remove the input file if requested
    if clean:
        input_file.unlink()
        logger.debug(f"Removing input file: {input_file}")

    return 0


if __name__ == "__main__":
    class PathAction(Action):
        def __call__(self, parser: ArgumentParser, namespace: Namespace, values: str, option_string: str = None) -> None:
            """Convert filepath string from argument into  a pathlib.Path object"""
            new_path = path.expandvars(values)
            new_path = Path(new_path).expanduser()
            new_path = new_path.resolve()
            setattr(namespace, self.dest, new_path)

    parser = ArgumentParser(prog="Archive Viewer File Converter",
                            description="Convert files used by the Java Archive"
                            " Viewer to a file format that can be used with the"
                            " newer PyDM Archive Viewer.")
    parser.add_argument("input_file",
                        action=PathAction,
                        type=str,
                        help="Path to the file to be converted")
    parser.add_argument("--output_file", "-o",
                        action=PathAction,
                        type=str,
                        help="Path to the output file (defaults to input file name)")
    parser.add_argument("--overwrite", "-w",
                        action="store_true",
                        help="Overwrite the target file if it exists")
    parser.add_argument("--clean",
                        action="store_true",
                        help="Remove the input file after successful conversion")
    args = parser.parse_args()

    try:
        main(**vars(args))
    except Exception as e:
        logger.error(e)
