var RelationalPlot = function(RelationalPlot){
    /**
     * Arc diagram rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.arc = function(dataUrl, graphSelector, refreshInterval) {

        var width,
            height,
            nodeCount,
            nodeRadius = d3.scaleSqrt().range([3, 7]),
            linkWidth = d3.scaleLinear().range([1.5, 2 * nodeRadius.range()[0]]);

        var margin = { top: 0, right: 18, bottom: 18, left: 18 };


        var x = d3.scaleLinear().range([0, width]);

        var graph = this;

        this._data = {};

        this.init = function(alreadyRunning) {
            width = $(graphSelector).width() - margin.left - margin.right;
            height = $(graphSelector).height() - margin.top - margin.bottom;
            if(alreadyRunning && graph.svg) {
                graph.svg.remove();
            }

            graph.svg = d3.select(graphSelector).append("svg")
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)

            graph.svg.append('g')
                .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

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
            var index = 0;
            for (var key in items) {
                item = items[key];
                item["x"] = index / nodeCount * width;
                item["y"] = height;
                index += 1;
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
            });
            if (!retLink.hasOwnProperty("source") || !retLink.hasOwnProperty("target")) {
              console.log("Can not find relation node for link " + link);
              retLink = link;
            }
            return retLink;
          });
        }

        this.render = function() {

            nodeCount = Object.keys(graph._data.resources).length;
            nodes = graph.createNodes(graph._data.resources);
            links = graph.createLinks(nodes, graph._data.relations);

            nodeRadius.domain(d3.extent(nodes, function (d) { return 18 }));
            linkWidth.domain(d3.extent(links, function (d) { return 1 }));

            var link = graph.svg.append('g')
                .attr('class', 'links')
                .selectAll('path')
                .data(links)
                .enter().append('path')
                .attr('d', function (d) {
                  return ['M', d.source.x, height, 'A',
                    (d.source.x - d.target.x)/2, ',',
                    (d.source.x - d.target.x)/2, 0, 0, ',',
                    d.source.x < d.target.x ? 1 : 0, d.target.x, ',', height]
                    .join(' ');
                })
                .on('mouseover', function (d) {
                  link.style('stroke', null);
                  d3.select(this).style('stroke', '#d62333');
//                  node.style('fill', function (node_d) {
//                    return node_d === d.source || node_d === d.target ? 'black' : null;
//                  });
                })
                .on('mouseout', function (d) {
                  link.style('stroke', null);
//                  node.style('fill', null);
                });

            var node = graph.svg.append('g')
                .attr('class', 'nodes')
                .selectAll('circle')
                .data(nodes)
                .enter().append('g')
                .attr("transform", function(d){
                    return "translate(" + d.x + ", " + d.y + ")"
                });

            node.append('circle')
                .attr('r', function (d) { return 16; })
                .on('mouseover', function (d) {
//                  node.style('fill', null);
//                  d3.select(this).style('fill', 'black');
                  var nodesToHighlight = links.map(function (e) { return e.source === d ? e.target : e.target === d ? e.source : 0})
                    .filter(function (d) { return d; });
//                  node.filter(function (d) { return nodesToHighlight.indexOf(d) >= 0; })
//                    .style('fill', '#555');
                  link.style('stroke', function (link_d) {
                    return link_d.source === d | link_d.target === d ? '#d62333' : null;
                  });
                })
                .on('mouseout', function (d) {
                  node.style('fill', null);
                  link.style('stroke', null);
                });

            node.append("text")
                .attr('fill', function(d) { return iconFunctions.color(d.kind); })
                .attr('font-size', function(d) { return iconFunctions.size(d.kind); })
                .attr('font-family', function(d) { return iconFunctions.family(d.kind); })
                .text(function(d) { return iconFunctions.character(d.kind); })
                .attr("transform", function(d) { return iconFunctions.transform(d.kind); })
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                graph._data = res;
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };

    };
    return RelationalPlot;
}(RelationalPlot || {});
