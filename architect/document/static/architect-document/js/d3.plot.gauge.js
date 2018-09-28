var QuantitativePlot = function(QuantitativePlot){
    /**
     * Gauge rendering method
     *
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.gauge = function(dataUrl, graphSelector, refreshInterval) {

        var config = {
            size: $(graphSelector).innerWidth(),
            label: 'gauge',
            min: undefined != min ? min : 0,
            max: undefined != max ? max : 100,
            minorTicks: 5
        }

        var range = config.max - config.min;
        config.yellowZones = [{ from: config.min + range*0.75, to: config.min + range*0.9 }];
        config.redZones = [{ from: config.min + range*0.9, to: config.max }];

        this.gauge = new Gauge(graphSelector, config);

        var graph = this;
        this._data = {};

        this.init = function(alreadyRunning) {

            if(!alreadyRunning){
                graph.requestData(dataUrl, graph.render);

                $(window).on('resize', function(ev){
                    graph.render();
                });

                if(refreshInterval){
                    setInterval(function(){
                        graph.requestData(dataUrl, function(){
                            graph.render();
                        });
                    }, refreshInterval * 1000);
                }
            }
        };

        this.render = function() {
            console.log(graph._data);
            graph.gauge.redraw(graph._data);
        };

        this.requestData = function(dataUrl, callback){
            d3.json(dataUrl, function(res){
                graph._data = res.data;
                if(typeof callback === 'function'){
                    callback();
                }
            });
        };
    };
    return QuantitativePlot;
}(QuantitativePlot || {});


var QuantitativePlot = function (QuantitativePlot) {
    /**
     * Gauge chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.gaugeChart = function (dataUrl, graphSelector, refreshInterval) {

        var graph = this;
        this._data = {};

        this.init = function (alreadyRunning) {

            if (alreadyRunning && graph.svg) {
                graph.chart.remove()
            }

            if (!alreadyRunning) {
                graph.requestData(dataUrl, graph.render);

                $(window).on('resize', function (ev) {
                    graph.init(true);
                    graph.render();
                });

                if (refreshInterval) {
                    setInterval(function () {
                        graph.requestData(dataUrl, function () {
                            graph.init(true);
                            graph.render();
                        });
                    }, refreshInterval * 1000);
                }
            }
        };

        this.render = function () {
            graph.chart = bb.generate({
                data: {
                    x: "x",
                    xFormat: '%Y-%m-%d %H:%M:%S',
                    columns: graph._data
                },
                point: {
                    show: false
                },
                axis: {
                    x: {
                        type: "timeseries",
                        tick: {
                            count: 4,
                            format: '%Y-%m-%d %H:%M'
                        }
                    }
                },
                bindto: graphSelector
            });

        };

        this.requestData = function (dataUrl, callback) {
            d3.json(dataUrl, function (res) {
                graph._data = res.data;
                if (typeof callback === 'function') {
                    callback();
                }
            });
        };
    };
    return QuantitativePlot;
}(QuantitativePlot || {});
