from datetime import datetime
import re
from os import listdir
from os.path import join, isfile
from typing import List, Any
import sys
from types import ModuleType, FunctionType
from gc import get_referents

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
# f'{round(getsize(self.hl7_message)/1024/1024, 2)}mb')
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


HL7_MESSAGE = {
    'I': {
        'ADT': {
            'A01': 'Admission',
            'A02': 'Transfer',
            'A03': 'Discharge',
            'A05': 'Pre-admission',
            'A08': 'Visit Update',
            'A11': 'Cancel Admission',
            'A12': 'Cancel Transfer',
            'A13': 'Cancel I/P Discharge',
            'A14': 'Pre-admission',
            'A21': 'On-Leave',
            'A22': 'Return from leave',
            'A27': 'Cancel Pre-admission',
            'A28': 'PMI Registration',
            'A31': 'PMI Update',
            'A34': 'PMI Merge',
            'A44': 'Change U/R for O/P visit',
        },
        'SIU': {
            'S12': 'Notification of New Appointment',
            'S14': 'Notification of Appointment Modification',
            'S15': 'Notification of Appointment Cancellation',
        }
    },
    'E': {
        'ADT': {
            'A03': 'Discharge Emergency Visit',
            'A04': 'Register Emergency Visit',
            'A08': 'Emergency Visit Update',
            'A11': 'Cancel Emergency Visit',
            'A13': 'Cancel Emergency Visit Discharge',
            'A44': 'Change U/R for Emergency Visit',
        }
    },
    'O': {
        'ADT': {
            'A03': 'Discharge',
            'A04': 'Register Event (Attendance)',
            'A05': 'Pre-admit a Patient (Booking)',
            'A08': 'Update Patient Information (Update Booking/Reschedule)',
            'A11': 'Cancel Visit (Unattend)',
            'A13': 'Cancel Discharge',
            'A38': 'Cancel Pre-admit (Booking)',
            'A44': 'Change U/R for O/P visit',
            'A31': 'PMI Update',
        }
    },

}
HL7_MESSAGE['S'] = HL7_MESSAGE['I']
BRD_FILE_PATH = r'C:\Users\username\Desktop\working_directory'
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

    def __repr__(self):
        return self._raw_message

    def __getitem__(self, item: Any):
        for segment in self.segments:
            if str(item).lower() == str(segment.name).lower():
                if segment:
                    return segment
                else:
                    pass


class Segment:
    def __init__(self, raw_segment: str, separators: dict):
        self._raw_segment = raw_segment
        self._separators = separators
        self.name = self._raw_segment[:3]
        self.fields = []
        self._parse_fields()

    def _parse_fields(self):
        for index, field in enumerate(self._raw_segment.split(self._separators['FIELD'])):
            if self.name == 'MSH':
                index = str(index + 1)
            else:
                index = str(index)
            for r_index, repeated_field in enumerate(field.split(self._separators['REPETITION'])):
                if r_index + 1 > 1:
                    r_index = '.'.join(index + str(r_index + 1))
                else:
                    r_index = index
                self.fields.append(Field(raw_field=repeated_field, separators=self._separators, index=r_index))

    def __repr__(self):
        return self._raw_segment

    def __getitem__(self, item: Any):
        for field in self.fields:
            if str(item).lower() == str(field.name).lower():
                if field:
                    return field
                else:
                    pass
        return self.fields

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
        return self._raw_field

    def __str__(self):
        return self._raw_field

    def __getitem__(self, item: Any):
        for component in self.components:
            if str(item).lower() == str(component.name).lower():
                if component:
                    return component
                else:
                    pass
        return self.components


class Component:
    def __init__(self, raw_component: str, separators: dict, index: str):
        self._raw_component = raw_component
        self._separators = separators
        self.name = index
        self.subcomponents = []
        self._parse_subcomponents()

    def _parse_subcomponents(self):
        for index, subcomponent in enumerate(self._raw_component.split(self._separators['SUBCOMPONENT'])):
            index = str(index + 1)
            self.subcomponents.append(SubComponent(raw_subcomponent=subcomponent, index=index))

    def __repr__(self):
        return self._raw_component

    def __str__(self):
        return self._raw_component

    def __getitem__(self, item: Any):
        for subcomponent in self.subcomponents:
            if str(item).lower() == str(subcomponent.name).lower():
                if subcomponent:
                    return subcomponent
                else:
                    pass
        return self.subcomponents


class SubComponent:
    def __init__(self, raw_subcomponent: str, index: str):
        self._raw_subcomponent = raw_subcomponent
        self.name = index

    def __repr__(self):
        return self._raw_subcomponent

    def __str__(self):
        return self._raw_subcomponent


class CommonHL7:
    def __init__(self, raw_message: str):
        self.raw = raw_message
        self.hl7_message = HL7Message(raw_message=raw_message)
        self.message_id = self.hl7_message['msh'][10]
        self.message_date_time = datetime.strptime(str(self.hl7_message['msh'][7]), '%Y%m%d%H%M%S')
        self.event_type = self.hl7_message['msh'][9][2]
        if self.hl7_message['pid']:
            self.ur_number = self.hl7_message['pid'][3][1]
            self.first_name = self.hl7_message['pid'][5][2]
            self.middle_name = self.hl7_message['pid'][5][3]
            self.last_name = self.hl7_message['pid'][5][1]
            self.date_of_birth = datetime.strptime(str(self.hl7_message['pid'][7]), '%Y%m%d')
        else:
            self.ur_number = ''
            self.first_name = ''
            self.middle_name = ''
            self.last_name = ''
            self.date_of_birth = ''
        if len(str(self.hl7_message['pv1'])) > 10:
            self.visit = self.hl7_message['pv1'][19]
            self.admission_type = self.hl7_message['pv1'][2]
            self.type_description = self._get_type_description()
            self.ward = self._get_ward()
            self.bed = self._get_bed()
        else:
            self.visit = ''
            self.admission_type = ''
            self.type_description = ''
            self.ward = ''
            self.bed = ''
        del self.hl7_message

    def _get_type_description(self):
        message_type = str(self.hl7_message["msh"][9][1])
        try:
            description = HL7_MESSAGE[self.admission_type][message_type][self.event_type]
        except KeyError:
            description = ''
        return description

    def _get_ward(self):
        if self.admission_type == 'E':
            ward = 'Emergency'
        else:
            ward = self.hl7_message['pv1'][3][2]
        return ward

    def _get_bed(self):
        if self.admission_type == 'E':
            bed = self.hl7_message['pv1'][39][2]
        else:
            bed = self.hl7_message['pv1'][3][3]
        return bed

    def __repr__(self):
        return self.message_id, self.message_date_time, self.event_type, self.type_description, self.ur_number, \
               self.first_name, self.middle_name, self.last_name, self.date_of_birth, self.visit, self.admission_type, \
               self.ward, self.bed, self.raw

    def __str__(self):
        return str(self.__repr__())


for message in HL7_Messages:
    hl7_message = CommonHL7(message)
    print(hl7_message)
