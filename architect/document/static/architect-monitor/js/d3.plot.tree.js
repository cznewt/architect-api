var RelationalPlot = function(RelationalPlot){
    /**
     * Tree structure rendering method
     *
     * Adapted from https://bl.ocks.org/d3noob/d316a488cae262ae24e6ca897b209f9e
     *
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.tree = function(dataUrl, graphSelector, refreshInterval) {

        var margin = {top: 20, right: 160, bottom: 20, left: 120},
            width = $(graphSelector).innerWidth() - margin.right - margin.left,
            height = $(graphSelector).innerHeight() - margin.top - margin.bottom;

        var treemap = d3.tree()
          .size([height, width]);

        var graph = this;
        this._data = {};

        this.init = function(alreadyRunning) {
            if(alreadyRunning && graph.svg) {
                graph.svg.remove()
            }

            graph.svg = d3.select(graphSelector).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom);

            if(!alreadyRunning){
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

        this.render = function() {

            nodes = treemap(graph._data);

            g = graph.svg.append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            // adds the links between the nodes
            var link = g.selectAll(".link")
                .data( nodes.descendants().slice(1))
                .enter().append("path")
                .attr("class", "link")
                .attr("d", function(d) {
                    return "M" + d.y + "," + d.x
                    + "C" + (d.y + d.parent.y) / 2 + "," + d.x
                    + " " + (d.y + d.parent.y) / 2 + "," + d.parent.x
                    + " " + d.parent.y + "," + d.parent.x;
                    });

          // adds each node as a group
            var node = g.selectAll(".node")
                .data(nodes.descendants())
                .enter().append("g")
                .attr("class", function(d) {
                    return "node" +
                    (d.children ? " node--internal" : " node--leaf"); })
                .attr("transform", function(d) {
                    return "translate(" + d.y + "," + d.x + ")"; });

            // adds the circle to the node
            node.append("circle")
                .attr("r", 10)
                .style("fill", function(d) {
                    if(d.data.status == 'active') {
                        return '#77dd77';
                    }
                    if(d.data.status == 'error') {
                        return '#ff6961';
                    }
                    return '#eee';
                });

            // adds the text to the node
            node.append("text")
                .attr("dy", ".35em")
                .attr("x", function(d) { return d.children ? -13 : 13; })
                .style("text-anchor", function(d) {
                    return d.children ? "end" : "start"; })
                .text(function(d) { return d.data.name; });

        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                console.log(res);
                graph._data = d3.hierarchy(res.resources, function(d) {
                    return d.children;
                });
//                relationalPlotHelpers.displayResources(Object.keys(graph._data.resources).length);
//                relationalPlotHelpers.displayRelations(graph._data.relations.length);
//                relationalPlotHelpers.displayScrapeTime(res.date);
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };
    };
    return RelationalPlot;
}(RelationalPlot || {});
