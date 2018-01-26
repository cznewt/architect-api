var RelationalPlot = function(RelationalPlot){
    /**
     * Force-directed diagram rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.forceDirected = function(dataUrl, graphSelector, refreshInterval) {

        var width,
            height,
            chartWidth,
            chartHeight,
            margin = {top:0, left:0, bottom:0, right:0 };

        var graph = this;

        this._data = {};

        this.init = function(alreadyRunning) {
            if(!dataUrl || !graphSelector){
                throw new Error("Cannot init graph, dataUrl or graphSelector not defined");
            }

            if(alreadyRunning && graph.svg) {
                graph.svg.remove();
            }

            graph.svg = d3.select(graphSelector).append("svg"),
            graph.chartLayer = graph.svg.append("g").classed("chartLayer", true);

            graph.setSize();

            if(!alreadyRunning) {
                graph.requestData(dataUrl, graph.render);
                $(window).on('resize', function(ev){
                    graph.init(true);
                    graph.render();
                });

                if(refreshInterval){
                    setInterval(function(){
                        graph.requestData(dataUrl, function(){
                            graph.init(true);
                            graph.render();
                        });
                    }, refreshInterval * 1000);
                }
            }
        };

        this.setSize = function() {
            width = document.querySelector(graphSelector).clientWidth;
            height = document.querySelector(graphSelector).clientHeight;
        
            margin = {top:0, left:0, bottom:0, right:0 };
            
            chartWidth = width - (margin.left+margin.right);
            chartHeight = height - (margin.top+margin.bottom);
            
            graph.svg.attr("width", width).attr("height", height)
            
            graph.chartLayer
                .attr("width", chartWidth)
                .attr("height", chartHeight)
                .attr("transform", "translate("+[margin.left, margin.top]+")")                
        }

        this.render = function() {
            graph.createAxes(Object.values(graph._data.axes));
            var nodes = graph.createNodes(Object.values(graph._data.resources));
            var links = graph.createLinks(nodes, graph._data.relations);

            var simulation = d3.forceSimulation()
                .force("link", d3.forceLink().id(function(d) { return d.index }))
                .force("collide",d3.forceCollide( function(d){return d.r + 20 }).iterations(16) )
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(chartWidth / 2, chartHeight / 2))
                .force("y", d3.forceY(0))
                .force("x", d3.forceX(0));

            var link = graph.svg.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(links)
                .enter()
                .append("line")
                .attr("stroke", "black")

            var node = graph.svg.append("g")
                .attr("class", "nodes")
                .selectAll("circle")
                .data(nodes)
                .enter().append("g")
                    .attr("class", "node");

            node.append("circle")
                .attr("r", 16)

            node.append("text")
                .attr('fill', function(d) { return iconFunctions.color(d.kind); })
                .attr('font-size', function(d) { return iconFunctions.size(d.kind); })
                .attr('font-family', function(d) { return iconFunctions.family(d.kind); })
                .text(function(d) { return iconFunctions.character(d.kind); })
                .attr("transform", function(d) { return iconFunctions.transform(d.kind); });

            var ticked = function() {
                link
                    .attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node
                    .attr("transform", function(d){
                        return "translate(" + d.x + ", " + d.y + ")"
                    });
            };

            simulation
                .nodes(nodes)
                .on("tick", ticked);

            simulation.force("link")
                .links(links);

            function dragstarted(d) {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(d) {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
            }

            function dragended(d) {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        };

        this.createNodes = function(items) {
          return items.map(function(item) {
            item["r"] = 10;
            return item;
          });
        };

        this.createAxes = function(items) {
          items.map(function(item, index) {
            item.icon.color = d3.schemeCategory20[index];
            iconMapping[item.kind] = item.icon;
          });
        };

        this.createLinks = function(nodes, relations) {
          return relations.map(function(link) {
            var retLink = {};
            nodes.forEach(function(node, index) {
              if (link.source == node.id) {
                retLink.source = index;
              } else if (link.target == node.id) {
                retLink.target = index;
              }
            });
            if (!retLink.hasOwnProperty("source") || !retLink.hasOwnProperty("target")) {
              console.log("Can not find relation node for link " + link);
              retLink = link;
            }
            return retLink;
          });
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                graph._data = res;
                relationalPlotHelpers.displayResources(Object.keys(graph._data.resources).length);
                relationalPlotHelpers.displayRelations(graph._data.relations.length);
                relationalPlotHelpers.displayScrapeTime(res.date);
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };

    };
    return RelationalPlot;
}(RelationalPlot || {});
