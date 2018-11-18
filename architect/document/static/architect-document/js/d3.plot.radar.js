var QuantitativePlot = function (QuantitativePlot) {
    /**
     * Radar chart rendering method
     * @param dataUrl - Data endpoint URL
     * @param graphSelector - Graph parent <div> CSS selector
     * @param refreshInterval - Refresh interval in seconds (null for disabled)
     */
    QuantitativePlot.radarChart = function (dataUrl, graphSelector, refreshInterval) {

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
            console.log(graph._data);
            graph.chart = bb.generate({
                data: {
                    x: "x",
                  //  xFormat: '%Y-%m-%d %H:%M:%S',
                    columns: graph._data,
                    type: "radar",
                    labels: false
                },
                radar: {
                    axis: {
                        max: 40
                    },
                    level: {
                        depth: 4
                    },
                    direction: {
                        clockwise: true
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
