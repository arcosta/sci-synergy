/**
 * 
 */

var count = 11;
function addInputText()
{
	var div = document.getElementsByName("extQuestion")[0];
	
	
	
	var inputRate = document.createElement("input");
	inputRate.type="text";
	inputRate.name="ps5text"+String(count);
	inputRate.size="2";
	inputRate.setAttribute("maxlength", "2");
	count +=1;
	
	var inputName = document.createElement("input");
	inputName.type="text";
	inputName.name="ps5text"+String(count);
	inputName.setAttribute("onfocus","if(this.value == 'Qual criterio ?') { this.value = ''; }");
	inputName.value="Qual criterio ?";	
	count +=1;
	
	var br = document.createElement("br");
	
	div.appendChild(inputRate);
	div.appendChild(inputName);
	div.appendChild(br);
}

$(function() {
    function log( message ) {
      $( "<div>" ).text( message ).prependTo( "#log" );
      $( "#log" ).scrollTop( 0 );
    }

    
$(function() {
    $("input.acmarea").autocomplete({
    	source: function( request, response ){
    		$.ajax({
    			url: "autocomplete",
    			dataType: "json",
    			data: {
    				partial: request.term
    			},
    			success: function(data){
    				response( data );
    			}
    		});
    	},
    	minLength: 3,
    	select: function(event, ui){
    		log(ui.item ? "Selected: " + ui.item.label : "Nothing selected, input was " + this.value);
    	},
    	open: function(){
    		$(this).removeClass("ui-corner-all").addClass("ui-corner-top");
    	},
    	close: function() {
    		$(this).removeClass("ui-corner-top").addClass("ui-corner-all");
    	}
    });
  });
});