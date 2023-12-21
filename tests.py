from unittest import TestCase
import unittest
from textwrap import dedent
from dataclasses import dataclass
from typing import Callable, Any
import copy

@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] | None = None

# TODO: add '' for strings
def to_string(self):
    lines = [self.__class__.__name__ + "("]
    for name, field in self.__fields__.items():
        value = getattr(self, name)
        if type(value) == str:
             value = "'" + value + "'"
        lines += [ "  # " + field.label + '\n' +
                   "  " + name + "=" + str(value)
                  ]
        lines += ["", ]
    lines.pop()
    lines += [")"]
    s = '\n'.join(lines)
    return s

def setattr_(self, name, value):
    if self.__readonly:
        raise(AttributeError())
    else:
        object.__setattr__(self, name, value)

def check_precondition(self, name, value):
    precondition = self.__fields__[name].precondition
    if precondition:
        if(self.__fields__[name].precondition(value)):
            return value
        raise TypeError()
    return value

def generate_code(annotations) -> str:
    lines = ["__readonly = False"]
    lines += [ '{}'.format(
                "\n".join((f'{arg}: {an.__qualname__}' for arg, an in annotations.items())))
            ]
    lines += [ 'def __init__(self, {}):'.format(
                ', '.join((f'{arg}: {an.__qualname__}' for arg, an in annotations.items())))
            ]
    for arg, _ in annotations.items():
        lines += [ f'  self.{arg} = check_precondition(self, "{arg}", {arg})', ]

    lines += [ '  self.__readonly = True' ]
    code = '\n'.join(lines)
    return code

class RecordMeta(type):
    def __new__(cls, name, bases, attr, **kwargs):
        # Implement the class creation by manipulating the attr dictionary

        fields = {}
        annotations = {}
        if bases:
            fields = copy.deepcopy(bases[0].__fields__)
            base_annotations = copy.deepcopy(bases[0].__annotations__)
            annotations.update(base_annotations)

        if attr.get('__annotations__'):
            annotations.update(attr.get('__annotations__'))

        if annotations:
            gen_code = generate_code(annotations)
            exec(gen_code, globals(), attr)
            for arg, _ in annotations.items():
                a = attr.get(arg)
                if type(a) == Field:
                    fields[arg] = a

        new_cls = super().__new__(cls, name, bases, attr, **kwargs)

        setattr(new_cls, "__fields__", fields)
        setattr(new_cls, "__str__", to_string)
        setattr(new_cls, "__setattr__", setattr_)
        setattr(new_cls, "__annotations", annotations)

        return new_cls

# Set the metaclass of the Record class
class Record(metaclass=RecordMeta):
    pass

# Usage of Record
class Person(Record):
    """
    A simple person record
    """ 
    name: str = Field(label="The name") 
    age: int = Field(label="The person's age", precondition=lambda x: 0 <= x <= 150)
    income: float = Field(label="The person's income", precondition=lambda x: 0 <= x)

class Named(Record):
    """
    A base class for things with names
    """
    name: str = Field(label="The name") 

class Animal(Named):
    """
    An animal
    """
    habitat: str = Field(label="The habitat", precondition=lambda x: x in ["air", "land","water"])
    weight: float = Field(label="The animals weight (kg)", precondition=lambda x: 0 <= x)

class Dog(Animal):
    """
    A type of animal
    """
    bark: str = Field(label="Sound of bark")

# Tests 
class RecordTests(TestCase):
    def test_creation(self):
        Person(name="JAMES", age=110, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=160, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES")
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age=-1, income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", income=24000.0)
        with self.assertRaises(TypeError): 
            Person(name="JAMES", age="150", wealth=24000.0)
    
    def test_properties(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        self.assertEqual(james.age, 34)
        with self.assertRaises(AttributeError):
            james.age = 32

    def test_str(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        correct = dedent("""
        Person(
          # The name
          name='JAMES'

          # The person's age
          age=34

          # The person's income
          income=24000.0
        )
        """).strip()
        self.assertEqual(str(james), correct)

    def test_dog(self):
        mike = Dog(name="mike", habitat="land", weight=50., bark="ARF")
        self.assertEqual(mike.weight, 50)
        
if __name__ == '__main__':
    unittest.main()

