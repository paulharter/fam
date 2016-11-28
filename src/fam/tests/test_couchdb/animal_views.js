
var cat_legs = {
    map: function(doc){
        if(doc.type == "cat"){
            emit(doc.legs, doc)
        }
    }
}