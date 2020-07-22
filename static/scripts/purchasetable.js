function addRow() {
    // var empTab = document.getElementById('tab_logic');
    var empTab = document.getElementById('normalpurchase').getElementsByTagName('tbody')[0];
    var rowCnt = empTab.rows.length;   // table row count.
    var tr = empTab.insertRow(rowCnt); // the table row.
    tr = empTab.insertRow(rowCnt);
    

    for (var c = 0; c < 7; c++) {
        var td = document.createElement('td'); // table definition.
        td = tr.insertCell(c);
        tr.setAttribute("id","addedrow")

        if (c == 6) {     
            var button = document.createElement('input');
            button.setAttribute('type', 'button');
            button.setAttribute('value', 'Remove');
            button.setAttribute('tabindex','16');
            button.setAttribute('onclick', 'removeRow(this)');
            button.setAttribute('class','btn btn-danger btn-sm row-remove')
            td.appendChild(button);
        }

        else if(c==0){
            var ele = document.createElement('input');
            ele.setAttribute('type', 'text');
            ele.setAttribute('value', '');
            ele.setAttribute('name', 'product_name[]');
            ele.setAttribute('placeholder', 'Product Name');
            ele.setAttribute('tabindex','7');
            ele.setAttribute('class','form-control')
            ele.setAttribute("id", "name1");
            ele.setAttribute("list","id_datalist")
            td.appendChild(ele);
            
        }
        else if(c==1){
            var le = document.createElement('input')
            le.setAttribute('type', 'date')
            le.setAttribute('name', "expiry_date[]")
            le.setAttribute('id', "ExpDate")
            le.setAttribute('required',"")
            le.setAttribute('class','form-control')
            td.appendChild(le);
        }
        else if(c==2){
            var element = document.createElement('input');
            element.setAttribute('text', 'text');
            element.setAttribute('name', 'quantity[]');
            element.setAttribute('id', 'quantity_1');
            element.setAttribute('class','form-control text-right')
           
            td.appendChild(element)

            
        }
        else if(c==3){
           
            var element = document.createElement('input');
            element.setAttribute('text', 'text');
            element.setAttribute('name', 'reoder_level');
            element.setAttribute('id', 'reoder_level');
            element.setAttribute('placeholder',"Reoder level")
            element.setAttribute('value',"0")
            element.setAttribute('class','form-control text-right')
           
            td.appendChild(element)
        }
        else if(c==4){
            var ele = document.createElement('input')
            ele.setAttribute('type', 'number')
            ele.setAttribute('name', "unit_cost[]")
            ele.setAttribute('id', "total_qntt_1");
            ele.setAttribute('placeholder',"0.00")
            ele.setAttribute('class','form-control text-right')
            
            td.appendChild(ele)
        }

        else {
            var ele = document.createElement('input');
            ele.setAttribute('type', 'number')
            ele.setAttribute('name', 'total_price')
            ele.setAttribute('readonly','')
            ele.setAttribute('class','form-control text-right txtCal')
            ele.setAttribute('id', 'total')
            ele.setAttribute('placeholder', '0.00')
            td.appendChild(ele)
        }

    }
}

function removeRow(oButton) {
    var empTab = document.getElementById('normalpurchase');
    var total=oButton.parentNode.parentNode.children[5].children[0].value
    empTab.deleteRow(oButton.parentNode.parentNode.rowIndex); 
    document.getElementById("total_sum_value").value -=total
   
}


 $('#insert_purchase').on('change',"input" ,function(e) {
        var target=e.target
        if(target.matches("input#supplier_name")){
            var target=target.value
            prod=target
            fetch('/supplierdata/' + prod).then(function(response){
                response.json().then(function(data){
                    var lentha=data.Supplies.length
                    if (lentha==0){
                    alert("That Supplier is not registered!");
                       $("#supplier_name").val() = '';
                        return false;
                    }
                  let previousbal='';
                
                            for(let supplier of data.Supplies){
                                previousbal +=  supplier.openbalance 
                             }
                            document.getElementById('previous').value=previousbal
                    });
                
                });
            }
        });


$('#normalpurchase').on("click","input" ,function(e) {
    var target=e.target
    
    if(target.matches("input#quantity_1")){
        target.addEventListener('keyup' ,function(){
        
        const values =target.value;
     
        const price_td=target.parentNode.parentNode.children[4].children[0].value
        
        const total=values*price_td
        target.parentNode.parentNode.children[5].children[0].value=total
        
        

        var calculated_total_sum = 0
        $("#normalpurchase .txtCal").each(function () {
         var get_textbox_value = $(this).val();
         if ($.isNumeric(get_textbox_value)) {
            calculated_total_sum += parseFloat(get_textbox_value);
            
            } 
 
          })
          document.getElementById("total_sum_value").value=calculated_total_sum

          var calculated_net_sum = 0
          $("#normalpurchase .txtnet").each(function () {
           var get_textbox_value = $(this).val();
           if ($.isNumeric(get_textbox_value)) {
            calculated_net_sum += parseFloat(get_textbox_value);
              
              } 
   
            })
            document.getElementById("nettotal").value=calculated_net_sum
        //   end
        //   ** start calculating balance**

        // get the paid amout values
       
        var paid_amount_value = document.getElementById("paidAmount").value
        const netTotal=document.getElementById('nettotal').value
        const grandtotal=document.getElementById('total_sum_value').value
        const total_previous=document.getElementById('previous').value
        
        var paid_net=parseInt(paid_amount_value)-parseInt(netTotal)
        var paid_grand=parseInt(paid_amount_value)-parseInt(grandtotal)

       
        
        if(paid_grand<0 && paid_net < 0){
            var total_balance=paid_grand*-1
            document.getElementById('balance').value= total_balance
            document.getElementById('dueAmmount').value=parseInt(total_previous) + parseInt(total_balance)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="none";
        }
        else if(paid_grand==0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= parseInt(total_previous)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value=parseInt(total_previous)- parseInt(paid_grand)
            document.getElementById('OpenBalance').value= paid_grand
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= total_previous
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand==0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_net>0 && paid_grand>0){
           
            
            $("#paidAmount").value = '';
            return false;
        }
        
        // end calculating 
        })
        }
        if(target.matches("input#total_qntt_1")){

            target.addEventListener('keyup' ,function(){
           
            const values =target.value;
            
            const quantity=target.parentNode.parentNode.children[2].children[0].value
            
            
            const total=values*quantity
            
            
            target.parentNode.parentNode.children[5].children[0].value=total

            var calculated_total_sum = 0

        $("#normalpurchase .txtCal").each(function () {
         var get_textbox_value = $(this).val();
         if ($.isNumeric(get_textbox_value)) {
            calculated_total_sum += parseFloat(get_textbox_value);
            
            } 
 
          })
          document.getElementById("total_sum_value").value=calculated_total_sum
          var calculated_net_sum = 0
          $("#normalpurchase .txtnet").each(function () {
           var get_textbox_value = $(this).val();
           if ($.isNumeric(get_textbox_value)) {
            calculated_net_sum += parseFloat(get_textbox_value);
              
              } 
   
            })
            document.getElementById("nettotal").value=calculated_net_sum
        //   end

        var paid_amount_value = document.getElementById("paidAmount").value
        const netTotal=document.getElementById('nettotal').value
        const grandtotal=document.getElementById('total_sum_value').value
        const total_previous=document.getElementById('previous').value
        
        var paid_net=parseInt(paid_amount_value)-parseInt(netTotal)
        var paid_grand=parseInt(paid_amount_value)-parseInt(grandtotal)

       
        
        if(paid_grand<0 && paid_net < 0){
            var total_balance=paid_grand*-1
            document.getElementById('balance').value= total_balance
            document.getElementById('dueAmmount').value=parseInt(total_previous) + parseInt(total_balance)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="none";
        }
        else if(paid_grand==0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= parseInt(total_previous)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value=parseInt(total_previous)- parseInt(paid_grand)
            document.getElementById('OpenBalance').value= paid_grand
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= total_previous
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand==0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_net>0 && paid_grand>0){
           
            
            $("#paidAmount").value = '';
            return false;
        }
        
        // end calculating 
            })
        }
        if(target.matches("input#paidAmount")){
            target.addEventListener('keyup' ,function(){
                const values =target.value;
                const netTotal=document.getElementById('nettotal').value
                const grandtotal=document.getElementById('total_sum_value').value
                const total_previous=document.getElementById('previous').value
                var paid_net=parseInt(values)-parseInt(netTotal)
                var paid_grand=parseInt(values)-parseInt(grandtotal)
                if(paid_grand<0 && paid_net < 0){
                    var total_balance=paid_grand*-1
                    document.getElementById('balance').value= total_balance
                    document.getElementById('dueAmmount').value=parseInt(total_previous) + parseInt(total_balance)
                    document.getElementById('OpenBalance').value= 0
                    document.getElementById("full_paid_tab").style.display="none";
                }
                else if(paid_grand==0 && paid_net<0){
                    document.getElementById('balance').value= 0
                    document.getElementById('dueAmmount').value= parseInt(total_previous)
                    document.getElementById('OpenBalance').value= 0
                    document.getElementById("full_paid_tab").style.display="block";
                }
                else if(paid_grand>0 && paid_net<0){
                    document.getElementById('balance').value= 0
                    document.getElementById('dueAmmount').value=parseInt(total_previous)- parseInt(paid_grand)
                    document.getElementById('OpenBalance').value= paid_grand
                    document.getElementById("full_paid_tab").style.display="block";
                }
                else if(paid_grand>0 && paid_net==0){
                    document.getElementById('balance').value= 0
                    document.getElementById('dueAmmount').value= 0
                    document.getElementById('OpenBalance').value= total_previous
                    document.getElementById("full_paid_tab").style.display="block";
                }
                else if(paid_grand==0 && paid_net==0){
                    document.getElementById('balance').value= 0
                    document.getElementById('dueAmmount').value= 0
                    document.getElementById('OpenBalance').value= 0
                    document.getElementById("full_paid_tab").style.display="block";
                }
                else if(paid_net>0 && paid_grand>0){
                   
                    alert("Your Paying More than Net-Total");
                    $("#paidAmount").value = '';
                    return false;
                }
            })
        }
    });
    $(document).on('change','#expiry_date',function(e){
        var purdates =  $("#dtpDate").val();
        var expiredate = e.target.value;
        var purchasedate = new Date(purdates);
        var expirydate = new Date(expiredate);

        if (expirydate <= purchasedate ) { 
            alert('Expiry Date should be greater than Puchase Date');
            e.target.value = '';
            return false;
        }
        return true;
    });

    $( "#target" ).keyup(function() {
        
        var paid_amount_value = document.getElementById("paidAmount").value
        const netTotal=document.getElementById('nettotal').value
        const grandtotal=document.getElementById('total_sum_value').value
        const total_previous=document.getElementById('previous').value
        
        var paid_net=parseInt(paid_amount_value)-parseInt(netTotal)
        var paid_grand=parseInt(paid_amount_value)-parseInt(grandtotal)

       
        
        if(paid_grand<0 && paid_net < 0){
            var total_balance=paid_grand*-1
            document.getElementById('balance').value= total_balance
            document.getElementById('dueAmmount').value=parseInt(total_previous) + parseInt(total_balance)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="none";
        }
        else if(paid_grand==0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= parseInt(total_previous)
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net<0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value=parseInt(total_previous)- parseInt(paid_grand)
            document.getElementById('OpenBalance').value= paid_grand
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand>0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= total_previous
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_grand==0 && paid_net==0){
            document.getElementById('balance').value= 0
            document.getElementById('dueAmmount').value= 0
            document.getElementById('OpenBalance').value= 0
            document.getElementById("full_paid_tab").style.display="block";
        }
        else if(paid_net>0 && paid_grand>0){
           
            
            $("#paidAmount").value = '';
            return false;
        }
        
        // end calculating 
      });