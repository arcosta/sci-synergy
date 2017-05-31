
var nodes = {};
var jsonURL = "/api.json?inst=" + institution;
var links, path;


d3.json(jsonURL, function(json) {
  links = json.children;
  
  //Toggle children on click.
  function click(d) {
      if (d3.event.defaultPrevented) return; // click suppressed

      centerNode(d);
      update(d);
  }
  
  function update(){
	  var width = 1440,
      height = 1028,
      duration = 750;

	    // Compute the distinct nodes from the links.
	    links.forEach(function(link) {
	      link.source = nodes[link.source] || (nodes[link.source] = {name: link.source, size: link.size, type: "source", institution: link.institution});
	      link.target = nodes[link.target] || (nodes[link.target] = {name: link.target, size: link.size, type: "target"});
	    });
	    
	  //Define the zoom function for the zoomable tree
	    function zoom() {
	        svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
	    }
	  
	  	//Function to center node when clicked/dropped so node doesn't get lost when collapsing/moving with large amount of children.
	    function centerNode(source) {
	        scale = zoomListener.scale();
	        x = -source.y0;
	        y = -source.x0;
	        x = x * scale + width / 2;
	        y = y * scale + height / 2;
	        d3.select('g').transition()
	            .duration(duration)
	            .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
	        zoomListener.scale(scale);
	        zoomListener.translate([x, y]);
	    }
	  
	  	//define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
	    var zoomListener = d3.behavior.zoom().scaleExtent([0.1, 3]).on("zoom", zoom);

	    var force = d3.layout.force()
	        .nodes(d3.values(nodes))
	        .links(links)
	        .size([width, height])
	        .linkDistance(60)
	        .charge(-300)
	        .on("tick", tick)
	        .start();

	    var svg = d3.select("body").append("svg")
	        .attr("width", width)
	        .attr("height", height)
	        .call(zoomListener);
	    
	 
	    var svgGroup = svg.append("g");

	    var path = svgGroup.selectAll("path")
	        .data(force.links())
	      .enter().append("path")
	        .attr("class", function(d) { return "link " + d.size; })
	        .attr("stroke-width", function(d){ return (d.rel_count/2)+"px"; })
	        .attr("marker-end", function(d) { return "url(#" + d.size + ")"; });

	    var circle = svgGroup.selectAll("circle")
	        .data(force.nodes())
	      .enter().append("circle")
	        .attr("r", function(d) { return d.size; })
	        .attr("class", function(d) { return d.type; })
	        .style("fill", function(d) {return d.institution || "yellow"; })
	        .call(force.drag)
	        .on("click", centerNode);

	    var text = svgGroup.selectAll("text")
	        .data(force.nodes())
	      .enter().append("text")
	        .attr("x", 8)
	        .attr("y", ".31em")
	        .text(function(d) { return d.name; });

	        
	    // Use elliptical arc path segments to doubly-encode directionality.
	    function tick() {
	      path.attr("d", linkArc);
	      circle.attr("transform", transform);
	      text.attr("transform", transform);
	    }
	    
	    function linkArc(d) {
	      var dx = d.target.x - d.source.x,
	          dy = d.target.y - d.source.y,
	          dr = Math.sqrt(dx * dx + dy * dy);
	      return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
	    }

	    function transform(d) {
	      return "translate(" + d.x + "," + d.y + ")";
	    }
	}

  update();  
});
