var nodes = {};
var jsonURL = "/api.json?inst=" + institution;
//var jsonURL = "/graph.json";
var links, path;


d3.json(jsonURL, function(json) {
  links = json.children;

  //Toggle children on click.
  function click(d) {
      if (d3.event.defaultPrevented) return; // click suppressed
      centerNode(d);
  }

  var width = 1440,
      height = 1028,
      duration = 750;
  var zoomable_layer;

   // Compute the distinct nodes from the links.
  links.forEach(function(link) {
    link.source = nodes[link.source] || (nodes[link.source] = {name: link.source, size: link.size, type: "source", institution: link.institution});
    link.target = nodes[link.target] || (nodes[link.target] = {name: link.target, size: link.size, type: "target"});
  });


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
      var zoomListener = d3.zoom().scaleExtent([0.1, 3]).on("zoom", function() {
          return zoomable_layer.attr("transform", d3.event.transform);
        });

      var fLinks = d3.forceLink(links);
      fLinks.distance(40);
      var force = d3.forceSimulation()
          .nodes(d3.values(nodes))
          .force("link", fLinks)
          .force("charge", d3.forceManyBody().strength(-300))
          .on("tick", tick);

      var svg = d3.select("body").append("svg")
          .attr("width", width)
          .attr("height", height)
          .attr("class", "bg")
          .call(zoomListener);
      zoomable_layer = svg.append('g');


      var link = zoomable_layer
        .attr("class", "links")
        .selectAll("path")
        .data(links)
        .enter().append("svg:path")
        .attr("stroke-width", function(d) { return 1 });

      link.style('fill', 'none')
        .style('stroke', 'black')
        .style("stroke-width", '2px');

      var node = zoomable_layer //.append('g')
        .attr("class", "nodes")
        .selectAll("g")
        .data(d3.values(nodes))
        .enter().append("g")
        .style('transform-origin', '50% 50%')
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
        );

      node.append("circle")
        .attr("class", function(d) { return d.type; })
        .attr("r", 5)
        .style("fill", function(d) {return d.institution || "yellow"; })
        .style("stroke-width", "2px")
        .attr("id", function(d) { return d.id; });

      node.append("text")
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .text(function(d) { return d.name; });

      // Use elliptical arc path segments to doubly-encode directionality.
      function tick() {
        link.attr("d", linkArc);
        node.attr("transform", transform);
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

      function dragstarted(d) {
        if (!d3.event.active) force.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
      }

      function dragended(d) {
        if (!d3.event.active) force.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
});

