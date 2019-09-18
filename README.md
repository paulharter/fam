# fam

[![Build Status](https://travis-ci.org/paulharter/fam.svg?branch=master)](https://travis-ci.org/paulharter/fam)

A simple Python ORM for CouchDB and Couchbase Sync Gateway. 

Fam is a work in progress growing as the needs of my current project dictate.  It is not a feature complete ORM, however it is useful if you, like me, have highly relational data in a couch type db. I use it to support a web app that sits side by side with a mobile application using sync gateway.

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

class Dog(FamObject):
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

## Installation

You can install fam from pypi with `pip install fam`

## Databases

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


## Classes
 
 Fam classes are defined as inheriting from fam.blud.FamObject like this:


 ```python 
 
class Cat(FamObject):
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
 
FamObject also provides six callbacks that occur as documents are saved and deleted

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

### ObjectField Fields

An ObjectField is an instance of another python object. The class of the object must be provided when defining the field. The class has to provide an instance method `to_json` and a class method `from_json` so fam can serialise and deserialise it successfully.

This is an example of a representation of a duration of time:

```python

"duration": ObjectField(cls=TimeDuration)

...

class TimeDuration(object):

    def __init__(self, nom=0, denom=0, count=0):
        self.nom = nom
        self.denom = denom
        self.count = count

    def to_json(self):
        return {
            "nom": self.nom,
            "denom": self.denom,
            "count": self.count,
        }

    @classmethod
    def from_json(cls, as_json):
        return cls(**as_json)
        
    ...

```

### ReferenceTo Fields

ReferenceTo is really just a string field that is the key of another document. ReferenceTo fields are defined with the namespace and name of the type of the referenced document. 

```python 

"owner_id": ReferenceTo(NAMESPACE, "person")

```

The name should always end with `_id` , this indicates that it is a reference but it also support fam's lookup of related objects. This allows you to directly access related documents for example dog.owner_id will return the key of the owner document but dog.owner will return an instance of the Owner class for that document.

### ReferenceFrom Fields

ReferenceFrom fields are quite different and they have no representation within the json document. Instead they use the automatically created design documents to find a collection of documents with the associated ReferenceTo field. So ReferenceFrom fields only work with as existing ReferenceTo Field. They are defined with the namespace and the type that the reference is from and the name of the ReferenceTo field in that type.

```python

"dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id")

```
This gives way to do one-to-one and one-to-many relationships. In practice I find I tend to model immutable one-to-many relationships internally as lists of keys within documents and mutable ones with fam view lookups. I also create mutable one-to-one and many-to-many relationships with small join documents with compound keys. I also have write extra views by hand for more complex indexing.

## Field Options

There are five optional arguments when creating a field:

- **required** - A boolean, false by default that asserts that this field must be present.
- **immutable** - A boolean, false by default asserts that you cannot change the value of ths field once it has been set.
- **default** - A default value for this field that will be returned on read if this field is absent from the underlying json. None by default.
- **cascade_delete** - Only applies to ReferenceTo and ReferenceFrom fields. A boolean, false by default, which if true will delete the object the reference points to when this object is deleted.
- **unique** - The thing about uniqueness in a distributed data set is that it cannot be guaranteed, so this assertion is weaker than you would get in a monolithic dataset. This said it is still sometimes useful. It is a boolean, false by default, which if true will raise an exception when you try to add a document with a non unique field to a database using fam. It also helps provide the classmethod `get_unique_instance` which can be used like this:

```python
Cat.get_unique_instance(db, "email", "tiddles@glowinthedark.co.uk)
```

## Validation

Fam now uses JSON Schema http://json-schema.org to validate documents. Fam's mapper generates schemata dynamically from the class definitions and uses them to validate documents.

You can get the mapper to write out its internal schemata by calling ```mapper.validator.write_out_schemata(directory)```


## Writing Views

Couch views are fragments of JavaScript stored in design documents in the database. Fam automatically generates some design documents for you, those describing relationships between documents, but the chances are you will want to create some other views to help search for documents. Fam takes a minimalist approach to design documents. It provides two things: firstly, JavaScript parsing in the mapper so you can write design documents in JavaScript rather than json (which is nasty), you write in js and it turns them into json; secondly a simple method on the fam db object to query views.

You can use it like this:

Write JavaScript versions of you design documents with the views as vars in the global namespace in files with the desired name of the design document. eg

```javascript
var cat_legs = {
    map: function(doc){
        if(doc.type == "cat"){
            emit(doc.legs, doc)
        }
    }
}
```

Saved in a file called `animal_views.js`. Then pass the paths to you JavaScript design documents to the constructor for the mapper:

```python
mapper = ClassMapper([Dog, Cat, Person], designs=[".../animal_views.js"])

```

Then you can then query these views like this `db.view(viewpath, **kwargs)` where viewpath is a composite of design name and view name `design_name/view_name` and kwargs are the normal view query attributes for either CouchDB or Sync Gateway (they differ slightly), eg:

```python
cats_with_three_legs = db.view("animal_views/cat_legs", key=3)
```

## Write Buffer

This is a context managed in-memory object buffer. Reads pass through it so the same Python object always represents same db doc,
and document write are only saved back to the database when the context manager closes.

This replaces the old cache it is aliased to it so existing code won't break.


```python

from fam.buffer import buffered_db

# create a database db as usual

# then create an in memory cache in front of it
with buffered_db(db) as bdb:

    # now use bdb instead of db
    dog = Dog(name="fly")
    bdb.put(dog)
    
    # dog2 will be the exact same python object as dog
    dog2 = bdb.get(dog.key)
    
#when the context closes the docs are saved back to db
    
```

## Sync Function ACLs

Although I am a big fan Couchbase Sync Gateway I feel that the sync function is a little over burdened with responsibilities,
so I template some portions of my sync function that protect access to writing documents.
To support this I have added declarative acls in an additional class attribute on FamObjects. It looks like this:

```python
    acl = [
        CreateRequirement(role=ANYONE, owner=True),
        UpdateRequirement(role=NO_ONE, fields=["channels", "project_id", "immutable_name", "owner_name"]),
        UpdateRequirement(role=ANYONE, owner=True, fields=["name"]),
        DeleteRequirement(role=ANYONE, owner=True)
    ]
 ```
 This will not be useful for everyone or it all situations as it necessarily limits the flexibility of how the sync function works. It isn't fully documented here and still requires a clear understanding of how the sync function works, so tread carefully.
 
There is then a function in `fam.acl.writer` which takes two templates, a top level one for the json config function and inner one for the js sync function, and a mapper, to generate a complete config file.

```python
write_sync_function(template_path, output_path, sync_template_path, mapper)
```
The templating is crude, using simple string replacement to add a collection of the requirements to the js. Have a look at the function to see what it does. You can then apply the normal sync function checks with a function something like this:

```javascript
    function check(a_doc, req){

        if(req  === undefined){
            requireRole([]);
            return;
        }
        if(req.owner !== undefined){
            if(a_doc.owner_name === undefined){
                throw("owner_name not given");
            }
            requireUser(a_doc.owner_name);
        }
        if(req.withoutAccess === undefined){
            requireAccess(a_doc.channels);
        }
        if(req.user !== undefined){
            requireUser(req.user);
        }
        if(req.role !== undefined){
            requireRole(req.role);
        }
    }

```


##To Do?

Some possible further features:

- Optional class attribute **schema** to give better control over document validation.
- Pass schemata to sync gateway's sync function to enforce typed validation on document creation and update.

