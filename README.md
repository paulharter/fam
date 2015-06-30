#fam

A simple Python ORM for Couchdb, Couchbase and Couchbase Sync Gateway. 

Fam is a work in progress growing as the needs of my current project dictate. This means that while very useful it is not a feature complete ORM. It is probably most useful if, like me, you want to use Couch family noSQL DBs for their handling of distributed data sets but have highly relational data.

Fam adds a type and namespace to each document:

- **type** - A lower case string derived from the class name
- **namespace** - An opaque string to help avoid class name clashes and allow versioning of classes

And uses them to provide:

- A class to bind methods to documents
- Automatic generation of design documents for relationships between classes
- Lookup of related documents
- Some validation of documents (currently a bit broken)
- Document life-cycle callbacks for creation, updates and deletion
- Optional cascading deletion through relationships

You can define a fam class like this:

```python

NAMESPACE = "mynamespace"

class Dog(GenericObject):
    use_cas = True
    additional_fields = True
    fields = {
        "name": StringField(),
        "owner_id": ReferenceTo(NAMESPACE, "person", delete="cascade")
        }

    def talk(self):
        return "woof"

```

and then use it to create a document like this:

```python
dog = Dog(name="fly")
dog.save(db)

```

##Databases

fam has wrappers for connecting to different databases:

- CouchDB
- Couchbase
- Couchbase Sync Gateway

These wrapper classes are stateless and thread safe, at least the CouchDB and Sync Gateway ones certainly are as they use the requests library to manage connection pooling and keep alive. The Couchbase one probably is too but it uses Couchbase's own libraries to connect to the db.
 
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
 
 The db objects are passed around everywhere in fam object method calls. This is a conscious design choice rather than hiding it away in a singleton somewhere.
 
##Classes
 
 Fam classes are defined as inheriting from fam.blud.GenericObject like this:


 ```python 
 
class Cat(GenericObject):
    use_cas = True
    additional_fields = False
    fields = {
        "name": StringField(),
        "legs": NumberField(),
        "owner_id": ReferenceTo(NAMESPACE, "person")
        }
 
 ```
 
 With three class attributes
 
 - **use_cas** - A boolean which if true uses the default rev/cas collision protection of Couch DBs but if false always forces a document update as if this mechanism didn't exist
 - **additional_fields** - A boolean which if true lets you add arbitrary additional top level attributes to an object and if flase will throw an exception when you try.
 - **fields** - A dict of named fields that map to the top level attributes of the underlying json documents. See below for use.

These classes have these methods provided by GenericObject:

- **get(cls, db, key)** - Instantiate an instance of this class using the document with this key from this database

And their instances have:
 
- **save(self, db)** - Save this object to this database
- **delete(self, db)** - Remove this object from this database
 
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

When defining a fam class you instantiate each of fields for the class and give it a name eg `"name": StringField()`

There are two optional arguments when creating a field that are used for validating documents:

- **optional** - A boolean, false by default that ensures that an attribute exists when the document is saved.
- **unique** - A boolean, false by default that ensures that an attribute is unique across documents in this class.

## NB WARNING - OPTIONAL AND UNIQUE ARE NOT CURRENTLY IMPLEMENTED IN VALIDATION

There are two additional field types that are used to define relationships.

###ReferenceTo

ReferenceTo is really just a string field that is the key of another document. ReferenceTo fields are defined with the namespace and name of the class of the referenced document. 

```python 

"owner_id": ReferenceTo(NAMESPACE, "person")

```

The name should always end with `_id` , this indicates that it is a reference but it also support fam's lookup of related objects. This allows you to directly access related documents for example dog.owner_id will return the key of the owner document but dog.owner will return an instance of the Owner class for that document.

###ReferenceFrom

ReferenceFrom fields are quite different and they have no representation within the json document. Instead they use the automatically created design documents to find a collection of documents with the associated ReferenceTo field. So ReferenceFrom fields only work with as existing ReferenceTo Field. They are defined with the namespace and the class that the reference is from and the name of the ReferenceTo field in that class.

```python

"dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id")

```

This gives way to do one-to-one and one-to-many relationships. In practice I find I tend to model immutable one-to-many relationships internally as lists of keys within documents and mutable ones with fam view lookups. I also create mutable one-to-one and many-to-many relationships with small join documents with compound keys. I also have write extra views by hand for more complex indexing.
