
var RelationalPlot = function(RelationalPlot){
    /**
     * Sankey diagram rendering method
     *
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    RelationalPlot.sankeyDiagram = function(dataUrl, graphSelector, refreshInterval) {

        var config = {
            margin: { top: 10, left: 10, right: 10, bottom: 10 },
            nodes: {
                dynamicSizeFontNode: {
                    enabled: true,
                    minSize: 14,
                    maxSize: 30
                },
                fontSize: 14, // if dynamicSizeFontNode not enabled
                draggableX: false, // default [ false ]
                draggableY: true, // default [ true ]
                colors: d3.scaleOrdinal(d3.schemeCategory10)
            },
            links: {
                formatValue: function(val) {
                    return d3.format(",.0f")(val);
                }
            },
            tooltip: {
                infoDiv: true,  // if false display default tooltip
                labelSource: 'Input:',
                labelTarget: 'Output:'
            }
        }

        var graph = this;
        this._data = {};

        this.init = function(alreadyRunning) {
            if(alreadyRunning && graph.sankey) {
                graph.sankey.remove()
            }

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
            console.log(graph._data);
            console.log(config);
            graph.sankey = sk.createSankey(graphSelector, config, graph._data);
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                var nodes = [];
                for (var d in res.resources) {
                    nodes.push(res.resources[d]);
                };
                graph._data = {
                    nodes: nodes,
                    links: res.relations
                };
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };
    };
    return RelationalPlot;
}(RelationalPlot || {});
