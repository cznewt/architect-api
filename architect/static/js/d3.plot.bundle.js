var RelationalPlot = function(RelationalPlot){
    /**
     * Hierarchical edge bundling rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.hierarchicalEdgeBundling = function(dataUrl, graphSelector, refreshInterval) {
        var contentWidth = $(graphSelector).innerWidth(),
            diameter = contentWidth,
            radius = diameter / 2,
            innerRadius = radius - 120;

        var line_color = function(d){
                var color = "#C7C7C7";
                if(d.hasOwnProperty("source") && d.hasOwnProperty("target")){
                    d.source.relations.forEach(function(item){
                        if(item.status === "success"){
                            color = "#00BB00";
                        }else if(item.status === "failed"){
                            color = "#FF0000";
                        }
                    });
                }
                return color;
            },
            color_arc = d3.scaleOrdinal(d3.schemeCategory10),
            cross = function(a, b) {
                return a[0] * b[1] - a[1] * b[0];
            },
            dot = function(a, b) {
                return a[0] * b[0] + a[1] * b[1];
            },
            mouseCoordinates = function(e) {
                return [e.pageX - rx, e.pageY - ry];
            },
            graph = this;

        this._data = {};

        this.init = function(alreadyRunning) {
            if(!dataUrl || !graphSelector){
                throw new Error("Cannot init graph, dataUrl or graphSelector not defined");
            }

            graph.cluster = d3.cluster()
                .size([360, innerRadius]);

            graph.line = d3.radialLine()
                .curve(d3.curveBundle.beta(0.85))
                .radius(function(d) { return d.y; })
                .angle(function(d) { return d.x / 180 * Math.PI; })
            if(alreadyRunning && graph.svg) {
                d3.select(graph.svg.node().parentNode).remove();
            }

            graph.svg = d3.select(graphSelector).append("svg")
                .attr("width", diameter)
                .attr("height", diameter)
              .append("g")
                .attr("transform", "translate(" + radius + "," + radius + ")");

            if(!alreadyRunning){
                graph.requestData(dataUrl, graph.render);
                $(window).on('resize', function(ev){
                    graph.resetPosition();
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

        this.render = function() {
            if(graph._data && graph._data.length > 0){

                var root = relationalPlotHelpers.nodeHierarchy(graph._data)
                    .sum(function(d) { return d.size; });
                var nodes = graph.cluster(root);
                var links = nodes.links();
                var rootNode = root.children[0];
                var groupData = graph.svg.selectAll("g.group")
                    .data(rootNode.children)
                    .enter().append("group")
                    .attr("class", "group")

                var groupArc = d3.arc()
                    .innerRadius((diameter/2))
                    .outerRadius((diameter/2) - 30)
                    .startAngle(function(d) {
                        return (graph.findStartAngle(d.__data__.children) - 3) * Math.PI / 180;
                    })
                    .endAngle(function(d) {
                        return (graph.findEndAngle(d.__data__.children) + 3) * Math.PI / 180
                    });


                graph.svg.selectAll("g.arc")
                    .data(groupData.nodes())
                    .enter().append("svg:path")
                    .attr("id",function(d){
                        return d.__data__.data.key.replace(/\./g,"_");
                    })
                    .attr("data-node-host",function(d){
                        return d.__data__.data.key;
                    })
                    .attr("d", groupArc)
                    .attr("class", "groupArc")
                    .style("fill", function(d,i) {
                        return color_arc(i);
                    });

                var groupArc2 = d3.arc()
                    .innerRadius((diameter/2) - 30)
                    .outerRadius((diameter/2) - 150)
                    .startAngle(function(d) {
                        return (graph.findStartAngle(d.__data__.children) - 3) * Math.PI / 180;
                    })
                    .endAngle(function(d) {
                        return (graph.findEndAngle(d.__data__.children) + 3) * Math.PI / 180
                    });


                graph.svg.selectAll("g.arc")
                    .data(groupData.nodes())
                    .enter().append("svg:path")
                    .attr("d", groupArc2)
                    .attr("class", "groupArc")
                    .style("fill", function(d,i) {
                        return "gray";
                    });

                graph.svg.selectAll("path.groupArc").nodes().forEach(function(group){
                    var arc = d3.select(group),
                        nodeHostId = arc.attr("id");
                        nodeHost = arc.attr("data-node-host");

                    d3.select("g").append("text")
                    .style("font-size",12)
                    .style("fill","#F8F8F8")
                    .attr("dy", 17)
                    .append("textPath")
                    .attr("xlink:href", function(d){
                        return "#"+nodeHostId;
                    })
                    .attr("startOffset", 7)
                    .attr("width", arc.node().getTotalLength()/2.4)
                    .text(nodeHost)
                    .each(function wrap( d ) {
                        var self = d3.select(this),
                            textLength = self.node().getComputedTextLength(),
                            text = self.text(),
                            width = self.attr('width');
                        if(width > 50){
                            while ( ( textLength > width )&& text.length > 0) {
                                if(width > 100){
                                    text = text.slice(0, -1);
                                    self.text(text + '...');
                                }else{
                                    text = text.slice(0, -5);
                                    self.text(text);
                                }
                                textLength = self.node().getComputedTextLength();
                            }
                        }else{
                            self.text("");
                        }
                    });
                });

                graph.link = graph.svg.append("g").selectAll(".link")
                  .data(relationalPlotHelpers.nodeRelations(root.leaves()))
                  .enter().append("path")
                    .each(function(d) { d.source = d[0], d.target = d[d.length - 1]; })
                    .attr("class", "link")
                    .attr("d", graph.line);

                graph.node = graph.svg.append("g").selectAll(".node")
                  .data(root.leaves())
                  .enter().append("text")
                    .attr("class", "node")
                    .attr("fill", "white")
                    .attr("dy", "0.31em")
                    .attr("transform", function(d) { return "rotate(" + (d.x - 90) + ")translate(" + (d.y - 20) + ",0)" + (d.x < 180 ? "" : "rotate(180)"); })
                    .attr("text-anchor", function(d) { return d.x < 180 ? "start" : "end"; })
                    .text(function(d) {
                        if(d.data.key.length > 20){
                            return d.data.key.substring(0, 20)+"…";
                        }
                        return d.data.key;
                    });
            }
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                graph._data = res.resources;
                relationalPlotHelpers.displayResources(Object.keys(graph._data).length);
                relationalPlotHelpers.displayRelations();
                relationalPlotHelpers.displayScrapeTime(res.date);
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };

        this.findStartAngle = function(children) {
            var min = children[0].x;
            children.forEach(function(d) {
                if (d.x < min)
                    min = d.x;
            });
            return min;
        };

        this.findEndAngle = function(children) {
            var max = children[0].x;
            children.forEach(function(d) {
                if (d.x > max)
                    max = d.x;
            });
            return max;
        };
        this.resetPosition = function(){
            contentWidth = $(graphSelector).innerWidth(),
            diameter = contentWidth,
            radius = diameter / 2,
            innerRadius = radius - 120;
        };

    };
    return RelationalPlot;
}(RelationalPlot || {});
