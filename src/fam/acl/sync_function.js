sync = function(doc, oldDoc) {

    function values_are_equal(list_a, list_b){

        if(list_a === undefined && list_b === undefined ){
            return true;
        }
        if(list_a === undefined && list_b !== undefined ){
            return false;
        }

        if(list_a.join !== undefined){
            return list_a.join() == list_b.join();
        }
       else{
            return list_a == list_b;
        }
    }

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

    var REQUIREMENTS_LOOKUP = "REQUIREMENTS_LOOKUP";
    var ACCESS_TYPES = "ACCESS_TYPES";

    var req;



    
    // This does requirements

    if(doc["_deleted"] == true){
        if(oldDoc) {
            if(oldDoc.type  === undefined){
                throw("type not given");
            }
            /* deleting a doc */
            req = REQUIREMENTS_LOOKUP["delete"][oldDoc.type];
            check(oldDoc, req);
        }
        else {
            throw("You can't delete something already deleted")
        }
    }
    else {
        if(doc.type  === undefined){
            throw("type not given");
        }
        doc_type = doc.type;
        if(oldDoc){
            if(doc.type != oldDoc.type){
                throw("types has changed");
            }
            // there are set of update requirements
            var updateReqs = REQUIREMENTS_LOOKUP["update"][oldDoc.type];
            if(updateReqs === undefined){
                requireRole([]);
            }
            else{
                for (var i = 0; i < updateReqs.length; i++) {
                    req = updateReqs[i];
                    // if no fields are defined then check
                    if(req.fields === undefined){
                        check(oldDoc, req);
                    }
                    else{
                        // // otherwise only do the checks if one of the named fields has changed
                        for (var j = 0; j < req.fields.length; j++) {
                            var field_name = req.fields[j];
                            if (!values_are_equal(oldDoc[field_name], doc[field_name])){
                                check(oldDoc, req);
                                break;
                            }
                        }
                    }
                }
            }
        }
        else{
            req = REQUIREMENTS_LOOKUP["create"][doc.type];
            check(doc, req);
        }
    }
    
       // grant users whose names or groups are in doc.access to channel called doc._id
    if(ACCESS_TYPES.indexOf(doc.type) != -1){
        console.log("granting access to " + doc.access)
        access(doc.access, doc._id);
    }

    channel(doc.channels);

}