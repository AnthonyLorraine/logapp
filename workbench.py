import enum
import re
from os import listdir
from os.path import join, isfile
from typing import List, Any

BRD_FILE_PATH = r'C:\Users\e261712\Desktop\1471683'

SB = '\x0b'
EB = '\x1c'
CR = '\x0d'

HL7_Messages = []
HL7_Message = ''
if __name__ == '__main__':
    for file in listdir(BRD_FILE_PATH):
        if isfile(join(BRD_FILE_PATH, file)):
            if 'brd' in file:
                with open(join(BRD_FILE_PATH, file), 'r', encoding='latin-1', errors='surrogateescape') as log_file:
                    logging = False
                    for log in log_file:
                        if SB in log:
                            logging = True
                            HL7_Message += log[1:]
                        elif EB in log:
                            logging = False
                            HL7_Messages.append(HL7_Message)
                            HL7_Message = ''
                        elif logging:
                            HL7_Message += log


class HL7Message:
    def __init__(self, raw_message: str):
        self._raw_message = raw_message
        self.segments = []
        self.separators = self._parse_separators()
        self._parse_segments()

    def _parse_separators(self):
        m = re.match("^MSH(?P<field_sep>\S)", self._raw_message)
        if m is not None:
            field_sep = m.group('field_sep')
            msh = self._raw_message.split("\n", 1)[0]
            fields = msh.split(field_sep)
            separators = fields[1]
            if len(separators) > len(set(separators)):
                raise ValueError(f'Duplicate field separators found {separators}')

            try:
                component_sep, repetition_sep, escape, subcomponent_sep = separators
                truncation_sep = None
            except ValueError:
                if len(separators) > 4:
                    raise ValueError(f'Incomplete MSH.2 field separators [{separators}]')
                elif len(separators) == 5 and fields[11] >= '2.7':
                    component_sep, repetition_sep, escape, subcomponent_sep, truncation_sep = separators
                else:
                    raise ValueError(f'MSH.2 contains invalid separators [{separators}]')

            separator_characters = {
                'FIELD': field_sep,
                'COMPONENT': component_sep,
                'SUBCOMPONENT': subcomponent_sep,
                'REPETITION': repetition_sep,
                'ESCAPE': escape,
                'SEGMENT': '\n',
                'GROUP': '\n',
            }
            if truncation_sep:
                separator_characters.update({'TRUNCATION': truncation_sep})

            return separator_characters

    def _parse_segments(self):
        for segment in self._raw_message.split(self.separators['SEGMENT']):
            self.segments.append(Segment(raw_segment=segment, separators=self.separators))

    def __str__(self):
        return self._raw_message

    def __getitem__(self, item: Any):
        for segment in self.segments:
            if str(item).lower() in str(segment.name).lower():
                return segment
        return self.segments[item]


class Segment:
    def __init__(self, raw_segment: str, separators: dict):
        self._raw_segment = raw_segment
        self._separators = separators
        self.name = self._raw_segment[:3]
        self.fields = []
        self._parse_fields()

    def _parse_fields(self):
        for index, field in enumerate(self._raw_segment.split(self._separators['FIELD'])):
            index = str(index)
            for r_index, repeated_field in enumerate(field.split(self._separators['REPETITION'])):
                if r_index+1 > 1:
                    r_index = '.'.join(index+str(r_index+1))
                else:
                    r_index = index
                self.fields.append(Field(raw_field=repeated_field, separators=self._separators, index=r_index))

    def __repr__(self):
        return f'{self.name}'

    def __getitem__(self, item: Any):
        for field in self.fields:
            if str(item).lower() in str(field.name).lower():
                return field

    def __str__(self):
        return self._raw_segment


class Field:
    def __init__(self, raw_field: str, separators: dict, index: str):
        self._raw_field = raw_field
        self._separators = separators
        self.name = index
        self.components = []
        self._parse_components()

    def _parse_components(self):
        for index, component in enumerate(self._raw_field.split(self._separators['COMPONENT'])):
            index = str(index + 1)
            self.components.append(Component(raw_component=component, separators=self._separators, index=index))

    def __repr__(self):
        return f'_{self.name}'

    def __str__(self):
        return self._raw_field

    def __getitem__(self, item: Any):
        for component in self.components:
            if str(item).lower() in str(component.name).lower():
                return component


class Component:
    def __init__(self, raw_component: str, separators: dict, index: str):
        self._raw_component = raw_component
        self._separators = separators
        self.name = index
        self.subcomponents = []
        self._parse_subcomponents()

    def _parse_subcomponents(self):
        for index, subcomponent in enumerate(self._raw_component.split(self._separators['SUBCOMPONENT'])):
            index = str(index+1)
            self.subcomponents.append(SubComponent(raw_subcomponent=subcomponent, index=index))

    def __repr__(self):
        return f'_{self.name}'

    def __str__(self):
        return self._raw_component

    def __getitem__(self, item: Any):
        for subcomponent in self.subcomponents:
            if str(item).lower() in str(subcomponent.name).lower():
                return subcomponent


class SubComponent:
    def __init__(self, raw_subcomponent: str, index: str):
        self._raw_subcomponent = raw_subcomponent
        self.name = index

    def __repr__(self):
        return f'_{self.name}'

    def __str__(self):
        return self._raw_subcomponent


# print(HL7Message(HL7_Messages[0]))
print(HL7Message(HL7_Messages[0])['pid'][3])

