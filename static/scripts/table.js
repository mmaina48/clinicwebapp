function send() {
    var myTab =  document.getElementById('normalpurchase').getElementsByTagName('tbody')[0];
    var arrValues = new Array();
    // loop through each row of the table.
    for (row = 0; row < myTab.rows.length; row++) {
        // loop through each cell in a row.
        for (c = 0; c < myTab.rows[row].cells.length; c++) {  
            var element = myTab.rows.item(row).cells[c];
            var element_type=element.firstElementChild.type
           console.log(element_type)
            if (element_type  == 'text' || element_type == 'number' || element_type == 'date')
             {
                arrValues.push({productname:myTab.rows[row].cells[0].children[0].value,
                expirydata:myTab.rows[row].cells[1].children[0].value,
                quantity:myTab.rows[row].cells[2].children[0].value,
                buying_price:myTab.rows[row].cells[3].children[0].value,
                total_price:myTab.rows[row].cells[4].children[0].value
             }); 
            }
        }
    }
    // function to remove duplicates
    function uniqBy(a, key) {
var seen = {};
return a.filter(function(item) {
    var k = key(item);
    return seen.hasOwnProperty(k) ? false : (seen[k] = true);
})
}
    var listz = arrValues 
    var uniqueNames = uniqBy(listz, JSON.stringify)
var data = {};
$("#insert_purchase").serializeArray().map(function(x){data[x.name] = x.value;}); 
var keys=["product_name","quantity","expiry_date","unit_cost","total_price"]
var i;
for (i = 0; i < keys.length; i++) {
    delete data[keys[i]]
}

var tabledata=uniqueNames
tabledata.push(data)

$.ajax({
    url: '/processpurchasedata',
    data: JSON.stringify(tabledata, null, '\t'),
    contentType: 'application/json;charset=UTF-8',
    type: 'POST',
    success: function(response){
        alert("Purchase Successfully Added")
        $('#successAlert').text(data.name).show();
        $('#errorAlert').hide();
        $("#insert_purchase")[0].reset();
        $('#addedrow').remove();
        
       
    },
    error: function(error){
        alert("The Make sure all required Field are not empty!")
        $('#errorAlert').text(data.error).show();
		$('#successAlert').hide();
        console.log(error);
    }
});

}
