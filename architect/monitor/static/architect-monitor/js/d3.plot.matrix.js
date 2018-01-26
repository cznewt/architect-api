var RelationalPlot = function(RelationalPlot){
    /**
     * Adjacency matrix rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.adjacencyMatrix = function(dataUrl, graphSelector, refreshInterval) {

        var adjacencyMatrix = d3.adjacencyMatrixLayout(),
            colorMapping = d3.scaleOrdinal()
                .range(d3.schemeCategory20b),
            width = $(graphSelector).innerWidth(),
            graphWidth = width - 10;

        var graph = this;

        this._data = {};

        this.init = function(alreadyRunning) {

            if(alreadyRunning && graph.svg) {
                graph.svg.remove()
            }

            graph.svg = d3.select(graphSelector).append("svg")
                .attr("width", width)
                .attr("height", width);
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

        this.createNodes = function(items) {
            var output = [];
            for (var key in items) {
                item = items[key];
                item["group"] = 1;
                output.push(item);
            }
            return output;
        };

        this.createLinks = function(nodes, relations) {
          return relations.map(function(link) {
            var retLink = {};
            nodes.forEach(function(node) {
              if (link.source == node.id) {
                retLink.source = node;
              } else if (link.target == node.id) {
                retLink.target = node;
              }
              retLink.value = 2;
            });
            if (!retLink.hasOwnProperty("source") || !retLink.hasOwnProperty("target")) {
              console.log("Can not find relation node for link " + link);
              retLink = link;
            }
            return retLink;
          });
        }
        this.render = function() {

            nodes = graph.createNodes(graph._data.resources);
            links = graph.createLinks(nodes, graph._data.relations);

            adjacencyMatrix
                .size([width-81, width-81])
                .nodes(nodes)
                .links(links)
                .directed(false)
                .nodeID(d => d.name);

            var matrixData = adjacencyMatrix();

            graph.svg.append('g')
                .attr('transform', 'translate(80,80)')
                .attr('id', 'adjacencyMatrix')
                .selectAll('rect')
                .data(matrixData)
                .enter()
                .append('rect')
                    .attr('width', d => d.width)
                    .attr('height', d => d.height)
                    .attr('x', d => d.x)
                    .attr('y', d => d.y)
                    .style('stroke', 'black')
                    .style('stroke-width', '1px')
                    .style('stroke-opacity', .1)
                    .style('fill', d => colorMapping(d.source.group))
                    .style('fill-opacity', d => d.weight * 0.8);

            d3.select('#adjacencyMatrix')
                .call(adjacencyMatrix.xAxis);

            d3.select('#adjacencyMatrix')
                .call(adjacencyMatrix.yAxis);
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
