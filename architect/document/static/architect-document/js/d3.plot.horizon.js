var QuantitativePlot = function(QuantitativePlot){
    /**
     * Horizon chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.horizonChart = function(dataUrl, graphSelector, refreshInterval) {

        var graph = this;
        this._data = {};

        this.init = function(alreadyRunning) {

            if(alreadyRunning && graph.svg) {
                graph.chart.remove()
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
            console.log(graphSelector);

            d3.select(graphSelector)
                .selectAll('.horizon-chart')
                .data(graph._data)
                .enter()
                .append('div')
                .attr('class', 'horizon-chart')
                .each(function(d) {
                    d3.horizonChart()
                        .title(d.name)
                        .call(this, d.values);
                });
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                var values = [];
                var raw_data = res.data;
                raw_data.slice(1, raw_data.length).forEach(function(d, i) {
                    values.push({
                        'name': d[0],
                        'values': d.slice(1, d.length)
                    });
                });;
                graph._data = values;
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };
    };
    return QuantitativePlot;
}(QuantitativePlot || {});
