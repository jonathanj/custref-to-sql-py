import argparse
import csv
import sys


class InconsistentState(RuntimeError):
    """
    Encountered an inconsistent state.
    """


def merge(*ds):
    """
    Merge several ``dict``s together.
    """
    res = {}
    for d in ds:
        if d:
            res.update(d)
    return res


def to_sql_name(name):
    """
    Ensure ``name`` is a valid SQL name.
    """
    return name.lower().replace(' ', '_')


def deserialize_text(value):
    """
    Deserialize a text value,
    """
    return value


def serialize_text(value):
    """
    Serialize a text value.
    """
    return "'{}'".format(quote_sql_string(value))


def deserialize_yesno(value):
    """
    Deserialize a boolean (yes or no) value.
    """
    return value.lower() == 'yes'


def serialize_yesno(value):
    """
    Serialize a boolean (yes or no) value.
    """
    return str(1 if value else 0)


def deserialize_integer(value):
    """
    Deserialize an integer value.
    """
    return int(value)


def serialize_integer(value):
    """
    Serialize an integer value.
    """
    return str(value)


class InOutType(object):
    sql_type = None
    _nothing = object()

    def __init__(self, serialize=_nothing, deserialize=_nothing):
        if serialize is not self._nothing:
            self.serialize = serialize
        if deserialize is not self._nothing:
            self.deserialize = deserialize

    @property
    def is_sql(self):
        return self.sql_type and self.serialize is not None

    @property
    def is_csv(self):
        return self.deserialize is not None

    @classmethod
    def no_sql(cls):
        return cls(serialize=None)

    @classmethod
    def no_csv(cls):
        return cls(deserialize=None)


class text(InOutType):
    sql_type = 'TEXT'
    serialize = staticmethod(serialize_text)
    deserialize = staticmethod(deserialize_text)


class integer(InOutType):
    sql_type = 'INTEGER'
    serialize = staticmethod(serialize_integer)
    deserialize = staticmethod(deserialize_integer)


class yesno(InOutType):
    sql_type = 'INTEGER'
    serialize = staticmethod(serialize_yesno)
    deserialize = staticmethod(deserialize_yesno)


class Column(object):
    def __init__(self, name, field_type):
        self.name = to_sql_name(name)
        self.field_type = field_type

    def __repr__(self):
        return '<{} name={!r} field_type={!r}>'.format(
            type(self).__name__,
            self.name,
            self.field_type)

    @property
    def is_sql(self):
        return self.field_type.is_sql

    @property
    def is_csv(self):
        return self.field_type.is_csv


class Table(object):
    def __init__(self, name, columns, foreign_keys=[]):
        self.name = to_sql_name(name)
        self.columns = columns
        self.foreign_keys = foreign_keys

    def __repr__(self):
        return '<{} name={!r} columns={!r} foreign_keys={!r}>'.format(
            type(self).__name__,
            self.name,
            self.columns,
            self.foreign_keys)

    @property
    def only_sql_columns(self):
        return [c for c in self.columns if c.is_sql]

    @property
    def only_csv_columns(self):
        return [c for c in self.columns if c.is_csv]

    def create_sql(self):
        cols = self.only_sql_columns + self.foreign_keys
        cols_sql = [
            '{} {}'.format(col.name, col.field_type.sql_type)
            for col in cols]
        return 'CREATE TABLE {} ({});'.format(
            self.name, ', '.join(cols_sql))

    def insert_sql(self, row, foreign_keys=None):
        if foreign_keys:
            fk_cols = [fk_col for fk_col in self.foreign_keys
                       if fk_col.name in foreign_keys]
        else:
            fk_cols = []
        columns = self.only_sql_columns + fk_cols
        row = merge(row, foreign_keys or {})
        col_names = [col.name for col in columns]
        data = [col.field_type.serialize(row[col.name]) for col in columns]
        return 'INSERT INTO {} ({}) VALUES ({});'.format(
            self.name,
            ', '.join(col_names),
            ', '.join(data))

    def parse_csv(self, data):
        return {col.name: col.field_type.deserialize(v)
                for (col, v) in zip(self.only_csv_columns, data)}


DATA_TYPE_HEADERS = {
    'CUST': Table(
        name='customers',
        columns=[
            Column('record_type', text.no_sql()),
            Column('customer_code', text),
            Column('name', text),
            Column('name_extra', text),
            Column('address_number', text),
            Column('address_line_1', text),
            Column('address_line_2', text),
            Column('address_line_3', text),
            Column('address_line_4', text),
            Column('address_line_5', text),
            Column('contact_name', text),
            Column('contact_extra', text),
            Column('language_code', text),
            Column('language', text),
            Column('headquarter', yesno),
            Column('headquarter_code', text),
            Column('telephone', text),
            Column('mobile_phone', text),
            Column('insert_date', text.no_csv()),
            Column('insert_time', text.no_csv()),
        ]),
    'REF': Table(
        name='customer_references',
        columns=[
            Column('record_type', text.no_sql()),
            Column('reference_identifier', text),
            Column('length', integer),
            Column('mandatory', yesno),
            Column('numeric_only', yesno),
            Column('folf_start_position', integer),
            Column('folf_length', integer),
            Column('print_on_invoice', yesno),
            Column('check_type', text),
            Column('send_to_crs', yesno),
            Column('validation_mask', text),
            Column('internal_name', text),
            Column('customer_reference_desc', text),
            Column('dbi_connector', text),
            Column('dbi_connector_desc', text),
            Column('alphabetic_only', yesno),
            Column('no_special_characters', yesno),
            Column('only_capital_letters', yesno),
            Column('minimum_length', integer),
            Column('reference_type', text),
            Column('insert_date', text.no_csv()),
            Column('insert_time', text.no_csv()),
        ],
        foreign_keys=[
            Column('customer_code', text),
        ]),
}


def parse_headers(headers, data):
    """
    Given a header structure and some data, parse the data as headers.
    """
    return {k: f(v) for (k, (f, _), _), v in zip(headers, data)}


def exit_H_CUST(state):
    """
    Handle leaving the ``H_CUST`` state.

    Add the customer data being processed to the list of all processed customers.
    """
    current_customer = state.pop('current_customer', None)
    if current_customer:
        state.setdefault('customers', []).append(current_customer)
    return state


def enter_final(state, data):
    """
    Handle entering the final state.

    Wrap up any lingering customer data.
    """
    return exit_H_CUST(state)


def enter_CUST(state, data):
    """
    Handle entering the ``CUST`` state.

    Process a customer record.
    """
    if state.get('current_customer'):
        raise InconsistentState(
            'Found unflushed CUST record when processing a new one')
    row = merge(
        DATA_TYPE_HEADERS['CUST'].parse_csv(data),
        state.get('append_to_cust'))
    state['current_customer'] = row
    return state


def enter_REF(state, data):
    """
    Handle entering the ``REF`` state.

    Process a customer reference and associate it with the customer record
    currently being processed.
    """
    current_customer = state.get('current_customer')
    if not current_customer:
        raise InconsistentState('Found REF but no current customer')
    references = current_customer.setdefault('references', [])
    row = merge(
        DATA_TYPE_HEADERS['REF'].parse_csv(data),
        state.get('append_to_ref'))
    references.append(row)
    return state


def enter_H(state, data):
    extra = [
        ('insert_date', data[7]),
        ('insert_time', data[8]),
        ]
    state['append_to_ref'] = extra
    state['append_to_cust'] = extra
    return state


# Valid state transitions.
STATES = {
    '__initial__': {
        'valid_states': {'H', '*'},
    },
    'H': {
        'enter': enter_H,
        'valid_states': {'H_CUST', 'S'},
    },
    'S': {
        'valid_states': {'H_CUST'},
    },
    'H_CUST': {
        'exit': exit_H_CUST,
        'valid_states': {'CUST', 'H_REF'},
    },
    'CUST': {
        'enter': enter_CUST,
        'valid_states': {'H_REF', 'H_CUST', 'MEDIUM'},
    },
    'H_REF': {
        'valid_states': {'REF'},
    },
    'REF': {
        'enter': enter_REF,
        'valid_states': {'REF', 'H_CUST', 'MEDIUM'},
    },
    'MEDIUM': {
    },
    '__final__': {
        'final': True,
        'enter': enter_final,
    }
}


def quote_sql_string(value):
    """
    Quote an SQL string.
    """
    return value.replace("'", "''")


def as_sql(state, create=True):
    """
    Serialize the application state as SQL.
    """
    yield 'BEGIN TRANSACTION;'

    ref_table = DATA_TYPE_HEADERS['REF']
    cust_table = DATA_TYPE_HEADERS['CUST']

    if create:
        yield ''
        yield '-- Create tables'
        yield ref_table.create_sql()
        yield cust_table.create_sql()

    yield ''

    customers = state.get('customers')
    if customers:
        yield '-- Customers'
        for customer in customers:
            yield cust_table.insert_sql(customer)
            for ref in customer.get('references', []):
                yield ref_table.insert_sql(ref, foreign_keys={
                    'customer_code': customer['customer_code'],
                })

    yield ''

    yield 'COMMIT;'


def fsm(action, data):
    """
    Finite-state machine to process an action and data, possibly leading to a
    new action.
    """
    valid_states = action.get('valid_states')
    if valid_states is None:
        return STATES['__final__']

    maybe_next = data[0]
    if maybe_next in valid_states:
        return STATES[maybe_next]
    elif '*' in valid_states:
        return action
    else:
        raise RuntimeError('Expected one of {!r} but got {!r}'.format(
            valid_states, maybe_next))


def parse_command_line():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_file',
        nargs='?',
        type=argparse.FileType('rb'),
        default=sys.stdin)
    parser.add_argument(
        'output_file',
        nargs='?',
        type=argparse.FileType('wb'),
        default=sys.stdout)
    parser.add_argument(
        '--create',
        action='store_true',
        help='Include SQL "CREATE TABLE" commands.')
    return parser.parse_args()


def main(args):
    reader = csv.reader(args.input_file, delimiter=';')
    state, action = {}, STATES['__initial__']
    while reader:
        data = next(reader, None)
        # XXX:
        if data is None:
            break
        new_action = fsm(action, data)
        if new_action != action:
            exitf = action.get('exit')
            if exitf:
                state = exitf(state)

        enterf = new_action.get('enter')
        if enterf:
            state = enterf(state, data)

        if new_action.get('final'):
            break

        action = new_action

    args.output_file.write(
        '\n'.join(as_sql(state, create=args.create)))


if __name__ == '__main__':
    args = parse_command_line()
    main(args)
