
var HivePlot = {
  init: function(container, data, config) {
    config = config || {};
    if (!data) {
      throw new Error("Cannot initialize Hive plot, invalid data provided: " + data);
    }
    var width = config.width || "auto",
        height = config.height || "auto",
        radius = config.radius || "auto",
        selector = config.selector,
        axisMapping = {},
        radiusMapping = {},
        itemCounters = {},
        itemStep = {},
        getNodeCode = function(node){
          //TODO: entities can have code
          return node.name.replace(/[\s\.]/g,"_");
        };

    relationalPlotHelpers.displayResources(Object.keys(data.resources).length);
    relationalPlotHelpers.displayRelations(data.relations.length);
    relationalPlotHelpers.displayScrapeTime(data.date);


    function render(){
      var container = d3.select(selector),
          targetHeight=height,
          targetWidth=width,
          targetRadius=radius;
      if(width === "auto"){
          targetWidth = container.node().clientWidth;
      }
      if(height === "auto"){
          targetHeight = container.node().clientHeight;
      }
      if(radius === "auto"){
          targetRadius= Math.min(targetWidth, targetHeight) * 0.4;
      }
      container.html("");
      var plotFunctions = {
        createAxes: function(items) {
          return items.map(function(item, index) {
            item.icon.color = d3.schemeCategory20[index];
            iconMapping[item.kind] = item.icon;
            itemCounters[item.kind] = 0;
            axisMapping[item.kind] = item.x;
            itemStep[item.kind] = 1 / item.items;
            radiusMapping[item.kind] = d3.scaleLinear()
              .range([item.innerRadius*targetRadius, item.outerRadius*targetRadius]);
            return item;
          });
        },
        createNodes: function(items) {
          return items.map(function(item) {
            item["x"] = axisMapping[item.kind];
            itemCounters[item.kind]++;
            item["y"] = itemCounters[item.kind];
            return item;
          });
        },
        createLinks: function(nodes, relations) {
          return relations.map(function(link) {
            var retLink = {};
            nodes.forEach(function(node) {
              if (link.source == node.id) {
                retLink.source = node;
              } else if (link.target == node.id) {
                retLink.target = node;
              }
            });
            if (!retLink.hasOwnProperty("source") || !retLink.hasOwnProperty("target")) {
              console.log("Can not find relation node for link " + link);
              retLink = link;
            }
            return retLink;
          });
        }
      };

      if (typeof data.axes === 'object') {
        data.axes = Object.values(data.axes);
      }

      if (typeof data.resources === 'object') {
        data.resources = Object.values(data.resources);
      }

      var axes = plotFunctions.createAxes(data.axes);
      var nodes = plotFunctions.createNodes(data.resources);
      var links = plotFunctions.createLinks(nodes, data.relations);

      console.log(nodes);

      var angle = function(d) {
        var angle = 0,
            found = false;
        axes.forEach(function(item) {
          if (d.kind == item.kind) {
            angle = item.angle;
            found = true;
          }
        });
        if (!found) {
          console.log("Cannot compute angle for " + d.kind + " " + d.name)
        }
        return angle;
      }

      var svg = container
        .append("svg")
        .attr("width", targetWidth)
        .attr("preserveAspectRatio","xMidYMid meet")
        .attr("height", targetHeight)
        .append("g")
        .attr("transform", "translate(" + (targetWidth / 2) + "," + (targetHeight / 2) + ")");

      var mouseFunctions = {
        linkOver: function(d) {
          svg.selectAll(".link").classed("active", function(p) {
            return p === d;
          });
          svg.selectAll(".node circle").classed("active", function(p) {
            return p === d.source || p === d.target;
          });
          svg.selectAll(".node text").classed("active", function(p) {
            return p === d.source || p === d.target;
          });
        },
        nodeOver: function(d) {
          var $elem = d3.select(this);
          svg.selectAll(".link").classed("active", function(p) {
            return p.source === d || p.target === d;
          });
          svg.selectAll(".link.active").each(function(link){
            svg.selectAll(".node.node-"+getNodeCode(link.target)+", .node.node-"+getNodeCode(link.source))
            .classed("active",true);
          });
          $elem.classed("active") || $elem.classed("active",true);
          tooltip.html("Node - " + d.name + "<br/>" + "Kind - " + d.kind)
            .style("left", (d3.event.pageX + 5) + "px")
            .style("top", (d3.event.pageY - 28) + "px");
          tooltip.transition()
            .duration(200)
            .style("opacity", .9);
        },
        out: function(d) {
          svg.selectAll(".active").classed("active", false);
          tooltip.transition()
            .duration(500)
            .style("opacity", 0);
        }
      };

      var tooltip = d3.select("#HiveChartTooltip");
      // tooltip is d3 selection
      if(tooltip.empty()){
        tooltip = d3.select("body").append("div")
              .attr("id", "HiveChartTooltip")
              .attr("class", "tooltip")
             .style("opacity", 0);
      }

      // Plot render
      var axe = svg.selectAll(".node").data(axes)
        .enter().append("g");

      axe.append("line")
        .attr("class", "axis")
        .attr("transform", function(d) {
          return "rotate(" + d.angle + ")";
        })
        .attr("x1", function(d) {
          return radiusMapping[d.kind].range()[0]
        })
        .attr("x2", function(d) {
          return radiusMapping[d.kind].range()[1]
        });

      axe.append("text")
        .attr("class", "axis-label")
        .attr('font-size', '16px')
        .attr('font-family', 'Open Sans')
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'central')
        .text(function(d) {
          return d.name;
        })
        .attr("transform", function(d) {
          var x = (radiusMapping[d.kind].range()[1] + 30) * Math.cos(Math.radians(d.angle));
          var y = (radiusMapping[d.kind].range()[1] + 30) * Math.sin(Math.radians(d.angle));
          return "translate(" + x + ", " + y + ")";
        });

      svg.selectAll(".link").data(links)
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.hive.link()
          .angle(function(d) {
            return Math.radians(angle(d));
          })
          .radius(function(d) {
            return radiusMapping[d.kind](d.y * itemStep[d.kind] - 0.1);
          }))
        .on("mouseover", mouseFunctions.linkOver)
        .on("mouseout", mouseFunctions.out);

      var node = svg.selectAll(".node").data(nodes)
        .enter().append("g")
        .attr("class",function(d){
          return "node node-"+getNodeCode(d);
         })
        .attr("transform", function(d) {
          var x = radiusMapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.cos(Math.radians(angle(d)));
          var y = radiusMapping[d.kind](d.y * itemStep[d.kind] - 0.1) * Math.sin(Math.radians(angle(d)));
          return "translate(" + x + ", " + y + ")";
        });

      node.append("circle")
        .attr("r", 16)

      node.append("text")
        .attr('fill', function(d) { return iconFunctions.color(d.kind); })
        .attr('font-size', function(d) { return iconFunctions.size(d.kind); })
        .attr('font-family', function(d) { return iconFunctions.family(d.kind); })
        .text(function(d) { return iconFunctions.character(d.kind); })
        .attr("transform", function(d) { return iconFunctions.transform(d.kind); });

      node.on("mouseover", mouseFunctions.nodeOver)
          .on("mouseout", mouseFunctions.out);

      node.on("click", function(node){
        svg.selectAll(".node").classed("selected", function(d) { return d === node; });
        svg.selectAll(".link").classed("selected", function(p) {
          return p.source === node || p.target === node;
        });
        if(config.hasOwnProperty("nodeClickFn") && typeof config.nodeClickFn === 'function'){
            config.nodeClickFn(node);
        }
      });
    }
    render();
    window.removeEventListener('resize', render);
    window.addEventListener('resize', render);
  }
};