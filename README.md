#fam

A simple Python ORM for CouchDB and Couchbase Sync Gateway. 

Current build status: ![Build Status](https://circleci.com/gh/paulharter/fam.png?circle-token=b11ad12686f98bb9f68956f680bb6e61184d5)

Fam is a work in progress growing as the needs of my current project dictate.  This means that while very useful it is not a feature complete ORM, however it is useful if you, like me, have highly relational data in a couch type db. I use it to support a web app that sits side by side with a mobile application using sync gateway.

Fam adds a type and namespace to each document:

- **type** - A lower case string derived from the class name
- **namespace** - An opaque string to help avoid class name clashes and allow versioning of classes

And uses them to provide:

- A class to bind methods to documents
- Automatic generation of design documents for relationships between classes
- Lookup of related documents
- Validation of documents
- Document life-cycle callbacks for creation, updates and deletion
- Optional cascading deletion through relationships

You can define a fam class like this:

```python

NAMESPACE = "mynamespace"

class Dog(GenericObject):
    use_rev = True
    additional_properties = True
    fields = {
        "name": StringField(),
        "owner_id": ReferenceTo(NAMESPACE, "person", cascade_delete=True)
        }

    def talk(self):
        return "woof"

```

and then use it to create a document like this:

```python
dog = Dog(name="fly")
db.put(dog)

```

##Installation

You can install fam from pypi with `pip install fam`

##Databases

fam has wrappers for connecting to different databases:

- CouchDB
- Couchbase Sync Gateway

These wrapper classes do very little except remember the location of the database and send requests, relying on the python requests library to provide connection pooling.

 To use fam you have to first create a class mapper passing in your classes eg:
 
 ```python
 
from fam.mapper import ClassMapper
 
mapper = ClassMapper([Dog, Cat, Person])

 ```
 and then create a db wrapper using the mapper, the address of the database and the name of the database/bucket
 
 ```python
 
db = CouchDBWrapper(mapper, database_url, database_name)
 
 ```
 
 This means that documents accessed though the db will be associated with their relative classes.
 
 You can then write or update the relational design documents in the database from the classes in the mapper like this:
 
 ```python
 
db.update_designs()
 
```

An instance of a database wrapper provides these methods for adding and removing fam objects from databases

- **db.put(an_object)** - Puts this object into the database
- **db.get(key)** - Gets the object with this key from the database
- **db.delete(an_object)** - Removes this object from the database
- **db.delete_key(key)** - Removes the object with this key from the database


##Classes
 
 Fam classes are defined as inheriting from fam.blud.GenericObject like this:


 ```python 
 
class Cat(GenericObject):
    use_rev = False
    additional_properties = False
    fields = {
        "name": StringField(),
        "legs": NumberField(),
        "owner_id": ReferenceTo(NAMESPACE, "person")
        }
 
 ```
 
 With three class attributes
 
 - **use_rev** - A boolean, True by default, which if true uses the default rev/cas collision protection of Couch DBs but if false always forces a document update as if this mechanism didn't exist
 - **additional_properties** - A boolean, false by default, which if true lets you add arbitrary additional top level attributes to an object and if false will throw an exception when you try.
 - **fields** - A dict of named fields that map to the top level attributes of the underlying json documents. See below for use.
 
GenericObject also provides six callbacks that occur as documents are saved and deleted

- **pre_save_new_cb(self)**
- **post_save_new_cb(self)**
- **pre_save_update_cb(self, old_properties)**
- **post_save_update_cb(self)**
- **pre_delete_cb(self)**
- **post_delete_cb(self)**
      
##Fields
 
There are several types of field defined in fam.blud that map to json types
 
- **BoolField**
- **NumberField**
- **StringField**
- **ListField**
- **DictField**

When defining a fam class you instantiate each of fields for the class and give it a name eg `"address": StringField()`

###ObjectField Fields

An ObjectField is an instance of another python object. The class of the object must be provided when defining the field. The class has to provide an instance method `to_json` and a class method `from_json` so fam can serialise and deserialise it successfully.

This is an example of a representation of a duration of time:

```python

"duration": ObjectField(cls=TimeDuration)

...

class TimeDuration(object):

    def __init__(self, nom=0, denom=0, count=0, per_frame=1):
        self.nom = nom
        self.denom = denom
        self.count = count
        self.per_frame = per_frame

    def to_json(self):
        return {
            "nom": self.nom,
            "denom": self.denom,
            "count": self.count,
            "per_frame": self.per_frame
        }

    @classmethod
    def from_json(cls, as_json):
        return cls(**as_json)
        
    ...

```

###ReferenceTo Fields

ReferenceTo is really just a string field that is the key of another document. ReferenceTo fields are defined with the namespace and name of the type of the referenced document. 

```python 

"owner_id": ReferenceTo(NAMESPACE, "person")

```

The name should always end with `_id` , this indicates that it is a reference but it also support fam's lookup of related objects. This allows you to directly access related documents for example dog.owner_id will return the key of the owner document but dog.owner will return an instance of the Owner class for that document.

###ReferenceFrom Fields

ReferenceFrom fields are quite different and they have no representation within the json document. Instead they use the automatically created design documents to find a collection of documents with the associated ReferenceTo field. So ReferenceFrom fields only work with as existing ReferenceTo Field. They are defined with the namespace and the type that the reference is from and the name of the ReferenceTo field in that type.

```python

"dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id")

```
This gives way to do one-to-one and one-to-many relationships. In practice I find I tend to model immutable one-to-many relationships internally as lists of keys within documents and mutable ones with fam view lookups. I also create mutable one-to-one and many-to-many relationships with small join documents with compound keys. I also have write extra views by hand for more complex indexing.

##Field Options

There are four optional arguments when creating a field:

- **required** - A boolean, false by default that asserts that this field must be present.
- **immutable** - A boolean, false by default asserts that you cannot change the value of ths field once it has been set.
- **default** - A default value for this field that will be returned on read if this field is absent from the underlying json. None by default.
- **cascade_delete** - Only applies to ReferenceTo and ReferenceFrom fields. A boolean, false by default, which if true will delete the object the reference points to when this object is deleted.


##Validation

Fam now uses JSON Schema http://json-schema.org to validate documents. Fam's mapper generates schemas dynamically from the class definitions and uses them to validate documents.

You can get the mapper to write out its internal schemata by calling ```mapper.validator.write_out_schemata(directory)```


