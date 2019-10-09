




SCHEMA_ID = "TEMPLATE_SCHEMA_ID"


def mutate(db, doc):

    colour = doc.colour
    if colour is None:
        doc.colour = "red"

    doc.schema = SCHEMA_ID
    doc.save(db)


